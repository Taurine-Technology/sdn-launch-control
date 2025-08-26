from django.core.management.base import BaseCommand
from software_plugin.models import Plugin

class Command(BaseCommand):
    help = "Initializes the Plugin table with default values if empty"

    def handle(self, *args, **options):
        if not Plugin.objects.exists():
            plugins = [
                {
                    "alias": "Opendaylight Traffic Classification Plugin",
                    "name": "tau-onos-metre-traffic-classification",
                    "version": "0.0.1",
                    "short_description": "Create Opendaylight Metres based on Traffic Classifications",
                    "long_description": "Create Opendaylight metres and link them to classifications.",
                    "author": "Taurine Technology",
                },
                {
                    "alias": "Traffic Classification Sniffer",
                    "name": "tau-traffic-classification-sniffer",
                    "version": "0.0.1",
                    "short_description": "Traffic sniffer that interfaces with Launch Control's AI models to classify your network traffic in real-time.",
                    "long_description": "The traffic sniffer sends small amounts of data per flow to the classification API to allow for real-time traffic classification. View the classifications on the dashboard.",
                    "author": "Taurine Technology",
                    "requires_target_device": True,
                }
            ]

            for plugin_data in plugins:
                Plugin.objects.create(**plugin_data)

            self.stdout.write(self.style.SUCCESS("Default plugins created."))
        else:
            self.stdout.write(self.style.SUCCESS("Plugin table already populated."))
