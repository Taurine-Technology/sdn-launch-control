#!/usr/bin/env python
"""Quick script to check Redis classification stats"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'control_center.settings')
django.setup()

from classifier.state_manager import state_manager

stats = state_manager.get_classification_stats()
print('=' * 60)
print('📊 CURRENT STATS IN REDIS (Shared Across All Processes)')
print('=' * 60)
print(f'Total Classifications:     {stats.get("total", 0):>6,}')
print(f'High Confidence:           {stats.get("high_confidence", 0):>6,}')
print(f'Low Confidence:            {stats.get("low_confidence", 0):>6,}')
print(f'Multiple Candidates:       {stats.get("multiple_candidates", 0):>6,}')
print(f'Uncertain:                 {stats.get("uncertain", 0):>6,}')
print(f'DNS Detections:            {stats.get("dns_detections", 0):>6,}')
print(f'ASN Fallback:              {stats.get("asn_fallback", 0):>6,}')
print(f'Prediction Times Tracked:  {len(stats.get("prediction_times", [])):>6,}')
print('=' * 60)


