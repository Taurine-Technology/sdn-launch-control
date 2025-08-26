from django.core.management.base import BaseCommand
from classifier.model_manager import model_manager
import numpy as np


class Command(BaseCommand):
    help = 'Test the model manager functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['list', 'load', 'unload', 'set-active', 'predict'],
            help='Action to perform'
        )
        parser.add_argument(
            '--model-name',
            type=str,
            help='Model name for load/unload/set-active actions'
        )

    def handle(self, *args, **options):
        action = options.get('action', 'list')
        model_name = options.get('model_name')

        self.stdout.write("Testing Model Manager")
        self.stdout.write("=" * 50)

        if action == 'list':
            self.list_models()
        elif action == 'load':
            if not model_name:
                self.stdout.write(self.style.ERROR('--model-name is required for load action'))
                return
            self.load_model(model_name)
        elif action == 'unload':
            if not model_name:
                self.stdout.write(self.style.ERROR('--model-name is required for unload action'))
                return
            self.unload_model(model_name)
        elif action == 'set-active':
            if not model_name:
                self.stdout.write(self.style.ERROR('--model-name is required for set-active action'))
                return
            self.set_active_model(model_name)
        elif action == 'predict':
            self.test_prediction()

    def list_models(self):
        """List all available models"""
        self.stdout.write("Available Models:")
        self.stdout.write("-" * 30)
        
        models_info = model_manager.list_models()
        for model_info in models_info:
            status = "🟢 ACTIVE" if model_info['is_active'] else "⚪ INACTIVE"
            loaded = "📦 LOADED" if model_info['is_loaded'] else "📭 NOT LOADED"
            exists = "✅ EXISTS" if model_info['file_exists'] else "❌ MISSING"
            
            self.stdout.write(f"Name: {model_info['name']}")
            self.stdout.write(f"Display: {model_info['display_name']}")
            self.stdout.write(f"Status: {status} | {loaded} | {exists}")
            self.stdout.write(f"Type: {model_info['model_type']}")
            self.stdout.write(f"Categories: {model_info['num_categories']}")
            self.stdout.write(f"Confidence Threshold: {model_info['confidence_threshold']}")
            self.stdout.write("-" * 30)
        
        self.stdout.write(f"Active Model: {model_manager.active_model}")

    def load_model(self, model_name):
        """Load a specific model"""
        self.stdout.write(f"Loading model: {model_name}")
        
        success = model_manager.load_model(model_name)
        if success:
            self.stdout.write(self.style.SUCCESS(f"✅ Model '{model_name}' loaded successfully"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Failed to load model '{model_name}'"))

    def unload_model(self, model_name):
        """Unload a specific model"""
        self.stdout.write(f"Unloading model: {model_name}")
        
        success = model_manager.unload_model(model_name)
        if success:
            self.stdout.write(self.style.SUCCESS(f"✅ Model '{model_name}' unloaded successfully"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Failed to unload model '{model_name}'"))

    def set_active_model(self, model_name):
        """Set the active model"""
        self.stdout.write(f"Setting active model: {model_name}")
        
        success = model_manager.set_active_model(model_name)
        if success:
            self.stdout.write(self.style.SUCCESS(f"✅ Active model set to '{model_name}'"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Failed to set active model to '{model_name}'"))

    def test_prediction(self):
        """Test prediction with the active model"""
        self.stdout.write("Testing prediction with active model")
        
        if not model_manager.get_active_model():
            self.stdout.write(self.style.ERROR("❌ No active model available"))
            return
        
        # Create mock packet data
        mock_packet_array = np.random.randint(0, 256, (225, 5)).tolist()
        
        try:
            prediction, time_elapsed = model_manager.predict_flow(mock_packet_array, "8.8.8.8")
            self.stdout.write(self.style.SUCCESS(f"✅ Prediction: {prediction}"))
            self.stdout.write(f"⏱️  Time: {time_elapsed:.3f}s")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Prediction failed: {e}"))
