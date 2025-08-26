from django.core.management.base import BaseCommand
from general.models import ClassifierModel


# class Command(BaseCommand):
#     help = 'Initializes the ClassifierModel table with default values if empty'
#
#     def handle(self, *args, **options):
#         if not ClassifierModel.objects.exists():
#             ClassifierModel.objects.create(
#                 name='attention_23_8400',
#                 number_of_bytes=225,
#                 number_of_packets=5,
#                 categories='AmazonAWS,Apple,Cloudflare,Cybersec,Facebook,GMail,Google,GoogleCloud,GoogleDocs,GoogleServices,HTTP,Instagram,Microsoft,Snapchat,Spotify,TLS,TikTok,Twitter,Unknown,WhatsApp,WhatsAppFiles,Xiaomi,YouTube'
#             )
#             self.stdout.write(self.style.SUCCESS('Default classifier model created.'))
#         else:
#             self.stdout.write(self.style.SUCCESS('Classifier model table already populated.'))

class Command(BaseCommand):
    help = 'Initializes the ClassifierModel table with default values if empty'

    def handle(self, *args, **options):
        if not ClassifierModel.objects.exists():
            ClassifierModel.objects.create(
                name='complex_22_9500_masked',
                number_of_bytes=225,
                number_of_packets=5,
                categories="ADS_Analytic_Track,AmazonAWS,BitTorrent,Facebook,FbookReelStory,GMail,Google,GoogleServices,HTTP,HuaweiCloud,Instagram,Messenger,Microsoft,NetFlix,QUIC,TikTok,TLS,Unknown,WhatsApp,WhatsAppFiles,WindowsUpdate,YouTube"
            )
            self.stdout.write(self.style.SUCCESS('Default classifier model created.'))
        else:
            self.stdout.write(self.style.SUCCESS('Classifier model table already populated.'))
