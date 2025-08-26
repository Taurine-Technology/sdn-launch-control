from django.core.management.base import BaseCommand
from odl.models import Category
from classifier.model_manager import model_manager


class Command(BaseCommand):
    help = 'Validates that database categories match the active model configuration.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model-name',
            type=str,
            help='Specific model name to validate against (defaults to active model)'
        )
        parser.add_argument(
            '--fix-missing',
            action='store_true',
            help='Automatically create missing categories'
        )

    def handle(self, *args, **options):
        model_name = options.get('model_name')
        fix_missing = options.get('fix_missing', False)
        
        self.stdout.write(self.style.SUCCESS('Validating model categories...'))
        
        # Get the model to validate against
        if model_name:
            if model_name not in model_manager.models:
                self.stdout.write(self.style.ERROR(f"Model '{model_name}' not found in configuration"))
                return
            target_model = model_manager.models[model_name]
            self.stdout.write(f"Validating against model: {model_name}")
        else:
            if not model_manager.active_model:
                self.stdout.write(self.style.ERROR("No active model configured"))
                return
            target_model = model_manager.models[model_manager.active_model]
            self.stdout.write(f"Validating against active model: {model_manager.active_model}")
        
        # Get expected categories from model
        expected_categories = set(target_model.categories)
        self.stdout.write(f"Expected categories ({len(expected_categories)}): {sorted(expected_categories)}")
        
        # Get actual categories from database
        db_categories = set(Category.objects.values_list('name', flat=True))
        self.stdout.write(f"Database categories ({len(db_categories)}): {sorted(db_categories)}")
        
        # Find differences
        missing_categories = expected_categories - db_categories
        extra_categories = db_categories - expected_categories
        
        # Report results
        if not missing_categories and not extra_categories:
            self.stdout.write(self.style.SUCCESS('✅ All categories match!'))
        else:
            if missing_categories:
                self.stdout.write(self.style.WARNING(
                    f'⚠️  Missing categories ({len(missing_categories)}): {sorted(missing_categories)}'))
                
                if fix_missing:
                    self.stdout.write('Creating missing categories...')
                    created_count = 0
                    for category_name in missing_categories:
                        try:
                            category, created = Category.objects.get_or_create(name=category_name)
                            if created:
                                self.stdout.write(self.style.SUCCESS(
                                    f'✅ Created: "{category.name}" (Cookie: {category.category_cookie})'))
                                created_count += 1
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(
                                f'❌ Error creating "{category_name}": {e}'))
                    
                    self.stdout.write(self.style.SUCCESS(f'Created {created_count} missing categories.'))
                else:
                    self.stdout.write(self.style.NOTICE(
                        'Run with --fix-missing to automatically create missing categories.'))
            
            if extra_categories:
                self.stdout.write(self.style.WARNING(
                    f'⚠️  Extra categories in database ({len(extra_categories)}): {sorted(extra_categories)}'))
                self.stdout.write(self.style.NOTICE(
                    'These categories exist in the database but are not in the model configuration.'))
        
        # Check for categories without cookies
        categories_without_cookies = Category.objects.filter(category_cookie__isnull=True)
        if categories_without_cookies.exists():
            self.stdout.write(self.style.WARNING(
                f'⚠️  Categories without cookies ({categories_without_cookies.count()}):'))
            for category in categories_without_cookies:
                self.stdout.write(f'   - {category.name}')
            
            if fix_missing:
                self.stdout.write('Fixing categories without cookies...')
                fixed_count = 0
                for category in categories_without_cookies:
                    try:
                        old_cookie = category.category_cookie
                        category.save()  # This will generate the cookie
                        self.stdout.write(self.style.SUCCESS(
                            f'✅ Fixed: "{category.name}" (Cookie: {category.category_cookie})'))
                        fixed_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f'❌ Error fixing "{category.name}": {e}'))
                
                self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} categories.'))
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('VALIDATION SUMMARY:')
        self.stdout.write(f'Model: {target_model.name}')
        self.stdout.write(f'Expected categories: {len(expected_categories)}')
        self.stdout.write(f'Database categories: {len(db_categories)}')
        self.stdout.write(f'Missing: {len(missing_categories)}')
        self.stdout.write(f'Extra: {len(extra_categories)}')
        self.stdout.write(f'Without cookies: {categories_without_cookies.count()}')
        
        if not missing_categories and not extra_categories and not categories_without_cookies.exists():
            self.stdout.write(self.style.SUCCESS('✅ VALIDATION PASSED'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  VALIDATION FAILED'))
