# Model Management System

This document describes the model management system that allows dynamic loading, switching, and configuration of machine learning models for traffic classification.

## Overview

The model management system provides:

- **JSON-based configuration** for model definitions
- **Dynamic model loading/unloading** without service restart
- **Automatic category management** with cookie generation
- **Model validation** and health checks
- **API endpoints** for model management
- **Integration with ODL meter system** for policy application

## Architecture

### 1. Configuration System

#### JSON Configuration File

Models are defined in `classifier/models_config.json`:

```json
{
  "models": {
    "complex_cnn_16_04_2025": {
      "name": "Complex CNN (16-04-2025)",
      "model_path": "classifier/ml_models/complex_cnn_16-04-2025.h5",
      "model_type": "keras_h5",
      "num_categories": 22,
      "description": "Complex CNN model trained on 22 categories",
      "version": "16-04-2025",
      "confidence_threshold": 0.7,
      "is_active": true,
      "categories": [
        "ADS_Analytic_Track",
        "AmazonAWS",
        "BitTorrent",
        "Facebook",
        "FbookReelStory",
        "GMail",
        "Google",
        "GoogleServices",
        "HTTP",
        "HuaweiCloud",
        "Instagram",
        "Messenger",
        "Microsoft",
        "NetFlix",
        "QUIC",
        "TikTok",
        "TLS",
        "Unknown",
        "WhatsApp",
        "WhatsAppFiles",
        "WindowsUpdate",
        "YouTube"
      ]
    }
  },
  "metadata": {
    "version": "1.0",
    "description": "Model configurations for traffic classification",
    "last_updated": "2025-01-19"
  }
}
```

#### Configuration Fields

| Field                  | Type    | Description                                         |
| ---------------------- | ------- | --------------------------------------------------- |
| `name`                 | string  | Human-readable model name                           |
| `model_path`           | string  | Relative path to model file                         |
| `model_type`           | string  | Model format (`keras_h5`, `tensorflow_saved_model`) |
| `num_categories`       | integer | Number of classification categories                 |
| `description`          | string  | Model description                                   |
| `version`              | string  | Model version identifier                            |
| `confidence_threshold` | float   | Minimum confidence for classification (0.0-1.0)     |
| `is_active`            | boolean | Whether this model should be active by default      |
| `categories`           | array   | List of category names the model can classify       |

### 2. Model Manager

#### Core Components

**ModelConfig Dataclass**:

```python
@dataclass
class ModelConfig:
    name: str
    model_path: str
    model_type: str
    num_categories: int
    categories: List[str]
    description: str = ""
    version: str = "1.0"
    confidence_threshold: float = 0.7
    is_active: bool = False
```

**ModelManager Class**:

- Loads configurations from JSON file
- Manages model lifecycle (load/unload)
- Handles active model switching
- Validates categories against database
- Provides prediction interface

#### Key Methods

```python
# Load model into memory
model_manager.load_model("model_name")

# Unload model from memory
model_manager.unload_model("model_name")

# Set active model
model_manager.set_active_model("model_name")

# Get active model info
active_model = model_manager.get_active_model()

# Get categories from model
categories = model_manager.get_active_model_categories()

# Make prediction
prediction, time = model_manager.predict_flow(packet_data, client_ip)
```

### 3. Category Management

#### Automatic Category Synchronization

The system automatically manages categories to ensure they match the active model:

1. **Category Creation**: Categories are created with deterministic cookies
2. **Cookie Generation**: SHA1 hash of category name generates 64-bit cookie
3. **Database Validation**: System validates categories exist before model activation
4. **ODL Integration**: Cookies are used for OpenDaylight meter policies

## Management Commands

### 1. Populate Categories from Model

Populates database categories based on active model configuration:

```bash
# Use active model
python manage.py populate_categories_from_model

# Use specific model
python manage.py populate_categories_from_model --model-name complex_cnn_16_04_2025

# Force update existing categories
python manage.py populate_categories_from_model --force-update
```

**Features**:

- Creates missing categories automatically
- Generates cookies for new categories
- Updates existing categories if needed
- Provides detailed progress reporting

### 2. Validate Model Categories

Validates that database categories match model configuration:

```bash
# Validate against active model
python manage.py validate_model_categories

# Validate against specific model
python manage.py validate_model_categories --model-name attention_random_23_8400

# Auto-fix missing categories
python manage.py validate_model_categories --fix-missing
```

**Features**:

- Compares expected vs. actual categories
- Identifies missing and extra categories
- Checks for categories without cookies
- Provides detailed validation report

### 3. Test Model Manager

Command-line interface for testing model management:

```bash
# List all models
python manage.py test_model_manager --action list

# Load specific model
python manage.py test_model_manager --action load --model-name complex_cnn_16_04_2025

# Set active model
python manage.py test_model_manager --action set-active --model-name attention_random_23_8400

# Test prediction
python manage.py test_model_manager --action predict
```

## API Endpoints

### 1. Model Management API

**List Models**:

```http
GET /api/models/
Response: {
    "status": "success",
    "models": [
        {
            "name": "complex_cnn_16_04_2025",
            "display_name": "Complex CNN (16-04-2025)",
            "model_type": "keras_h5",
            "num_categories": 22,
            "description": "Complex CNN model trained on 22 categories",
            "version": "16-04-2025",
            "confidence_threshold": 0.7,
            "is_active": true,
            "is_loaded": true
        }
    ],
    "active_model": "complex_cnn_16_04_2025"
}
```

**Set Active Model**:

```http
POST /api/models/
Body: {"model_name": "attention_random_23_8400"}
Response: {
    "status": "success",
    "message": "Active model set to: attention_random_23_8400",
    "active_model": "attention_random_23_8400"
}
```

### 2. Model Loading API

**Load Model**:

```http
POST /api/models/load/
Body: {"model_name": "complex_cnn_16_04_2025"}
Response: {
    "status": "success",
    "message": "Model loaded: complex_cnn_16_04_2025"
}
```

**Unload Model**:

```http
DELETE /api/models/load/
Body: {"model_name": "complex_cnn_16_04_2025"}
Response: {
    "status": "success",
    "message": "Model unloaded: complex_cnn_16_04_2025"
}
```

## Integration with ODL System

### 1. Category Cookie Usage

Categories with their cookies are used in the ODL meter system:

```python
# In CreateOpenDaylightMeterView
category_obj = Category.objects.get(name=application_name)
category_cookie_to_use = category_obj.category_cookie

# Apply meter with category cookie
odl_flow_manager = OdlMeterFlowRule(
    # ... other parameters ...
    category_obj_cookie=category_cookie_to_use
)
```

### 2. Automatic Validation

When switching models, the system automatically validates categories:

```python
def set_active_model(self, model_name: str) -> bool:
    # ... load model ...

    # Validate categories exist in database
    self._validate_model_categories(model_name)

    return True
```

## Workflow Examples

### 1. Adding a New Model

1. **Add model file** to `classifier/ml_models/`
2. **Update JSON configuration**:
   ```json
   "new_model_v2": {
     "name": "New Model v2",
     "model_path": "classifier/ml_models/new_model_v2.h5",
     "model_type": "keras_h5",
     "num_categories": 25,
     "categories": ["Category1", "Category2", ...],
     "is_active": false
   }
   ```
3. **Populate categories**:
   ```bash
   python manage.py populate_categories_from_model --model-name new_model_v2
   ```
4. **Activate model**:
   ```bash
   python manage.py test_model_manager --action set-active --model-name new_model_v2
   ```

### 2. Updating Model Categories

1. **Update JSON configuration** with new categories
2. **Validate changes**:
   ```bash
   python manage.py validate_model_categories --model-name model_name
   ```
3. **Apply changes**:
   ```bash
   python manage.py populate_categories_from_model --model-name model_name --force-update
   ```

### 3. Production Deployment

1. **Validate configuration**:
   ```bash
   python manage.py validate_model_categories --fix-missing
   ```
2. **Test model switching**:
   ```bash
   python manage.py test_model_manager --action list
   python manage.py test_model_manager --action predict
   ```
3. **Monitor logs** for category validation messages

## Error Handling

### 1. Missing Categories

When switching to a model with missing categories:

```
[WARNING] Missing categories for model 'new_model': ['NewCategory1', 'NewCategory2']
[WARNING] Run 'python manage.py populate_categories_from_model' to create missing categories
```

### 2. Model Loading Errors

```python
try:
    model_manager.load_model("model_name")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    # Handle gracefully
```

### 3. Category Cookie Issues

```bash
# Check for categories without cookies
python manage.py validate_model_categories

# Fix missing cookies
python manage.py populate_categories_from_model --force-update
```

## Performance Considerations

### 1. Memory Management

- Models are loaded on-demand
- Unused models can be unloaded to free memory
- Connection pooling for Redis lookups
- Batch processing for category operations

### 2. Model Switching

- Switching models is fast (<1 second)
- Categories are validated automatically
- No service restart required
- Graceful fallback to previous model

### 3. Prediction Performance

- Sub-millisecond prediction times
- Automatic ASN lookup for low confidence
- Efficient model loading and caching
- Optimized for high-throughput APIs

## Monitoring and Logging

### 1. Model Lifecycle Events

```python
logger.info(f"Successfully loaded model: {model_name}")
logger.info(f"Active model set to: {model_name}")
logger.warning(f"Missing categories for model '{model_name}': {missing_categories}")
```

### 2. Prediction Logging

```python
logger.info("Top 5 Classification Percentages:")
logger.info(f"1. {class_name}: {percentage:.2f}%")
logger.info(f"ASN Lookup Results (Low Confidence Classification):")
logger.info(f"Client IP: {client_ip_address}")
logger.info(f"ASN: {asn_info['asn']}")
```

### 3. Health Checks

```bash
# Check model status
python manage.py test_model_manager --action list

# Validate categories
python manage.py validate_model_categories

# Test prediction
python manage.py test_model_manager --action predict
```

## Best Practices

### 1. Model Configuration

- Keep JSON configuration in version control
- Use descriptive model names and versions
- Document category changes
- Test configurations before deployment

### 2. Category Management

- Always validate categories after model changes
- Use consistent category naming conventions
- Monitor for missing cookies
- Regular validation in production

### 3. Model Deployment

- Test model switching in staging
- Validate categories before production
- Monitor memory usage
- Have fallback models ready

### 4. Error Handling

- Implement graceful degradation
- Log all model operations
- Monitor for prediction errors
- Have recovery procedures ready

## Troubleshooting

### Common Issues

1. **Model not found**: Check JSON configuration and file paths
2. **Missing categories**: Run populate command with correct model
3. **Memory issues**: Unload unused models
4. **Cookie problems**: Force update categories
5. **Prediction errors**: Check model file integrity

### Debug Commands

```bash
# Check model configuration
python manage.py test_model_manager --action list

# Validate categories
python manage.py validate_model_categories --fix-missing

# Test prediction
python manage.py test_model_manager --action predict

# Check logs
docker compose logs django | grep model_manager
```
