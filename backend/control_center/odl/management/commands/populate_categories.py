
from django.core.management.base import BaseCommand, CommandError
from odl.models import Category
from classifier.model_manager import model_manager
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Populates the Category model with categories from the active model configuration (legacy command).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'This command is deprecated. Please use "populate_categories_from_model" instead.'))
        
        try:
            call_command('populate_categories_from_model')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error calling new command: {e}'))
            
            # Fallback to old behavior if new command fails
            self.stdout.write(self.style.NOTICE('Falling back to legacy behavior...'))
            self._legacy_populate_categories()
    
    def _legacy_populate_categories(self):
        """Legacy method for backward compatibility"""
        # List of categories to ensure exist (legacy fallback)
        PREDEFINED_CATEGORIES = [
            "ADS_Analytic_Track", "AmazonAWS", "BitTorrent", "Facebook", "FbookReelStory",
            "GMail", "Google", "GoogleServices", "HTTP", "HuaweiCloud", "Instagram",
            "Messenger", "Microsoft", "NetFlix", "QUIC", "TikTok", "TLS", "Unknown",
            "WhatsApp", "WhatsAppFiles", "WindowsUpdate", "YouTube"
        ]

        self.stdout.write(self.style.SUCCESS('Starting to populate categories (legacy mode)...'))
        created_count = 0
        skipped_count = 0

        for category_name in PREDEFINED_CATEGORIES:
            category, created = Category.objects.get_or_create(name=category_name)
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully created category: "{category.name}" (Cookie: {category.category_cookie})'))
                created_count += 1
            else:
                # If it already existed, ensure the cookie is populated if it was somehow missed
                if not category.category_cookie:
                    category.save()  # This will trigger the cookie generation
                    self.stdout.write(self.style.NOTICE(
                        f'Category "{category.name}" already exists. Cookie updated/verified: {category.category_cookie}'))
                else:
                    self.stdout.write(self.style.NOTICE(
                        f'Category "{category.name}" (Cookie: {category.category_cookie}) already exists. Skipped.'))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f'Finished populating categories. {created_count} created, {skipped_count} skipped.'))

