# File: network_data/migrations/0012_create_flowstat_usage_aggregate.py
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

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ('network_data', '0011_timescaledb_optimizations'),
    ]

    operations = [
        # Create continuous aggregate for FlowStat data usage calculations
        migrations.RunSQL(
            sql="""
                -- Create continuous aggregate for FlowStat data usage calculations
                CREATE MATERIALIZED VIEW IF NOT EXISTS network_data_flowstat_usage_1min
                WITH (timescaledb.continuous) AS
                SELECT
                    time_bucket('1 minute', timestamp) AS bucket,
                    mac_address,
                    classification,
                    protocol,
                    port,
                    MAX(byte_count) AS max_bytes,
                    MIN(byte_count) AS min_bytes,
                    (MAX(byte_count) - MIN(byte_count)) AS usage_bytes
                FROM network_data_flowstat
                WHERE mac_address IS NOT NULL
                GROUP BY bucket, mac_address, classification, protocol, port;
            """,
            reverse_sql="""
                DROP MATERIALIZED VIEW IF EXISTS network_data_flowstat_usage_1min;
            """
        ),
        
        # Add refresh policy for the usage continuous aggregate
        migrations.RunSQL(
            sql="""
                -- Add refresh policy for the usage continuous aggregate
                SELECT add_continuous_aggregate_policy(
                    'network_data_flowstat_usage_1min',
                    start_offset => INTERVAL '3 minute',
                    end_offset => INTERVAL '1 minute',
                    schedule_interval => INTERVAL '1 minute'
                );
            """,
            reverse_sql="""
                SELECT remove_continuous_aggregate_policy('network_data_flowstat_usage_1min');
            """
        ),
        
        # Enable compression on the usage continuous aggregate
        migrations.RunSQL(
            sql="""
                -- Enable compression on the usage continuous aggregate
                ALTER MATERIALIZED VIEW network_data_flowstat_usage_1min SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'mac_address, classification, protocol',
                    timescaledb.compress_orderby = 'bucket DESC'
                );
            """,
            reverse_sql="""
                ALTER MATERIALIZED VIEW network_data_flowstat_usage_1min SET (timescaledb.compress = false);
            """
        ),
        
        # Add compression policy for the usage continuous aggregate (if it doesn't exist)
        migrations.RunSQL(
            sql="""
                -- Add compression policy for the usage continuous aggregate
                DO $$
                BEGIN
                    PERFORM add_compression_policy('network_data_flowstat_usage_1min', INTERVAL '1 hour');
                EXCEPTION
                    WHEN duplicate_object THEN
                        -- Policy already exists, ignore
                        NULL;
                END $$;
            """,
            reverse_sql="""
                SELECT remove_compression_policy('network_data_flowstat_usage_1min');
            """
        ),
    ]
