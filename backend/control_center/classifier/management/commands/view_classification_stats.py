"""
Django Management Command: view_classification_stats

This command displays classification statistics for models.
"""

from django.core.management.base import BaseCommand
from classifier.models import ClassificationStats, ModelConfiguration
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Avg


class Command(BaseCommand):
    help = 'View classification statistics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            help='Filter by model name',
            default=None
        )
        parser.add_argument(
            '--hours',
            type=int,
            help='Show stats for last N hours (default: 24)',
            default=24
        )
        parser.add_argument(
            '--summary',
            action='store_true',
            help='Show summary statistics only'
        )

    def handle(self, *args, **options):
        model_name = options.get('model')
        hours = options.get('hours', 24)
        summary_only = options.get('summary', False)
        
        # Calculate time range
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('CLASSIFICATION STATISTICS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(f'Time Range: Last {hours} hours')
        self.stdout.write(f'From: {start_time.strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write(f'To:   {end_time.strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write('')
        
        # Filter stats
        stats_query = ClassificationStats.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        )
        
        if model_name:
            try:
                model_config = ModelConfiguration.objects.get(name=model_name)
                stats_query = stats_query.filter(model_configuration=model_config)
                self.stdout.write(f'Model: {model_config.display_name} ({model_config.name})')
            except ModelConfiguration.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Model "{model_name}" not found'))
                return
        else:
            self.stdout.write('Model: All Models')
        
        self.stdout.write(self.style.SUCCESS('-' * 80))
        
        # Get stats
        stats = stats_query.order_by('-timestamp')
        
        if not stats.exists():
            self.stdout.write(self.style.WARNING('⚠️  No statistics found for the specified criteria'))
            return
        
        # Calculate aggregated statistics
        totals = stats_query.aggregate(
            total_classifications=Sum('total_classifications'),
            high_confidence=Sum('high_confidence_count'),
            low_confidence=Sum('low_confidence_count'),
            multiple_candidates=Sum('multiple_candidates_count'),
            uncertain=Sum('uncertain_count'),
            dns_detections=Sum('dns_detections'),
            asn_fallback=Sum('asn_fallback_count'),
            avg_prediction_time=Avg('avg_prediction_time_ms')
        )
        
        total_count = totals['total_classifications'] or 0
        
        if total_count == 0:
            self.stdout.write(self.style.WARNING('⚠️  No classifications recorded'))
            return
        
        # Display summary statistics
        self.stdout.write(self.style.SUCCESS('\n📊 SUMMARY STATISTICS'))
        self.stdout.write(self.style.SUCCESS('-' * 80))
        
        self.stdout.write(f'\nTotal Classifications: {total_count:,}')
        avg_time = totals["avg_prediction_time"] or 0.0
        self.stdout.write(f'Average Prediction Time: {avg_time:.2f} ms')
        
        self.stdout.write(f'\n📈 CONFIDENCE BREAKDOWN:')
        self.stdout.write(f'  High Confidence:      {totals["high_confidence"]:>8,}  ({(totals["high_confidence"]/total_count)*100:>5.1f}%)')
        self.stdout.write(f'  Low Confidence:       {totals["low_confidence"]:>8,}  ({(totals["low_confidence"]/total_count)*100:>5.1f}%)')
        self.stdout.write(f'  Multiple Candidates:  {totals["multiple_candidates"]:>8,}  ({(totals["multiple_candidates"]/total_count)*100:>5.1f}%)')
        self.stdout.write(f'  Uncertain:            {totals["uncertain"]:>8,}  ({(totals["uncertain"]/total_count)*100:>5.1f}%)')
        
        self.stdout.write(f'\n🔍 DETECTION METHODS:')
        self.stdout.write(f'  DNS Detections:       {totals["dns_detections"]:>8,}  ({(totals["dns_detections"]/total_count)*100:>5.1f}%)')
        self.stdout.write(f'  ASN Fallback Used:    {totals["asn_fallback"]:>8,}  ({(totals["asn_fallback"]/total_count)*100:>5.1f}%)')
        
        if not summary_only:
            # Display detailed statistics per period
            self.stdout.write(self.style.SUCCESS('\n\n📋 DETAILED STATISTICS (5-minute periods)'))
            self.stdout.write(self.style.SUCCESS('-' * 80))
            
            # Group by model if showing all models
            if not model_name:
                models = stats_query.values_list('model_configuration__name', flat=True).distinct()
                for model in models:
                    model_stats = stats.filter(model_configuration__name=model)
                    self.stdout.write(f'\n🔹 Model: {model}')
                    self._display_period_stats(model_stats)
            else:
                self._display_period_stats(stats)
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write('✅ Statistics displayed successfully')
        self.stdout.write('\nTo setup automatic stats collection, run: python manage.py setup_classification_stats')
    
    def _display_period_stats(self, stats):
        """Display statistics for each period"""
        for stat in stats[:20]:  # Show last 20 periods
            self.stdout.write(f'\n  Period: {stat.period_start.strftime("%Y-%m-%d %H:%M")} - {stat.period_end.strftime("%H:%M")}')
            self.stdout.write(f'    Total: {stat.total_classifications:,} classifications')
            self.stdout.write(f'    High Confidence: {stat.high_confidence_count:,} ({stat.high_confidence_percentage:.1f}%)')
            self.stdout.write(f'    Low Confidence: {stat.low_confidence_count:,} ({stat.low_confidence_percentage:.1f}%)')
            self.stdout.write(f'    Multiple Candidates: {stat.multiple_candidates_count:,} ({stat.multiple_candidates_percentage:.1f}%)')
            self.stdout.write(f'    Avg Prediction Time: {stat.avg_prediction_time_ms:.2f} ms')
        
        if stats.count() > 20:
            self.stdout.write(f'\n  ... and {stats.count() - 20} more periods')

