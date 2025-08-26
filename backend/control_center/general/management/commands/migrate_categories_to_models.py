from django.core.management.base import BaseCommand, CommandError
from odl.models import Category
from classifier.model_manager import model_manager


class Command(BaseCommand):
    help = 'Migrates existing categories to be linked to the active model configuration.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model-name',
            type=str,
            help='Specific model name to link categories to (defaults to active model)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if categories already exist for the model'
        )

    def handle(self, *args, **options):
        model_name = options.get('model_name')
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        
        self.stdout.write(self.style.SUCCESS('Starting category migration to model configuration...'))
        
        # Get the target model configuration
        if model_name:
            try:
                from classifier.models import ModelConfiguration
                target_model_config = ModelConfiguration.objects.get(name=model_name)
                self.stdout.write(f"Using specified model: {model_name}")
            except ModelConfiguration.DoesNotExist:
                raise CommandError(f"Model '{model_name}' not found in database")
        else:
            if not model_manager.active_model:
                raise CommandError("No active model configured")
            
            try:
                from classifier.models import ModelConfiguration
                target_model_config = ModelConfiguration.objects.get(name=model_manager.active_model)
                self.stdout.write(f"Using active model: {model_manager.active_model}")
            except ModelConfiguration.DoesNotExist:
                raise CommandError(f"Active model '{model_manager.active_model}' not found in database")
        
        # Get categories that should exist for this model
        expected_categories = set(target_model_config.categories)
        
        # Get existing categories for this model
        existing_model_categories = set(Category.objects.filter(
            model_configuration=target_model_config
        ).values_list('name', flat=True))
        
        # Get legacy categories (no model_configuration)
        legacy_categories = set(Category.objects.filter(
            model_configuration__isnull=True
        ).values_list('name', flat=True))
        
        self.stdout.write(f"Expected categories for model '{target_model_config.name}': {len(expected_categories)}")
        self.stdout.write(f"Existing model-specific categories: {len(existing_model_categories)}")
        self.stdout.write(f"Legacy categories (no model): {len(legacy_categories)}")
        
        # Categories that need to be created for this model
        categories_to_create = expected_categories - existing_model_categories
        
        # Categories that exist as legacy but need to be linked to this model
        categories_to_link = expected_categories & legacy_categories
        
        # Categories that exist for this model but are not in expected categories
        categories_to_remove = existing_model_categories - expected_categories
        
        if dry_run:
            self.stdout.write(self.style.NOTICE("\n=== DRY RUN - No changes will be made ==="))
            
            if categories_to_create:
                self.stdout.write(f"\nCategories to create for model '{target_model_config.name}':")
                for cat in sorted(categories_to_create):
                    self.stdout.write(f"  + {cat}")
            
            if categories_to_link:
                self.stdout.write(f"\nLegacy categories to link to model '{target_model_config.name}':")
                for cat in sorted(categories_to_link):
                    self.stdout.write(f"  → {cat}")
            
            if categories_to_remove and force:
                self.stdout.write(f"\nCategories to remove from model '{target_model_config.name}':")
                for cat in sorted(categories_to_remove):
                    self.stdout.write(f"  - {cat}")
            
            return
        
        # Perform the migration
        created_count = 0
        linked_count = 0
        removed_count = 0
        
        # Create new categories for this model
        for category_name in categories_to_create:
            try:
                category = Category.objects.create(
                    name=category_name,
                    model_configuration=target_model_config
                )
                self.stdout.write(self.style.SUCCESS(f"✅ Created category: {category_name}"))
                created_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed to create category '{category_name}': {e}"))
        
        # Link existing legacy categories to this model
        for category_name in categories_to_link:
            try:
                # Find the legacy category and update it to link to the model
                legacy_category = Category.objects.get(name=category_name, model_configuration__isnull=True)
                legacy_category.model_configuration = target_model_config
                legacy_category.save()
                self.stdout.write(self.style.SUCCESS(f"🔗 Linked category: {category_name}"))
                linked_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed to link category '{category_name}': {e}"))
        
        # Remove categories that shouldn't be in this model (if force is enabled)
        if force and categories_to_remove:
            for category_name in categories_to_remove:
                try:
                    category = Category.objects.get(name=category_name, model_configuration=target_model_config)
                    category.delete()
                    self.stdout.write(self.style.WARNING(f"🗑️ Removed category: {category_name}"))
                    removed_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Failed to remove category '{category_name}': {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"\n=== Migration Summary ==="))
        self.stdout.write(f"Created: {created_count}")
        self.stdout.write(f"Linked: {linked_count}")
        self.stdout.write(f"Removed: {removed_count}")
        self.stdout.write(f"Total changes: {created_count + linked_count + removed_count}")
        
        if created_count + linked_count + removed_count > 0:
            self.stdout.write(self.style.SUCCESS("✅ Category migration completed successfully!"))
        else:
            self.stdout.write(self.style.NOTICE("ℹ️ No changes were needed."))
