from django.core.management.base import BaseCommand
from classifier.model_manager import model_manager
from classifier.state_manager import state_manager
from classifier.models import ModelConfiguration


class Command(BaseCommand):
    help = 'Check and fix model state issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix model state issues',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Model State Check ===")
        
        # Check Redis connection
        if not state_manager.health_check():
            self.stdout.write(self.style.ERROR("❌ Redis connection failed"))
            return
        
        self.stdout.write(self.style.SUCCESS("✅ Redis connection OK"))
        
        # Check active model in Redis
        active_model_redis = state_manager.get_active_model()
        self.stdout.write(f"Active model in Redis: {active_model_redis or 'None'}")
        
        # Check active model in database
        try:
            active_model_db = ModelConfiguration.objects.filter(is_active=True).first()
            self.stdout.write(f"Active model in database: {active_model_db.name if active_model_db else 'None'}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error checking database: {e}"))
            return
        
        # Check loaded models
        loaded_models = state_manager.get_loaded_models()
        self.stdout.write(f"Loaded models in Redis: {loaded_models}")
        
        # Check model manager state
        model_manager_loaded = list(model_manager.loaded_models.keys())
        self.stdout.write(f"Models loaded in memory: {model_manager_loaded}")
        
        # Check for inconsistencies
        issues_found = []
        
        if active_model_redis != (active_model_db.name if active_model_db else None):
            issues_found.append("Active model mismatch between Redis and database")
        
        if active_model_redis and active_model_redis not in loaded_models:
            issues_found.append("Active model not in loaded models list")
        
        if active_model_redis and active_model_redis not in model_manager_loaded:
            issues_found.append("Active model not loaded in memory")
        
        if not active_model_redis and active_model_db:
            issues_found.append("Active model in database but not in Redis")
        
        if issues_found:
            self.stdout.write(self.style.WARNING("⚠️  Issues found:"))
            for issue in issues_found:
                self.stdout.write(f"  - {issue}")
            
            if options['fix']:
                self.stdout.write("\n🔧 Attempting to fix issues...")
                self._fix_issues(active_model_db)
            else:
                self.stdout.write("\nRun with --fix to attempt automatic repair")
        else:
            self.stdout.write(self.style.SUCCESS("✅ No issues found"))
    
    def _fix_issues(self, active_model_db):
        """Attempt to fix model state issues"""
        if active_model_db:
            # Set active model in Redis
            if state_manager.set_active_model(active_model_db.name):
                self.stdout.write(f"✅ Set active model in Redis: {active_model_db.name}")
            else:
                self.stdout.write(self.style.ERROR(f"❌ Failed to set active model in Redis"))
            
            # Load model if not loaded
            if active_model_db.name not in model_manager.loaded_models:
                if model_manager.load_model(active_model_db.name):
                    self.stdout.write(f"✅ Loaded model: {active_model_db.name}")
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Failed to load model: {active_model_db.name}"))
            
            # Add to loaded models list
            if active_model_db.name not in state_manager.get_loaded_models():
                if state_manager.add_loaded_model(active_model_db.name):
                    self.stdout.write(f"✅ Added model to loaded list: {active_model_db.name}")
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Failed to add model to loaded list"))
        else:
            self.stdout.write(self.style.WARNING("⚠️  No active model in database to restore"))

