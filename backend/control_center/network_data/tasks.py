# network_data/tasks.py
# Copyright (C) 2025 Taurine Technology
#
# This file is part of the SDN Launch Control project.
#
# This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
# available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
#
# Contributions to this project are governed by a Contributor License Agreement (CLA).
# By submitting a contribution, contributors grant Taurine Technology exclusive rights to
# the contribution, including the right to relicense it under a different license
# at the copyright owner's discretion.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the GNU General Public License for more details.
#
# For inquiries, contact Keegan White at keeganwhite@taurinetech.com.

from datetime import datetime, timedelta
from django.db.models import Count
from .models import Flow, AggregatedFlow
from celery import shared_task
from django.utils.dateparse import parse_datetime
from .models import FlowStat
import threading
import time
import requests

@shared_task
def create_flow_entry(data):
    """
    Creates a new Flow entry.

    Expected data is a dictionary with keys corresponding to Flow fields:
        - src_ip
        - dst_ip
        - src_mac
        - dst_mac (optional)
        - src_port (optional)
        - dst_port (optional)
        - protocol (optional)
        - classification
    """
    # The Flow model's timestamp is auto-generated.
    Flow.objects.create(**data)
    return "Flow entry created"


@shared_task
def aggregate_flows():
    """
    Aggregates Flow entries for the last minute and creates new AggregatedFlow entries.
    """
    # Calculate the aggregation period. Adjust as needed.
    period_end = datetime.now()
    period_start = period_end - timedelta(minutes=1)

    # Group flows by classification and count them.
    aggregates = (
        Flow.objects
        .filter(timestamp__gte=period_start, timestamp__lt=period_end)
        .values('classification')
        .annotate(count=Count('id'))
    )

    # Create an AggregatedFlow entry for each classification.
    for agg in aggregates:
        AggregatedFlow.objects.create(
            period_start=period_start,
            period_end=period_end,
            classification=agg['classification'],
            count=agg['count']
        )

    return f"Aggregated flows from {period_start} to {period_end}"


@shared_task
def create_flow_stat_entry(data):
    """
    Celery task to create a new FlowStat record.

    Expected keys in data:
      - timestamp: ISO formatted string or a datetime object.
      - meter: int
      - duration: string (e.g. "224.533s") or float (seconds)
      - packets: int
      - bytes: int
      - priority: int
      - mac_address: str (format XX:XX:XX:XX:XX:XX)
      - protocol: str (e.g. "tcp" or "udp")
      - port: int (either tp_src or tp_dst)
      - classification: application classification

    This task converts the timestamp and duration as necessary, then creates the FlowStat entry.
    """
    try:
        ts_str = data.get('timestamp')
        timestamp = parse_datetime(ts_str) if isinstance(ts_str, str) else ts_str
        if not timestamp:
            # logger.error(f"Invalid timestamp format received: {ts_str}")
            raise ValueError("Invalid timestamp format")

        duration_str = data.get('duration', "0s")  # Default to "0s"
        duration_seconds = 0.0
        if isinstance(duration_str, str) and duration_str.endswith('s'):
            try:
                duration_seconds = float(duration_str.rstrip('s'))
            except ValueError:
                # logger.warning(f"Could not parse duration string: {duration_str}")
                print(f"Could not parse duration string: {duration_str}")
        elif isinstance(duration_str, (int, float)):
            duration_seconds = float(duration_str)

        flow_stat = FlowStat.objects.create(
            timestamp=timestamp,
            classification=str(data.get('classification', 'unknown_cookie')),  # 'classification' from client IS the cookie
            meter_id=int(data.get('meter', 0)),  # Meter ID from the flow action
            duration_seconds=duration_seconds,
            packet_count=int(data.get('packets', 0)),
            byte_count=int(data.get('bytes', 0)),
            priority=int(data.get('priority', 0)),
            mac_address=data.get('mac_address', ""),
            protocol=data.get('protocol', ""),
            port=int(data.get('port', 0) or 0)  # Ensure port is int, default 0
        )
        # logger.info(f"FlowStat entry created with id {flow_stat.id} for cookie {flow_stat.cookie}")
        return f"FlowStat entry created with id {flow_stat.id}"
    except KeyError as e:
        # logger.error(f"Missing expected key in flow stat data: {e}. Data: {data}")
        return f"Error: Missing key {e}"
    except ValueError as e:  # Catch specific ValueErrors from int/float conversions
        # logger.error(f"ValueError processing flow stat data: {e}. Data: {data}")
        return f"Error: ValueError - {e}"
    except Exception as e:
        # logger.error(f"Error creating FlowStat entry: {e}. Data: {data}", exc_info=True)
        return f"Error creating FlowStat entry: {e}"


@shared_task
def create_flow_stat_entries_batch(data_list):
    """
    Celery task to create new FlowStat records using a batch of data.

    Each item in data_list should be a dict with keys:
      - timestamp: ISO formatted string or a datetime object.
      - meter: int
      - duration: string (e.g. "224.533s") or float (seconds)
      - packets: int
      - bytes: int
      - priority: int
      - mac_address: str (format XX:XX:XX:XX:XX:XX)
      - protocol: str (e.g. "tcp" or "udp")
      - port: int (either tp_src or tp_dst)
      - classification: application classification

    This task converts the timestamp and duration as necessary, then creates the FlowStat entries in bulk.
    Optimized for TimescaleDB with larger batch sizes and better error handling.
    """
    objs = []
    errors = []
    
    # Pre-allocate list for better memory efficiency
    objs = [None] * len(data_list)
    obj_count = 0
    
    for idx, data in enumerate(data_list):
        try:
            ts_str = data.get('timestamp')
            timestamp = parse_datetime(ts_str) if isinstance(ts_str, str) else ts_str
            if not timestamp:
                raise ValueError(f"Invalid timestamp format at index {idx}: {ts_str}")

            duration_str = data.get('duration', "0s")  # Default to "0s"
            duration_seconds = 0.0
            if isinstance(duration_str, str) and duration_str.endswith('s'):
                try:
                    duration_seconds = float(duration_str.rstrip('s'))
                except ValueError:
                    errors.append(f"Could not parse duration string at index {idx}: {duration_str}")
                    continue
            elif isinstance(duration_str, (int, float)):
                duration_seconds = float(duration_str)

            obj = FlowStat(
                timestamp=timestamp,
                classification=str(data.get('classification', 'unknown_cookie')),
                meter_id=int(data.get('meter', 0)),
                duration_seconds=duration_seconds,
                packet_count=int(data.get('packets', 0)),
                byte_count=int(data.get('bytes', 0)),
                priority=int(data.get('priority', 0)),
                mac_address=data.get('mac_address', ""),
                protocol=data.get('protocol', ""),
                port=int(data.get('port', 0) or 0)
            )
            objs[obj_count] = obj
            obj_count += 1
        except Exception as e:
            errors.append(f"Error processing record at index {idx}: {e}")

    created_count = 0
    try:
        if obj_count > 0:
            # Use larger batch size for TimescaleDB optimization
            # TimescaleDB handles large batches more efficiently
            FlowStat.objects.bulk_create(objs[:obj_count], batch_size=5000)  # type: ignore[attr-defined]
            created_count = obj_count
    except Exception as e:
        errors.append(f"bulk_create failed: {e}")

    return {
        "created": created_count,
        "errors": errors,
        "received": len(data_list)
    }


@shared_task
def create_flow_entries_batch(data_list):
    """
    Celery task to create new Flow records using a batch of data.
    Each item in data_list should be a dict with keys:
      - src_ip
      - dst_ip
      - src_mac
      - dst_mac (optional)
      - src_port (optional)
      - dst_port (optional)
      - classification
    Optimized for TimescaleDB with larger batch sizes and better memory efficiency.
    """
    # Pre-allocate list for better memory efficiency
    objs = [None] * len(data_list)
    obj_count = 0
    errors = []
    
    for idx, data in enumerate(data_list):
        try:
            obj = Flow(
                src_ip=data.get('src_ip'),
                dst_ip=data.get('dst_ip'),
                src_mac=data.get('src_mac'),
                dst_mac=data.get('dst_mac'),
                src_port=data.get('src_port'),
                dst_port=data.get('dst_port'),
                classification=data.get('classification'),
            )
            objs[obj_count] = obj
            obj_count += 1
        except Exception as e:
            errors.append(f"Error processing record at index {idx}: {e}")
    
    created_count = 0
    try:
        if obj_count > 0:
            # Use larger batch size for TimescaleDB optimization
            Flow.objects.bulk_create(objs[:obj_count], batch_size=5000)  # type: ignore[attr-defined]
            created_count = obj_count
    except Exception as e:
        errors.append(f"bulk_create failed: {e}")
    
    return {
        "created": created_count,
        "errors": errors,
        "received": len(data_list)
    }
