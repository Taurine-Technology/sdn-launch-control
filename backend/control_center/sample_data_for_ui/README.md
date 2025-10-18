# Sample Data for UI Development

This directory contains sample data exported from a running SDN Launch Control instance.

## Files Included

1. **classification_stats.json** - Classification statistics (5-minute periods)
2. **models.json** - ML model configurations
3. **categories.json** - Traffic categories (YouTube, Facebook, etc.)
4. **odl_meters.json** - Sample traffic control policies
5. **network_devices.json** - Sample network devices/clients

## How to Load Data

### Option 1: Load All Data at Once

```bash
# From backend/control_center directory
python manage.py loaddata sample_data_for_ui/*.json
```

### Option 2: Load Specific Files

```bash
# Load just classification stats
python manage.py loaddata sample_data_for_ui/classification_stats.json

# Load models and categories
python manage.py loaddata sample_data_for_ui/models.json
python manage.py loaddata sample_data_for_ui/categories.json
```

### Option 3: With Docker

```bash
# Load all data
docker exec launch-control-api-dev python manage.py loaddata sample_data_for_ui/*.json

# Or specific files
docker exec launch-control-api-dev python manage.py loaddata sample_data_for_ui/classification_stats.json
```

## Prerequisites

Before loading this data, ensure:

1. ✅ Database is migrated: `python manage.py migrate`
2. ✅ Models are initialized: `python manage.py initialize_models`
3. ✅ Redis is running (for DNS/ASN lookups)

## What You'll Have Access To

### Classification Statistics
- Multiple periods of classification data
- Confidence breakdowns (high, low, uncertain, multiple)
- DNS and ASN detection stats
- Linked to specific models

### Models
- Pre-configured ML models
- Categories for each model
- Confidence thresholds

### Categories
- Standard categories: Unknown, DNS, Apple
- App-specific categories: YouTube, Facebook, TikTok, etc.
- Each with unique cookies for flow matching

### Sample Devices
- Network devices with MAC addresses
- IP addresses
- Device types

## API Endpoints You Can Test

With this data loaded, you can test:

```bash
# Get classification stats
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/classification-stats/

# Get models
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/models/

# Get categories
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/categories/

# Get ODL meters
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/odl/meters/
```

## Notes

- All data is anonymized/sample data
- Timestamps are from the export time
- Foreign key relationships are preserved
- Data is safe to delete and reload

## Cleaning Up

To remove this sample data and start fresh:

```bash
# Clear classification stats
python manage.py shell -c "from classifier.models import ClassificationStats; ClassificationStats.objects.all().delete()"

# Clear all sample data (be careful!)
python manage.py flush --no-input
```

## Support

See full API documentation in:
- `docs/API_DOCS_FOR_UI.md` - UI developer guide
- `docs/API_CLASSIFICATION_STATS.md` - Complete API reference
- `docs/README.md` - Management commands reference

