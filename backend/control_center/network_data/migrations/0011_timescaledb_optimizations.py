# File: network_data/migrations/0011_timescaledb_optimizations.py
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
        ('network_data', '0010_alter_flowstat_options_and_more'),
    ]

    operations = [
        # Step 1: Enable compression on FlowStat hypertable
        migrations.RunSQL(
            sql="""
                -- Enable compression on FlowStat hypertable
                ALTER TABLE network_data_flowstat SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'classification, mac_address, protocol',
                    timescaledb.compress_orderby = 'timestamp DESC'
                );
            """,
            reverse_sql="""
                ALTER TABLE network_data_flowstat SET (timescaledb.compress = false);
            """
        ),
        
        # Step 2: Enable compression on Flow hypertable
        migrations.RunSQL(
            sql="""
                -- Enable compression on Flow hypertable
                ALTER TABLE network_data_flow SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'classification, src_mac, dst_mac',
                    timescaledb.compress_orderby = 'timestamp DESC'
                );
            """,
            reverse_sql="""
                ALTER TABLE network_data_flow SET (timescaledb.compress = false);
            """
        ),
        
        # Step 3: Add compression policies (if they don't exist)
        migrations.RunSQL(
            sql="""
                -- Add compression policy for FlowStat (compress chunks older than 1 hour)
                DO $$
                BEGIN
                    PERFORM add_compression_policy('network_data_flowstat', INTERVAL '1 hour');
                EXCEPTION
                    WHEN duplicate_object THEN
                        -- Policy already exists, ignore
                        NULL;
                END $$;
                
                -- Add compression policy for Flow (compress chunks older than 1 hour)
                DO $$
                BEGIN
                    PERFORM add_compression_policy('network_data_flow', INTERVAL '1 hour');
                EXCEPTION
                    WHEN duplicate_object THEN
                        -- Policy already exists, ignore
                        NULL;
                END $$;
            """,
            reverse_sql="""
                SELECT remove_compression_policy('network_data_flowstat');
                SELECT remove_compression_policy('network_data_flow');
            """
        ),
        
        # Step 4: Add retention policies (keep data for 90 days)
        migrations.RunSQL(
            sql="""
                -- Add retention policy for FlowStat (keep 90 days)
                DO $$
                BEGIN
                    PERFORM add_retention_policy('network_data_flowstat', INTERVAL '90 days');
                EXCEPTION
                    WHEN duplicate_object THEN
                        -- Policy already exists, ignore
                        NULL;
                END $$;
                
                -- Add retention policy for Flow (keep 90 days)
                DO $$
                BEGIN
                    PERFORM add_retention_policy('network_data_flow', INTERVAL '90 days');
                EXCEPTION
                    WHEN duplicate_object THEN
                        -- Policy already exists, ignore
                        NULL;
                END $$;
            """,
            reverse_sql="""
                SELECT remove_retention_policy('network_data_flowstat');
                SELECT remove_retention_policy('network_data_flow');
            """
        ),
        
        # Step 5: Enable compression on existing continuous aggregates
        migrations.RunSQL(
            sql="""
                -- Enable compression on continuous aggregates
                ALTER MATERIALIZED VIEW network_data_flow_1min SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'classification',
                    timescaledb.compress_orderby = 'bucket DESC'
                );
                
                ALTER MATERIALIZED VIEW network_data_flow_by_mac_1min SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'src_mac, classification',
                    timescaledb.compress_orderby = 'bucket DESC'
                );
            """,
            reverse_sql="""
                ALTER MATERIALIZED VIEW network_data_flow_1min SET (timescaledb.compress = false);
                ALTER MATERIALIZED VIEW network_data_flow_by_mac_1min SET (timescaledb.compress = false);
            """
        ),
        
        # Step 6: Add compression policies for continuous aggregates (if they don't exist)
        migrations.RunSQL(
            sql="""
                -- Add compression policies for continuous aggregates
                DO $$
                BEGIN
                    PERFORM add_compression_policy('network_data_flow_1min', INTERVAL '1 hour');
                EXCEPTION
                    WHEN duplicate_object THEN
                        -- Policy already exists, ignore
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM add_compression_policy('network_data_flow_by_mac_1min', INTERVAL '1 hour');
                EXCEPTION
                    WHEN duplicate_object THEN
                        -- Policy already exists, ignore
                        NULL;
                END $$;
            """,
            reverse_sql="""
                SELECT remove_compression_policy('network_data_flow_1min');
                SELECT remove_compression_policy('network_data_flow_by_mac_1min');
            """
        ),
    ]
