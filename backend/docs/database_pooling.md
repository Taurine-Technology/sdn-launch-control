# Database Connection Pooling Setup

This document describes the database connection pooling configuration for the SDN Launch Control backend using TimescaleDB.

## Overview

The application uses `django-db-connection-pool` to manage database connections efficiently and prevent "too many open connections" errors. This is particularly important for time-series data applications with high write/read loads.

**Note**: This implementation uses `dj_db_conn_pool.backends.postgresql` engine with proper `POOL_OPTIONS` configuration.

**Important**: Celery workers use a separate database configuration without connection pooling to avoid multiprocessing issues. The `CELERY_WORKER_RUNNING` environment variable is used to detect Celery workers and apply the appropriate configuration.

## Configuration

### Environment Variables

Configure the following environment variables in your `.env` file:

```bash
# Database Configuration
DB_HOST=pgdatabase
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASS=postgres

# Database Connection Pool Settings (Production)
DB_MAX_CONNS=20          # Pool size (maximum connections in the pool)
DB_MAX_OVERFLOW=10       # Additional connections when pool is full
DB_POOL_RECYCLE=3600     # Recycle connections after 1 hour

# Database Connection Pool Settings (Development)
DB_MAX_CONNS_DEV=10      # Smaller pool size for development
DB_MAX_OVERFLOW_DEV=5    # Smaller overflow for development

# Celery Configuration
CELERY_WORKER_RUNNING=1  # Set for Celery workers to use standard DB backend
```

### Pool Settings Explained

- **POOL_SIZE**: Maximum number of connections in the pool. Set based on your application's concurrent load.
- **MAX_OVERFLOW**: Additional connections allowed when the pool is full. Total connections = POOL_SIZE + MAX_OVERFLOW.
- **RECYCLE**: How often to recycle connections to prevent stale connections (in seconds).

## Celery Configuration

### Separate Database Configuration for Celery Workers

Celery workers use a separate database configuration to avoid connection pooling issues in multiprocessing environments:

- **Web Server**: Uses `dj_db_conn_pool.backends.postgresql` with connection pooling
- **Celery Workers**: Uses `django.db.backends.postgresql` (standard backend)

The `CELERY_WORKER_RUNNING` environment variable is automatically set in Celery containers to detect workers and apply the correct configuration.

### Testing Celery Database Connectivity

```bash
# Test Celery database configuration
docker-compose -f docker-compose.dev.yml exec celery python test_celery_db.py

# Check Celery worker logs
docker-compose -f docker-compose.dev.yml logs celery

# Check Celery beat logs
docker-compose -f docker-compose.dev.yml logs celery_beat
```

## Monitoring and Debugging

### Management Commands

Check connection pool status:

```bash
python manage.py db_pool_status
python manage.py db_pool_status --detailed
```

### Logging

The application includes middleware that logs:

- Slow database operations (>1 second)
- Connection usage patterns
- Connection errors

### Utility Functions

Use the utility functions in `utils/db_utils.py`:

```python
from utils.db_utils import (
    db_connection_monitor,
    get_connection_info,
    check_connection_health,
    log_connection_pool_stats
)

# Monitor a database operation
with db_connection_monitor("my_operation"):
    # Your database operations here
    pass

# Check connection health
if check_connection_health():
    print("Database connection is healthy")

# Log pool statistics
stats = log_connection_pool_stats()
```

## Best Practices

### 1. Use Connection Monitoring

Wrap database operations in the monitoring context:

```python
from utils.db_utils import db_connection_monitor

def my_view(request):
    with db_connection_monitor("user_data_query"):
        users = User.objects.filter(is_active=True)
    return JsonResponse({'users': list(users.values())})
```

### 2. Manage Transactions Properly

Use the managed transaction context for complex operations:

```python
from utils.db_utils import managed_transaction

def bulk_operation():
    with managed_transaction():
        # Your bulk operations here
        pass
```

### 3. Optimize TimescaleDB Queries

Apply TimescaleDB-specific optimizations:

```python
from utils.db_utils import optimize_timescaledb_queries

# Call this during application startup
optimize_timescaledb_queries()
```

## Troubleshooting

### Common Issues

1. **"Too many open connections"**

   - Increase `DB_MAX_CONNS`
   - Check for connection leaks in your code
   - Monitor with `db_pool_status` command

2. **Slow queries**

   - Use `db_connection_monitor` to identify slow operations
   - Check for long-running transactions
   - Optimize TimescaleDB settings

3. **Connection timeouts**
   - Increase `DB_POOL_TIMEOUT`
   - Check database server load
   - Verify network connectivity

### Performance Tuning

1. **For high write loads**:

   - Increase `DB_MAX_CONNS` to 30-50
   - Set `DB_MIN_CONNS` to 10-15
   - Use bulk operations where possible

2. **For high read loads**:

   - Consider read replicas
   - Optimize query patterns
   - Use appropriate indexes

3. **For mixed workloads**:
   - Monitor connection usage patterns
   - Adjust pool size based on actual usage
   - Use connection monitoring to identify bottlenecks

## TimescaleDB Specific Considerations

### Chunk Management

TimescaleDB uses chunks for time-series data. Ensure proper chunk management:

```sql
-- Check chunk information
SELECT * FROM timescaledb_information.chunks;

-- Compress old chunks
SELECT compress_chunk(chunk_name) FROM timescaledb_information.chunks
WHERE chunk_name < '2024-01-01'::text;
```

### Retention Policies

Set up retention policies for automatic data cleanup:

```sql
-- Example: Keep data for 1 year
SELECT add_retention_policy('your_hypertable', INTERVAL '1 year');
```

### Continuous Aggregates

Use continuous aggregates for improved query performance:

```sql
-- Create continuous aggregate
CREATE MATERIALIZED VIEW hourly_stats
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour', timestamp) AS bucket,
       avg(value) as avg_value,
       max(value) as max_value
FROM your_hypertable
GROUP BY bucket;
```

## Monitoring Dashboard

Consider setting up monitoring for:

- Connection pool utilization
- Query performance
- TimescaleDB chunk statistics
- Database server metrics

This will help you proactively identify and resolve connection issues.
