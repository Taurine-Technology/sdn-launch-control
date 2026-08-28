# Migration to alter SNMPMetrics and SNMPInterfaceStats primary keys to include timestamp

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False  # Altering primary keys typically cannot run inside a transaction

    dependencies = [
        ('snmp_monitoring', '0001_initial'),
    ]

    operations = [
        # Alter SNMPMetrics primary key
        migrations.RunSQL(
            sql="""
                -- Drop the automatically created primary key constraint.
                ALTER TABLE snmp_monitoring_snmpmetrics DROP CONSTRAINT snmp_monitoring_snmpmetrics_pkey;
                -- Create a composite primary key including the partitioning column (timestamp) and the id.
                ALTER TABLE snmp_monitoring_snmpmetrics ADD PRIMARY KEY (timestamp, id);
            """,
            reverse_sql="""
                -- Reverse: Drop the composite primary key and restore the original primary key on id.
                ALTER TABLE snmp_monitoring_snmpmetrics DROP CONSTRAINT snmp_monitoring_snmpmetrics_pkey;
                ALTER TABLE snmp_monitoring_snmpmetrics ADD PRIMARY KEY (id);
            """,
        ),
        # Alter SNMPInterfaceStats primary key
        migrations.RunSQL(
            sql="""
                -- Drop the automatically created primary key constraint.
                ALTER TABLE snmp_monitoring_snmpinterfacestats DROP CONSTRAINT snmp_monitoring_snmpinterfacestats_pkey;
                -- Create a composite primary key including the partitioning column (timestamp) and the id.
                ALTER TABLE snmp_monitoring_snmpinterfacestats ADD PRIMARY KEY (timestamp, id);
            """,
            reverse_sql="""
                -- Reverse: Drop the composite primary key and restore the original primary key on id.
                ALTER TABLE snmp_monitoring_snmpinterfacestats DROP CONSTRAINT snmp_monitoring_snmpinterfacestats_pkey;
                ALTER TABLE snmp_monitoring_snmpinterfacestats ADD PRIMARY KEY (id);
            """,
        ),
    ]

