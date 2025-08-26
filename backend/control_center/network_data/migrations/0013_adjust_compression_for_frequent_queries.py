# File: network_data/migrations/0013_adjust_compression_for_frequent_queries.py
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
        ('network_data', '0012_create_flowstat_usage_aggregate'),
    ]

    operations = [
        # Adjust compression policies for better day/week query performance
        migrations.RunSQL(
            sql="""
                -- Remove existing compression policies
                DO $$
                BEGIN
                    PERFORM remove_compression_policy('network_data_flowstat');
                EXCEPTION
                    WHEN undefined_object THEN
                        -- Policy doesn't exist, ignore
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM remove_compression_policy('network_data_flow');
                EXCEPTION
                    WHEN undefined_object THEN
                        -- Policy doesn't exist, ignore
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM remove_compression_policy('network_data_flow_1min');
                EXCEPTION
                    WHEN undefined_object THEN
                        -- Policy doesn't exist, ignore
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM remove_compression_policy('network_data_flow_by_mac_1min');
                EXCEPTION
                    WHEN undefined_object THEN
                        -- Policy doesn't exist, ignore
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM remove_compression_policy('network_data_flowstat_usage_1min');
                EXCEPTION
                    WHEN undefined_object THEN
                        -- Policy doesn't exist, ignore
                        NULL;
                END $$;
                
                -- Add new compression policies with longer intervals for better day/week query performance
                -- Compress data after 24 hours instead of 1 hour for main tables
                DO $$
                BEGIN
                    PERFORM add_compression_policy('network_data_flowstat', INTERVAL '24 hours');
                EXCEPTION
                    WHEN duplicate_object THEN
                        -- Policy already exists, ignore
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM add_compression_policy('network_data_flow', INTERVAL '24 hours');
                EXCEPTION
                    WHEN duplicate_object THEN
                        -- Policy already exists, ignore
                        NULL;
                END $$;
                
                -- Compress continuous aggregates after 7 days (since they're pre-aggregated)
                DO $$
                BEGIN
                    PERFORM add_compression_policy('network_data_flow_1min', INTERVAL '7 days');
                EXCEPTION
                    WHEN duplicate_object THEN
                        -- Policy already exists, ignore
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM add_compression_policy('network_data_flow_by_mac_1min', INTERVAL '7 days');
                EXCEPTION
                    WHEN duplicate_object THEN
                        -- Policy already exists, ignore
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM add_compression_policy('network_data_flowstat_usage_1min', INTERVAL '7 days');
                EXCEPTION
                    WHEN duplicate_object THEN
                        -- Policy already exists, ignore
                        NULL;
                END $$;
            """,
            reverse_sql="""
                -- Revert to original 1-hour compression policies
                DO $$
                BEGIN
                    PERFORM remove_compression_policy('network_data_flowstat');
                EXCEPTION
                    WHEN undefined_object THEN
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM remove_compression_policy('network_data_flow');
                EXCEPTION
                    WHEN undefined_object THEN
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM remove_compression_policy('network_data_flow_1min');
                EXCEPTION
                    WHEN undefined_object THEN
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM remove_compression_policy('network_data_flow_by_mac_1min');
                EXCEPTION
                    WHEN undefined_object THEN
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM remove_compression_policy('network_data_flowstat_usage_1min');
                EXCEPTION
                    WHEN undefined_object THEN
                        NULL;
                END $$;
                
                -- Add back 1-hour policies
                DO $$
                BEGIN
                    PERFORM add_compression_policy('network_data_flowstat', INTERVAL '1 hour');
                EXCEPTION
                    WHEN duplicate_object THEN
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM add_compression_policy('network_data_flow', INTERVAL '1 hour');
                EXCEPTION
                    WHEN duplicate_object THEN
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM add_compression_policy('network_data_flow_1min', INTERVAL '1 hour');
                EXCEPTION
                    WHEN duplicate_object THEN
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM add_compression_policy('network_data_flow_by_mac_1min', INTERVAL '1 hour');
                EXCEPTION
                    WHEN duplicate_object THEN
                        NULL;
                END $$;
                
                DO $$
                BEGIN
                    PERFORM add_compression_policy('network_data_flowstat_usage_1min', INTERVAL '1 hour');
                EXCEPTION
                    WHEN duplicate_object THEN
                        NULL;
                END $$;
            """
        ),
    ]
