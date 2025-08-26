import datetime
import json

from django.core.exceptions import ValidationError
from django.db import connection
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes
)
from django.utils import timezone
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
import re
from rest_framework import status
from django.core.validators import RegexValidator

from odl.models import Category
from django.utils import timezone as django_timezone
from django.conf import settings

from .models import FlowStat, Flow
ALLOWED_PERIOD_REGEX = re.compile(r"^\s*\d+\s*(seconds?|minutes?|hours?|days?)\s*$", re.IGNORECASE)
# Validator for MAC addresses (format: XX:XX:XX:XX:XX:XX)
mac_address_validator = RegexValidator(
    regex=r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
    message="Enter a valid MAC address in format XX:XX:XX:XX:XX:XX."
)
from .tasks import create_flow_stat_entry, create_flow_stat_entries_batch
from django.db.models import Q

def get_latest_flow_by_mac_port(mac, port):
    """
    Returns the latest Flow record where either:
      - src_mac equals mac and src_port equals port, OR
      - src_mac equals mac and dst_port equals port, OR
      - dst_mac equals mac and src_port equals port, OR
      - dst_mac equals mac and dst_port equals port.
    """
    return Flow.objects.filter(
        Q(src_mac__iexact=mac, src_port=port) |
        Q(src_mac__iexact=mac, dst_port=port) |
        Q(dst_mac__iexact=mac, src_port=port) |
        Q(dst_mac__iexact=mac, dst_port=port)
    ).order_by('-timestamp').first()


@api_view(['POST'])
def log_flow(request):
    if request.method == 'POST':
        stats_data_list = request.data
        if not isinstance(stats_data_list, list):
            print("Received non-list data for log_flow_stats")
            return Response(
                {"status": "error", "message": "Expected a list of flow stat objects."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # print("Received stats_data_list: {}".format(stats_data_list))
        successful_tasks = 0
        failed_tasks = 0

        try:
            # Asynchronously call the Celery task for each stat entry
            create_flow_stat_entries_batch.delay(stats_data_list)
            successful_tasks += 1
        except Exception as e:  # Catch issues with .delay() itself, though rare
            print(f"Error dispatching Celery task for stats_data_list: {stats_data_list}, Error: {e}")
            failed_tasks += 1

        msg = f"Processed {len(stats_data_list)} flow stat entries. Dispatched: {successful_tasks}, Failed to dispatch: {failed_tasks}."
        # print(msg)
        return Response({"status": "success", "message": msg}, status=status.HTTP_202_ACCEPTED)
    return Response({"status": "error", "message": "Only POST method is allowed."},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def aggregate_flows(request):
    """
    Retrieve aggregated flow data for a specified look-back period.

    Query Parameters:
        period (optional): Look-back period (e.g., '15 minutes', '24 hours').
                             Defaults to '15 minutes'.

    Returns:
        JSON response mapping each classification to the total count in that period.
        Example:
            {
                "google": 105,
                "dns": 123,
                ...
            }
    """
    try:
        # Get the period from query parameters; default to '15 minutes' if not provided.
        period = request.query_params.get('period', '15 minutes').strip()

        # Validate the period parameter to ensure it is in the expected format.
        if not ALLOWED_PERIOD_REGEX.match(period):
            raise ValidationError(
                "Invalid period format. Expected format: '<integer> <unit>' "
                "where unit is seconds, minutes, hours, or days."
            )

        # Use a raw SQL query to sum counts per classification over the specified period.
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT classification, SUM(count) AS total_count
                FROM network_data_flow_1min
                WHERE bucket >= NOW() - %s::interval
                GROUP BY classification;
                """,
                [period]
            )
            rows = cursor.fetchall()

        # Convert the results into a dictionary mapping classification -> total count.
        data = {classification: total_count for classification, total_count in rows}

        return Response(data,
                        status=status.HTTP_200_OK)
    except ValidationError:
        return Response({"status": "error", "message": "Invalid period format. Expected format: '<integer> <unit>' "
                "where unit is seconds, minutes, hours, or days."},
                        status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def aggregate_flows_by_mac(request):
    """
    Retrieve aggregated flow data for a specified look-back period filtered by a MAC address.

    Query Parameters:
        period (optional): Look-back period (e.g., '15 minutes', '24 hours').
                           Defaults to '15 minutes'.
        mac_address (required): A valid MAC address (format: XX:XX:XX:XX:XX:XX).

    Returns:
        JSON response mapping each classification to the total count for the given MAC address.
        Example:
            {
                "google": 105,
                "dns": 123,
                ...
            }
    """
    try:
        # Get the period parameter, defaulting to '15 minutes'
        period = request.query_params.get('period', '15 minutes').strip()
        if not ALLOWED_PERIOD_REGEX.match(period):
            raise ValidationError(
                "Invalid period format. Expected format: '<integer> <unit>' "
                "where unit is seconds, minutes, hours, or days."
            )

        # Get and validate the MAC address parameter
        mac = request.query_params.get('mac_address')
        if not mac:
            raise ValidationError("The 'mac_address' parameter is required.")
        mac = mac.strip()
        # Validate using the RegexValidator (this will raise a ValidationError if invalid)
        mac_address_validator(mac)

        # Use a parameterized raw SQL query to sum counts per classification for the given MAC address.
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT src_mac, classification, SUM(count) AS total_count
                FROM network_data_flow_by_mac_1min
                WHERE bucket >= NOW() - %s::interval
                  AND src_mac = %s
                GROUP BY src_mac, classification;
                """,
                [period, mac]
            )
            rows = cursor.fetchall()

        # Convert the results into a dictionary mapping classification -> total count.
        data = {classification: total_count for _, classification, total_count in rows}

        return Response(data, status=status.HTTP_200_OK)

    except ValidationError as ve:
        return Response(
            {"status": "error", "message": str(ve)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def data_used_per_classification(request):
    """
    Retrieve the data usage per classification for the specified period.
    For each unique flow (mac_address, port, protocol, classification), the usage is calculated
    as (max(bytes) - min(bytes)) over the period.
    """
    # 1. Fetch Category Mappings
    # Category.category_cookie is a CharField storing the string representation
    # of the integer cookie.
    try:
        categories = Category.objects.all()
        category_cookie_to_name_map = {
            cat.category_cookie: cat.name
            for cat in categories
            if cat.category_cookie and cat.name
        }
        # print(category_cookie_to_name_map)
    except Exception as e:
        print(f"Error fetching category mappings: {e}")
        return Response(
            {
                "status": "error",
                "message": "Could not load category mappings.",
            },
            status=500,
        )
    period = request.query_params.get('period', '15 minutes').strip()
    if not ALLOWED_PERIOD_REGEX.match(period):
        return Response(
            {"status": "error", "message": "Invalid period format. Expected '<integer> <unit>'."},
            status=400
        )


    # Use the optimized continuous aggregate for better performance
    query = """
    SELECT classification, SUM(usage_bytes) AS total_bytes
    FROM network_data_flowstat_usage_1min
    WHERE bucket >= NOW() - %s::interval
    GROUP BY classification;
    """
    rows = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT NOW();")
            db_now = cursor.fetchone()[0]  # Aware, in session's timezone (settings.TIME_ZONE)
            # print(f"Database NOW(): {db_now.isoformat()}")
            # print(f"Database NOW() timezone: {db_now.tzinfo}")
            cursor.execute(query, [period])
            rows = cursor.fetchall()
    except Exception as e:
        # Log this error in a real application
        print(f"Database query error: {e}")  # Replace with logging
        return Response(
            {"status": "error", "message": "Error querying data usage."},
            status=500,
        )
    # print(rows)

    # 2. Process rows, translate classification cookies, and aggregate
    data = {}
    for classification_cookie_val, total_bytes_val in rows:
        # Ensure total_bytes_val is a number (it could be None if SUM results in NULL)
        current_bytes = total_bytes_val if total_bytes_val is not None else 0

        classification_name = "unallocated"  # Default value

        if classification_cookie_val is not None:
            # The classification_cookie_val from the DB is the OVS/ODL cookie
            classification_cookie_str = str(classification_cookie_val)
            classification_name = category_cookie_to_name_map.get(
                classification_cookie_str, "unallocated"
            )

        # Aggregate bytes for the same classification name
        data[classification_name] = (
                data.get(classification_name, 0) + current_bytes
        )
    # print(data)
    return Response(data, status=200)


@api_view(['GET'])
def data_used_per_user(request):
    """
    Retrieve the data usage per user (mac_address) for the specified period.
    For each unique flow, the usage is (max(bytes) - min(bytes)) over the period,
    then aggregated by the mac_address.
    """
    period = request.query_params.get('period', '15 minutes').strip()
    if not ALLOWED_PERIOD_REGEX.match(period):
        return Response(
            {"status": "error", "message": "Invalid period format. Expected '<integer> <unit>'."},
            status=400
        )
    # Use the optimized continuous aggregate for better performance
    query = """
        SELECT mac_address, SUM(usage_bytes) AS total_bytes
        FROM network_data_flowstat_usage_1min
        WHERE bucket >= NOW() - %s::interval
        GROUP BY mac_address;
        """
    with connection.cursor() as cursor:
        cursor.execute(query, [period])
        rows = cursor.fetchall()
    data = {mac: total_bytes for mac, total_bytes in rows}
    return Response(data, status=200)


@api_view(['GET'])
def data_used_per_user_per_classification(request):
    """
    Retrieve the data usage per user per classification for the specified period.
    For each unique flow, the usage is (max(bytes) - min(bytes)) over the period,
    then aggregated by mac_address and classification.
    """
    # 1. Fetch Category Mappings
    # Category.category_cookie is a CharField storing the string representation
    # of the integer cookie.
    try:
        categories = Category.objects.all()
        category_cookie_to_name_map = {
            cat.category_cookie: cat.name
            for cat in categories
            if cat.category_cookie and cat.name
        }
    except Exception as e:
        print(f"Error fetching category mappings: {e}")
        return Response(
            {
                "status": "error",
                "message": "Could not load category mappings.",
            },
            status=500,
        )
    period = request.query_params.get('period', '15 minutes').strip()
    if not ALLOWED_PERIOD_REGEX.match(period):
        return Response(
            {"status": "error", "message": "Invalid period format. Expected '<integer> <unit>'."},
            status=400
        )



    # Use the optimized continuous aggregate for better performance
    query = """
    SELECT mac_address, classification, SUM(usage_bytes) AS total_bytes
    FROM network_data_flowstat_usage_1min
    WHERE bucket >= NOW() - %s::interval
    GROUP BY mac_address, classification;
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [period])
        rows = cursor.fetchall()
    # 2. Process rows and translate classification cookies
    data = {}
    for mac, classification_cookie_val, total_bytes in rows:
        classification_name = "unallocated"
        if classification_cookie_val is not None:
            # The classification_cookie_val from the DB is an OVS/ODL cookie
            classification_cookie_str = str(classification_cookie_val)
            classification_name = category_cookie_to_name_map.get(
                classification_cookie_str, "unallocated"
            )

        if mac not in data:
            data[mac] = {}
        data[mac][classification_name] = total_bytes
    return Response(data, status=200)