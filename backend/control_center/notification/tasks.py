import time
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Notifier, Notification, NetworkSummaryNotification, DataUsageNotification, ApplicationUsageNotification
from account.models import UserProfile
from celery import shared_task
import requests
from django.db import connection
from django.apps import apps
import logging

User = get_user_model()

TELEGRAM_API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_API_KEY}/getUpdates"
MESSAGE_TIMEOUT = 30  # Maximum waiting time in seconds
POLL_INTERVAL = 2  # Poll every 2 seconds

logger = logging.getLogger(__name__)

def format_megabytes(bytes_value):
    """Convert bytes to megabytes with 4 decimal places"""
    return round(bytes_value / (1024 * 1024), 4)

@shared_task
def monitor_telegram_registration(user_id, unique_token):
    """Monitors Telegram messages for a /start command containing the unique token."""
    start_time = time.time()
    offset = None  # Track the latest update_id to avoid duplicates


    while time.time() - start_time < MESSAGE_TIMEOUT:
        params = {"timeout": 5}  # Adjust Telegram long polling timeout
        if offset:
            params["offset"] = offset  # Only fetch new updates

        response = requests.get(TELEGRAM_API_URL, params=params)

        if response.status_code == 200:
            updates = response.json().get("result", [])


            for update in updates:
                offset = update["update_id"] + 1  # Move to next update

                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id")
                username = message.get("from", {}).get("username", "")

                if text and text.startswith(f"/start {unique_token}"):


                    # Register Notifier for the user
                    user = User.objects.get(id=user_id)
                    notifier, created = Notifier.objects.get_or_create(
                        user=user,
                        defaults={"chat_id": str(chat_id), "telegram_api_key": settings.TELEGRAM_API_KEY}
                    )

                    if not created:

                        notifier.chat_id = str(chat_id)
                        notifier.save()

                    # Ensure UserProfile is updated
                    try:
                        user_profile = UserProfile.objects.get(user=user)
                        user_profile.telegram_linked = True
                        user_profile.telegram_chat_id = str(chat_id)
                        if username:
                            user_profile.telegram_username = username  # Store username if available
                        user_profile.save()

                    except UserProfile.DoesNotExist:

                        user_profile = UserProfile.objects.create(
                            user=user,
                            telegram_linked=True,
                            telegram_chat_id=str(chat_id),
                            telegram_username=username if username else None,
                        )

                    # Send confirmation message
                    telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_API_KEY}/sendMessage"
                    data = {"chat_id": chat_id, "text": "You have successfully linked your Telegram account!"}
                    response = requests.post(telegram_url, data=data)


                    # Create a notification record
                    Notification.objects.create(
                        user=user,
                        message="Your Telegram account has been successfully linked.",
                        notifier=notifier
                    )

                    return {"success": True, "message": "Telegram linked successfully"}


        time.sleep(POLL_INTERVAL)

    return {"success": False, "message": "Timed out waiting for Telegram message"}


def get_top_users(n, period):
    """
    Retrieve top `n` users by data usage within the last `period` using the difference
    between the latest and earliest bytes for each unique flow.
    """
    query = """
        SELECT mac_address, SUM(max_bytes - min_bytes) AS total_bytes
        FROM (
          SELECT mac_address, MAX(byte_count) AS max_bytes, MIN(byte_count) AS min_bytes
          FROM network_data_flowstat
          WHERE timestamp >= NOW() - %s::interval
          GROUP BY mac_address, port, protocol, classification
        ) AS sub
        GROUP BY mac_address
        ORDER BY total_bytes DESC
        LIMIT %s;
        """
    with connection.cursor() as cursor:
        cursor.execute(query, [period, n])
        rows = cursor.fetchall()

    return [
        {"mac_address": mac, "total_mb": format_megabytes(total_bytes)}
        for mac, total_bytes in rows
    ]


def get_category_name_from_cookie(cookie):
    """Return the category name for a given cookie, or the cookie itself if not found."""
    try:
        Category = apps.get_model('odl', 'Category')
        return Category.objects.get(category_cookie=str(cookie)).name
    except Exception:
        return str(cookie)


def get_top_classes(n, period):
    """
    Retrieve top `n` application classifications by data usage within the last `period`
    using the difference between the latest and earliest bytes for each unique flow.
    """
    query = """
    SELECT classification, SUM(max_bytes - min_bytes) AS total_bytes
    FROM (
      SELECT classification, MAX(byte_count) AS max_bytes, MIN(byte_count) AS min_bytes
      FROM network_data_flowstat
      WHERE timestamp >= NOW() - %s::interval
      GROUP BY mac_address, port, protocol, classification
    ) AS sub
    GROUP BY classification
    ORDER BY total_bytes DESC
    LIMIT %s;
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [period, n])
        rows = cursor.fetchall()

    return [
        {"classification": get_category_name_from_cookie(classification), "total_mb": format_megabytes(total_bytes)}
        for classification, total_bytes in rows
    ]


def get_top_flows(n=5, period="1 minute"):
    """Retrieve top `n` most frequent flows from aggregate_flows within the last `period`."""
    query = """
    SELECT classification, SUM(count) AS total_count
    FROM network_data_flow_1min
    WHERE bucket >= NOW() - %s::interval
    GROUP BY classification
    ORDER BY total_count DESC
    LIMIT %s;
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [period, n])
        rows = cursor.fetchall()

    return [
        {"classification": classification, "total_count": total_count}
        for classification, total_count in rows
    ]

@shared_task
def send_network_summary(notification_id):
    """
    Sends a network summary report via Telegram based on the user's preferences.
    """
    try:
        notification = NetworkSummaryNotification.objects.get(id=notification_id)
        notifier = notification.notifier

        if not notifier:
            logger.warning(f"No notifier found for NetworkSummaryNotification id={notification_id}")
            return

        # Convert frequency into a valid PostgreSQL interval format (minutes or hours)
        period = f"{notification.frequency} minutes" if notification.frequency < 60 else f"{notification.frequency // 60} hours"
        top_users = get_top_users(notification.top_users_count, period)
        top_classes = get_top_classes(notification.top_apps_count, period)
        top_flows = get_top_flows(period=period)

        message = (
            f"📡 *Network Summary Report*\n\n"
            f"🔄 Frequency: {notification.get_frequency_display()}\n\n"
            f"📊 *Top {notification.top_users_count} Data Users (Last {period}):*\n"
        )

        if top_users:
            for user in top_users:
                message += f"  🔹 {user['mac_address']}: {user['total_mb']} MB\n"
        else:
            message += "  🚫 No users found.\n"

        message += f"\n📌 *Top {notification.top_apps_count} Applications (Last {period}):*\n"
        if top_classes:
            for app in top_classes:
                message += f"  🔸 {app['classification']}: {app['total_mb']} MB\n"
        else:
            message += "  🚫 No applications found.\n"

        message += f"\n🔥 *Top 5 Flows (Last {period}):*\n"
        if top_flows:
            for flow in top_flows:
                # Map classification cookie to name for flows as well
                flow_name = get_category_name_from_cookie(flow['classification'])
                message += f"  ⚡ {flow_name}: {flow['total_count']} flows\n"
        else:
            message += "  🚫 No flow data available.\n"

        # Send message via Telegram
        telegram_url = f"https://api.telegram.org/bot{notifier.telegram_api_key}/sendMessage"
        data = {"chat_id": notifier.chat_id, "text": message, "parse_mode": "Markdown"}
        logger.info(f"Sending Telegram network summary to chat_id={notifier.chat_id}: {message}")
        response = requests.post(telegram_url, data=data)
        logger.info(f"Telegram API response: {response.status_code} {response.text}")
        return {"success": True, "message": "Sent message successfully."}
    except NetworkSummaryNotification.DoesNotExist:
        logger.error(f"NetworkSummaryNotification id={notification_id} does not exist.")
        return {"success": False, "message": "Timed out waiting for Telegram message"}
    except Exception as e:
        logger.exception(f"Exception in send_network_summary: {e}")
        return {"success": False, "message": str(e)}

def get_users_exceeding_limit(limit_mb, period):
    """
    Fetch users who have exceeded the data limit within the given time period,
    where usage is calculated as the sum of (latest bytes - earliest bytes)
    for each unique flow.
    """

    query = """
        SELECT mac_address, SUM(max_bytes - min_bytes) AS total_bytes
        FROM (
          SELECT mac_address, MAX(byte_count) AS max_bytes, MIN(byte_count) AS min_bytes
          FROM network_data_flowstat
          WHERE timestamp >= NOW() - %s::interval
          GROUP BY mac_address, port, protocol, classification
        ) AS sub
        GROUP BY mac_address
        HAVING SUM(max_bytes - min_bytes) > %s * 1024 * 1024
        ORDER BY total_bytes DESC;
        """
    with connection.cursor() as cursor:
        cursor.execute(query, [period, limit_mb])
        rows = cursor.fetchall()
    return [
        {"mac_address": mac, "total_mb": format_megabytes(total_bytes)}
        for mac, total_bytes in rows
    ]


@shared_task
def check_data_usage(notification_id):
    """
    Checks if any users have exceeded the data limit and sends an alert via Telegram.
    """
    try:
        notification = DataUsageNotification.objects.get(id=notification_id)
        notifier = notification.notifier

        if not notifier:
            logger.warning(f"No notifier found for DataUsageNotification id={notification_id}")
            return

        # Convert frequency into a valid PostgreSQL interval format
        period = f"{notification.frequency} minutes" if notification.frequency < 60 else f"{notification.frequency // 60} hours"

        exceeded_users = get_users_exceeding_limit(notification.data_limit_mb, period)

        if not exceeded_users:
            logger.info(f"No users exceeded data limit for DataUsageNotification id={notification_id}")
            return  # No users exceeded the limit, no need to send a message

        message = (
            f"🚨 *Data Usage Alert*\n\n"
            f"🔄 *Frequency:* {notification.get_frequency_display()}\n"
            f"📏 *Limit:* {notification.data_limit_mb} MB\n\n"
            f"⚠️ *Users who exceeded the limit in the last {period}:*\n"
        )

        for user in exceeded_users:
            message += f"  🔹 {user['mac_address']}: {user['total_mb']} MB\n"

        # Send message via Telegram
        telegram_url = f"https://api.telegram.org/bot{notifier.telegram_api_key}/sendMessage"
        data = {"chat_id": notifier.chat_id, "text": message, "parse_mode": "Markdown"}
        logger.info(f"Sending Telegram data usage alert to chat_id={notifier.chat_id}: {message}")
        response = requests.post(telegram_url, data=data)
        logger.info(f"Telegram API response: {response.status_code} {response.text}")

        if response.status_code == 200:
            return {"success": True, "message": f"Notification sent successfully."}
        else:
            logger.error(f"Failed to send Telegram message: {response.status_code} {response.text}")
            return {"success": False, "message": f"Request to send telegram message failed with status {response.status_code}."}

    except DataUsageNotification.DoesNotExist:
        logger.error(f"DataUsageNotification id={notification_id} does not exist.")
        return {"success": False, "message": f"Notification ID {notification_id} not found"}
    except Exception as e:
        logger.exception(f"Exception in check_data_usage: {e}")
        return {"success": False, "message": str(e)}

@shared_task
def check_application_usage(notification_id):
    """
    Checks if any applications have exceeded the data limit and sends an alert via Telegram.
    Usage is calculated as the sum of (latest bytes - earliest bytes) for each unique flow
    grouped by classification.
    """
    try:
        notification = ApplicationUsageNotification.objects.get(id=notification_id)
        notifier = notification.notifier

        if not notifier:
            logger.warning(f"No notifier found for ApplicationUsageNotification id={notification_id}")
            return

        # Convert frequency into a valid PostgreSQL interval format
        period = f"{notification.frequency} minutes" if notification.frequency < 60 else f"{notification.frequency // 60} hours"

        query = """
            SELECT classification, SUM(max_bytes - min_bytes) AS total_bytes
            FROM (
              SELECT classification, MAX(byte_count) AS max_bytes, MIN(byte_count) AS min_bytes
              FROM network_data_flowstat
              WHERE timestamp >= NOW() - %s::interval
              GROUP BY mac_address, port, protocol, classification
            ) AS sub
            GROUP BY classification
            HAVING SUM(max_bytes - min_bytes) > %s * 1024 * 1024
            ORDER BY total_bytes DESC;
            """
        with connection.cursor() as cursor:
            cursor.execute(query, [period, notification.data_limit_mb])
            rows = cursor.fetchall()

        exceeded_apps = [
            {"classification": get_category_name_from_cookie(classification), "total_mb": format_megabytes(total_bytes)}
            for classification, total_bytes in rows
        ]

        if not exceeded_apps:
            logger.info(f"No applications exceeded data limit for ApplicationUsageNotification id={notification_id}")
            return  # No applications exceeded the limit

        message = (
            f"🚨 *Application Usage Alert*\n\n"
            f"🔄 *Frequency:* {notification.get_frequency_display()}\n"
            f"📏 *Limit:* {notification.data_limit_mb} MB\n\n"
            f"⚠️ *Applications exceeding the limit in the last {period}:*\n"
        )

        for app in exceeded_apps:
            message += f"  🔹 {app['classification']}: {app['total_mb']} MB\n"

        # Send message via Telegram
        telegram_url = f"https://api.telegram.org/bot{notifier.telegram_api_key}/sendMessage"
        data = {"chat_id": notifier.chat_id, "text": message, "parse_mode": "Markdown"}
        logger.info(f"Sending Telegram application usage alert to chat_id={notifier.chat_id}: {message}")
        response = requests.post(telegram_url, data=data)
        logger.info(f"Telegram API response: {response.status_code} {response.text}")

        if response.status_code == 200:
            return {"success": True, "message": "Notification sent successfully."}
        else:
            logger.error(f"Failed to send Telegram message: {response.status_code} {response.text}")
            return {"success": False,
                    "message": f"Request to send telegram message failed with status {response.status_code}."}

    except ApplicationUsageNotification.DoesNotExist:
        logger.error(f"ApplicationUsageNotification id={notification_id} does not exist.")
        return {"success": False, "message": f"Notification ID {notification_id} not found"}
    except Exception as e:
        logger.exception(f"Exception in check_application_usage: {e}")
        return {"success": False, "message": str(e)}
