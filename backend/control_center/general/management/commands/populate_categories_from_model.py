from django.core.management.base import BaseCommand, CommandError
from odl.models import Category
from classifier.model_manager import model_manager
from classifier.models import ModelConfiguration
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Populates the Category model with categories from the active model configuration.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model-name',
            type=str,
            help='Specific model name to use for categories (defaults to active model)'
        )
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Force update existing categories (regenerate cookies)'
        )

    def handle(self, *args, **options):
        model_name = options.get('model_name')
        force_update = options.get('force_update', False)
        
        self.stdout.write(self.style.SUCCESS('Starting to populate categories from model configuration...'))
        
        # Get the model to use for categories and store the ModelConfiguration instance
        model_config = None
        
        if model_name:
            # Check if model exists in database
            try:
                model_config = ModelConfiguration.objects.get(name=model_name)
                target_model = type('ModelConfig', (), {
                    'name': model_config.display_name,
                    'categories': model_config.categories
                })()
                self.stdout.write(f"Using specified model: {model_name}")
            except ModelConfiguration.DoesNotExist:
                raise CommandError(f"Model '{model_name}' not found in database")
        else:
            if not model_manager.active_model:
                # Try to get the first active model from database
                try:
                    model_config = ModelConfiguration.objects.filter(is_active=True).first()
                    if model_config:
                        target_model = type('ModelConfig', (), {
                            'name': model_config.display_name,
                            'categories': model_config.categories
                        })()
                        self.stdout.write(f"Using active model from database: {model_config.name}")
                    else:
                        raise CommandError("No active model found in database")
                except Exception as e:
                    raise CommandError(f"No active model configured: {e}")
            else:
                # Use the active model from model manager
                try:
                    model_config = ModelConfiguration.objects.get(name=model_manager.active_model)
                    target_model = type('ModelConfig', (), {
                        'name': model_config.display_name,
                        'categories': model_config.categories
                    })()
                    self.stdout.write(f"Using active model: {model_manager.active_model}")
                except ModelConfiguration.DoesNotExist:
                    raise CommandError(f"Active model '{model_manager.active_model}' not found in database")
        
        # Verify we have a valid model_config
        if not model_config:
            raise CommandError("Failed to retrieve model configuration")
        
        # Get categories from the model configuration
        categories = target_model.categories
        
        if not categories:
            raise CommandError(f"No categories found in model configuration for '{target_model.name}'")
        
        self.stdout.write(f"Found {len(categories)} categories in model configuration")
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for category_name in categories:
            try:
                # Get or create category with model configuration (reuse model_config)
                category, created = Category.objects.get_or_create(
                    name=category_name,
                    model_configuration=model_config
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f'✅ Created category: "{category.name}" (Cookie: {category.category_cookie})'))
                    created_count += 1
                else:
                    # Category already exists
                    if force_update:
                        # Force regenerate the cookie
                        old_cookie = category.category_cookie
                        category.save()  # This will regenerate the cookie
                        self.stdout.write(self.style.WARNING(
                            f'🔄 Updated category: "{category.name}" (Cookie: {old_cookie} → {category.category_cookie})'))
                        updated_count += 1
                    else:
                        # Just verify the cookie exists
                        if not category.category_cookie:
                            category.save()  # This will generate the cookie
                            self.stdout.write(self.style.WARNING(
                                f'🔧 Fixed category: "{category.name}" (Cookie: {category.category_cookie})'))
                            updated_count += 1
                        else:
                            self.stdout.write(
                                f'⏭️  Skipped category: "{category.name}" (Cookie: {category.category_cookie})')
                            skipped_count += 1
                            
            except Exception as e:
                logger.exception(f'Error processing category "{category_name}"')
                self.stdout.write(self.style.ERROR(
                    f'❌ Error processing category "{category_name}": {e}'))
        
        # Ensure standard fallback categories always exist (reuse model_config from above)
        self.stdout.write('Ensuring standard fallback categories exist...')
        
        if model_config:
            # Standard fallback categories that should always exist
            standard_categories = ["Unknown", "DNS", "Apple"]
            
            for standard_category_name in standard_categories:
                try:
                    # Check if category already exists for this model
                    category, category_created = Category.objects.get_or_create(
                        name=standard_category_name,
                        model_configuration=model_config
                    )
                    
                    if category_created:
                        self.stdout.write(self.style.SUCCESS(
                            f'✅ Created standard "{standard_category_name}" category (Cookie: {category.category_cookie})'))
                        created_count += 1
                    else:
                        # Verify the cookie exists
                        if not category.category_cookie:
                            category.save()  # This will generate the cookie
                            self.stdout.write(self.style.WARNING(
                                f'🔧 Fixed standard "{standard_category_name}" category (Cookie: {category.category_cookie})'))
                            updated_count += 1
                        else:
                            self.stdout.write(
                                f'⏭️  Standard "{standard_category_name}" category already exists (Cookie: {category.category_cookie})')
                            skipped_count += 1
                            
                except Exception as e:
                    logger.exception(f'Error ensuring standard category "{standard_category_name}" for model {model_config.name}')
                    self.stdout.write(self.style.ERROR(
                        f'❌ Error ensuring "{standard_category_name}" category: {e}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'Finished populating categories from model "{target_model.name}". '
            f'{created_count} created, {updated_count} updated, {skipped_count} skipped.'))
        
        # Summary
        total_categories = Category.objects.count()
        self.stdout.write(f'Total categories in database: {total_categories}')
        
        # Verify all categories have cookies
        categories_without_cookies = Category.objects.filter(category_cookie__isnull=True).count()
        if categories_without_cookies > 0:
            self.stdout.write(self.style.WARNING(
                f'⚠️  {categories_without_cookies} categories without cookies found. '
                f'Run with --force-update to fix.'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ All categories have valid cookies.'))
