from django.core.management.base import BaseCommand
from general.models import Plugins


class Command(BaseCommand):
    help = 'Initializes the Plugins table with default values if empty'

    def handle(self, *args, **options):
        if not Plugins.objects.exists():
            Plugins.objects.create(
                alias='ONOS Traffic Classification Plugin',
                name='tau-onos-metre-traffic-classification',
                version='0.0.1',
                short_description='Create ONOS Metres based on Traffic Classifications',
                long_description='Create ONOS metres and link them to classifications.',
                author='Taurine Technology',
                installed=False,
            )
            Plugins.objects.create(
                alias='Traffic Classification Sniffer',
                name='tau-traffic-classification-sniffer',
                version='0.0.1',
                short_description='Traffic sniffer that interfaces with Launch Control\'s AI models to classify your network traffic in real-time.',
                long_description='The traffic sniffer sends small amounts of data per flow to the classification API to allow for real-time traffic classification. View the classifications on the dashboard.',
                author='Taurine Technology',
                installed=False,
            )
            self.stdout.write(self.style.SUCCESS('Default classifier model created.'))
        else:
            self.stdout.write(self.style.SUCCESS('Classifier model table already populated.'))
