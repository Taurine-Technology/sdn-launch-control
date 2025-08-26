from django.core.management.base import BaseCommand
from classifier.models import ModelConfiguration
import json
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Initialize model configurations from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing models'
        )

    def handle(self, *args, **options):
        force_update = options.get('force', False)
        
        self.stdout.write(self.style.SUCCESS('Initializing model configurations from JSON...'))
        
        json_config_path = os.path.join(settings.BASE_DIR, 'classifier/models_config.json')
        
        if not os.path.exists(json_config_path):
            self.stdout.write(self.style.ERROR(f'JSON configuration file not found: {json_config_path}'))
            return
        
        try:
            with open(json_config_path, 'r') as f:
                config_data = json.load(f)
            
            models_created = 0
            models_updated = 0
            
            for model_key, model_data in config_data.get('models', {}).items():
                model_path = os.path.join(settings.BASE_DIR, model_data['model_path'])
                
                # Check if model already exists
                existing_model = ModelConfiguration.objects.filter(name=model_key).first()
                
                if existing_model and not force_update:
                    self.stdout.write(self.style.NOTICE(f'Model {model_key} already exists, skipping...'))
                    continue
                elif existing_model and force_update:
                    self.stdout.write(self.style.NOTICE(f'Model {model_key} exists, will update...'))
                
                model_config_data = {
                    'name': model_key,
                    'display_name': model_data['name'],
                    'model_type': model_data['model_type'],
                    'model_path': model_path,
                    'input_shape': model_data.get('input_shape', [225, 5]),
                    'num_categories': model_data['num_categories'],
                    'confidence_threshold': model_data.get('confidence_threshold', 0.7),
                    'description': model_data.get('description', ''),
                    'version': model_data.get('version', '1.0'),
                    'is_active': model_data.get('is_active', False),
                    'categories': model_data['categories']
                }
                
                if existing_model:
                    # Update existing model
                    for field, value in model_config_data.items():
                        setattr(existing_model, field, value)
                    existing_model.save()
                    models_updated += 1
                    self.stdout.write(self.style.SUCCESS(f'Updated model: {model_key}'))
                else:
                    # Create new model
                    ModelConfiguration.objects.create(**model_config_data)
                    models_created += 1
                    self.stdout.write(self.style.SUCCESS(f'Created model: {model_key}'))
            
            self.stdout.write(self.style.SUCCESS(
                f'Initialization complete. {models_created} created, {models_updated} updated.'
            ))
            
            # Show current models
            total_models = ModelConfiguration.objects.count()
            active_models = ModelConfiguration.objects.filter(is_active=True).count()
            
            self.stdout.write(f'Total models in database: {total_models}')
            self.stdout.write(f'Active models: {active_models}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error initializing models: {e}'))
