# File: network_data/migrations/0005_create_continuous_aggregate_by_mac.py
# Copyright (C) 2025 Keegan White
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

from django.db import migrations

class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        # Ensure this runs after your hypertable migration (or after 0004/0005, depending on your setup)
        ('network_data', '0004_create_continuous_aggregate'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Create a continuous aggregate materialized view that groups flows by 1-minute buckets,
                -- source MAC address, and classification.
                CREATE MATERIALIZED VIEW IF NOT EXISTS network_data_flow_by_mac_1min
                WITH (timescaledb.continuous) AS
                SELECT
                    time_bucket('1 minute', timestamp) AS bucket,
                    src_mac,
                    classification,
                    COUNT(*) AS count
                FROM network_data_flow
                GROUP BY bucket, src_mac, classification;
            """,
            reverse_sql="DROP MATERIALIZED VIEW IF EXISTS network_data_flow_by_mac_1min;"
        ),
        migrations.RunSQL(
            sql="""
                -- Add a refresh policy for the MAC-based continuous aggregate.
                SELECT add_continuous_aggregate_policy(
                    'network_data_flow_by_mac_1min',
                    start_offset => INTERVAL '3 minute',
                    end_offset => INTERVAL '1 minute',
                    schedule_interval => INTERVAL '1 minute'
                );
            """,
            reverse_sql="""
                SELECT remove_continuous_aggregate_policy('network_data_flow_by_mac_1min');
            """,
        )
    ]
