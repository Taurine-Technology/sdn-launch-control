from django.core.management.base import BaseCommand
from general.models import ClassifierModel


class Command(BaseCommand):
    help = 'Initializes the ClassifierModel table with default values if empty'

    def handle(self, *args, **options):
        if not ClassifierModel.objects.exists():
            ClassifierModel.objects.create(
                name='attention_23_8400',
                number_of_bytes=225,
                number_of_packets=5,
                categories='AmazonAWS,AppleCloudflare,Cybersec,Facebook,GMail,Google,GoogleCloud,GoogleDocs,GoogleServices,HTTP,Instagram,Microsoft,Snapchat,Spotify,TLS,TikTok,Twitter,Unknown,WhatsApp,WhatsAppFiles,Xiaomi,YouTube'
            )
            self.stdout.write(self.style.SUCCESS('Default classifier model created.'))
        else:
            self.stdout.write(self.style.SUCCESS('Classifier model table already populated.'))
