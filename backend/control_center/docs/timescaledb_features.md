# TimescaleDB Features & Optimizations

## Overview

This document outlines the TimescaleDB features and optimizations implemented in the SDN Launch Control system for efficient time-series data management.

## 🚀 Features Implemented

### 1. Database Connection Pooling

**Purpose**: Resolves "too many open connections" issues with TimescaleDB

**Configuration**:

- **Development**: Pool Size: 10, Max Overflow: 5, Recycle: 3600s
- **Production**: Pool Size: 20, Max Overflow: 10, Recycle: 3600s
- **Celery Workers**: Use standard PostgreSQL backend (no pooling) for multiprocessing compatibility

**Files**:

- `control_center/database.py` - Centralized database configuration
- `control_center/connection_pool_setup.py` - Pool initialization
- `control_center/general/middleware.py` - Connection monitoring
- `docker-compose.yml` & `docker-compose.dev.yml` - Environment variables

### 2. Hypertables

**Purpose**: Automatic time-based partitioning for efficient querying

**Tables**:

- `network_data_flow` - Network flow data
- `network_data_flowstat` - Network flow statistics

**Benefits**:

- Automatic partitioning by time
- Faster queries on time ranges
- Better maintenance operations

### 3. Continuous Aggregates

**Purpose**: Pre-aggregated materialized views for fast analytics

**Views**:

- `network_data_flow_1min` - 1-minute aggregated flow data
- `network_data_flow_by_mac_1min` - 1-minute aggregated flow data by MAC address
- `network_data_flowstat_usage_1min` - 1-minute aggregated usage calculations

**Features**:

- Automatic refresh policies (every 1 minute)
- Compression enabled
- Optimized for day/week queries

### 4. Compression Policies

**Purpose**: Reduce storage space while maintaining query performance

**Current Settings**:

- **Main Tables**: Compress after 24 hours (optimized for day/week queries)
- **Continuous Aggregates**: Compress after 7 days
- **Compression Ratio**: 70-90% storage reduction

**Configuration**:

```sql
-- FlowStat compression
timescaledb.compress_segmentby = 'classification, mac_address, protocol'
timescaledb.compress_orderby = 'timestamp DESC'

-- Flow compression
timescaledb.compress_segmentby = 'classification, src_mac, dst_mac'
timescaledb.compress_orderby = 'timestamp DESC'
```

### 5. Retention Policies

**Purpose**: Automatically delete old data to manage storage

**Settings**:

- **Retention Period**: 90 days
- **Automatic Cleanup**: Old chunks are automatically dropped
- **Storage Management**: Prevents unlimited growth

### 6. Database Indexes

**Purpose**: Optimize query performance for common access patterns

**Indexes Added**:

```sql
-- FlowStat indexes
CREATE INDEX ON network_data_flowstat (mac_address, timestamp);
CREATE INDEX ON network_data_flowstat (protocol, timestamp);
```

### 7. API Optimizations

**Purpose**: Leverage continuous aggregates for faster API responses

**Optimized Endpoints**:

- `data_used_per_classification` - Uses continuous aggregates
- `data_used_per_user` - Uses continuous aggregates
- `data_used_per_user_per_classification` - Uses continuous aggregates

**Performance**: 10-100x faster for day/week queries

### 8. Bulk Insert Optimizations

**Purpose**: Efficient batch processing for high-volume data insertion

**Optimizations**:

- Increased `batch_size` from 1000 to 5000
- Pre-allocated lists for memory efficiency
- Optimized for TimescaleDB chunk management

## 📊 Monitoring & Management

### Management Commands

#### Database Pool Status

```bash
python manage.py db_pool_status
```

Shows:

- Connection pool configuration
- Active connections
- Pool statistics
- Long-running queries

#### TimescaleDB Status

```bash
python manage.py timescaledb_status
python manage.py timescaledb_status --detailed
python manage.py timescaledb_status --optimize
```

Shows:

- Hypertable information
- Continuous aggregate status
- Compression statistics
- Chunk distribution
- Query performance metrics

### Utility Functions

#### Database Utilities (`utils/db_utils.py`)

- `db_connection_monitor()` - Performance monitoring
- `get_connection_info()` - Connection status
- `check_connection_health()` - Health checks
- `optimize_timescaledb_queries()` - Query optimization

#### TimescaleDB Utilities (`network_data/timescaledb_utils.py`)

- `get_hypertable_info()` - Hypertable details
- `get_continuous_aggregate_info()` - Aggregate status
- `get_compression_stats()` - Compression metrics
- `optimize_timescaledb_settings()` - Performance tuning

## 🔧 Configuration

### Environment Variables

```bash
# Database Connection
DB_HOST=postgres
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_user
DB_PASS=your_password

# Connection Pooling (Production)
DB_MAX_CONNS=20
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=3600

# Connection Pooling (Development)
DB_MAX_CONNS_DEV=10
DB_MAX_OVERFLOW_DEV=5

# Celery Workers
CELERY_WORKER_RUNNING=1
```

### Docker Configuration

**Django Service**:

- Uses connection pooling
- Optimized for web requests

**Celery Services**:

- Uses standard PostgreSQL backend
- Compatible with multiprocessing
- No connection pooling conflicts

## 📈 Performance Benefits

### Query Performance

- **Day queries**: 10-50x faster with continuous aggregates
- **Week queries**: 50-100x faster with continuous aggregates
- **Real-time queries**: Fast with uncompressed recent data

### Storage Efficiency

- **Compression**: 70-90% storage reduction
- **Retention**: Automatic cleanup of old data
- **Partitioning**: Efficient maintenance operations

### Scalability

- **Connection pooling**: Handles high concurrent load
- **Bulk operations**: Efficient batch processing
- **Automatic maintenance**: Self-managing system

## 🚨 Troubleshooting

### Common Issues

#### Connection Pool Exhausted

```bash
# Check pool status
python manage.py db_pool_status

# Increase pool size in settings
DB_MAX_CONNS=30
DB_MAX_OVERFLOW=15
```

#### Slow Queries

```bash
# Check TimescaleDB status
python manage.py timescaledb_status

# Optimize settings
python manage.py timescaledb_status --optimize
```

#### Migration Errors

```bash
# Check for existing policies
docker-compose exec postgres psql -U your_user -d your_db -c "
SELECT * FROM timescaledb_information.jobs WHERE proc_name LIKE '%policy%';
"
```

### Performance Tuning

#### For High-Volume Data

- Increase `batch_size` in tasks
- Adjust compression intervals
- Monitor chunk sizes

#### For Fast Queries

- Use continuous aggregates
- Optimize indexes
- Adjust compression policies

## 🔄 Maintenance

### Regular Tasks

1. **Monitor pool status**: Weekly
2. **Check compression stats**: Monthly
3. **Review retention policies**: Quarterly
4. **Optimize settings**: As needed

### Backup Considerations

- TimescaleDB backups include all features
- Continuous aggregates are automatically included
- Compression doesn't affect backup size
