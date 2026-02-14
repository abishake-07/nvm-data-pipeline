# System Architecture

## Overview

The NVM Data Pipeline is a production-grade system for ingesting, validating, and analyzing high-frequency vibration data from motor test benches. It follows a medallion architecture (Bronze → Silver) with near-real-time processing capabilities.

## System Context

```
┌─────────────────┐
│  Test Bench     │
│  Sensors        │
│  - 3× Accel     │──┐
│  - 1× RPM       │  │
└─────────────────┘  │
                     │  25.6 kHz data
                     ↓
┌─────────────────────────────────────────────────────────┐
│                 NVM Data Pipeline                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │Generator │→ │Validation│→ │ Features │→ │Power BI │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│       ↓              ↓              ↓            ↑       │
│  ┌─────────────────────────────────────────────────┐    │
│  │         MySQL (Bronze + Silver)                 │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Architecture Principles

1. **Validate Early**: Reject bad data at ingestion, not analysis
2. **Medallion Architecture**: Bronze (raw) → Silver (curated)
3. **Idempotency**: Reprocessing same data yields same results
4. **Fault Tolerance**: Quarantine bad data, don't crash pipeline
5. **Observability**: Track data quality and pipeline health
6. **Scalability**: Design for sharding by test_id and time partitioning

## Components

### 1. Synthetic Data Generator (Week 2)

**Purpose**: Simulate realistic test bench sessions for development/testing

**Responsibilities**:
- Generate time-series vibration data with realistic physics
- Create phase transitions (idle → run-up → steady → run-down)
- Inject controlled anomalies for fault detection testing
- Output raw Parquet files + pre-computed feature files

**Key Features**:
- **Physics-based**: RPM harmonics, bearing frequencies
- **Anomaly injection**: Spikes, dropouts, stuck sensors
- **Configurable**: Duration, phases, noise levels

**Output Files**:
```
data/landing/{test_id}_{timestamp}.parquet  (raw samples)
data/processed/{test_id}_features.json      (1-sec windows)
```

### 2. MySQL Database (Week 3)

#### Bronze Layer (Raw/Landing)

**Purpose**: Track what data arrived, light metadata storage

**Tables**:
- `raw_file_registry`: File metadata, sizes, hashes, validation status
- `raw_sample_preview` (optional): Downsampled view for quick checks

**Characteristics**:
- Minimal transformation
- Keep quarantine records
- Audit trail of all ingestion attempts

#### Silver Layer (Curated/Analytics)

**Purpose**: Clean, validated, feature-enriched data for analytics

**Tables**:
- `window_features`: 1-second aggregated features
  - Time-domain: RMS, peak, crest factor, kurtosis
  - Frequency-domain: Band energies, dominant freq
  - Quality flags: Anomaly indicators, data quality scores
- `session_metadata`: Test session information
- `phase_transitions`: Phase change events

**Characteristics**:
- Schema enforced
- Business logic applied
- Optimized for queries (indexed, partitioned)

### 3. Ingestion Service (Week 4)

**Purpose**: Watch landing folder, validate, load to database

**Architecture Pattern**: Event-driven file watcher or scheduled batch

**Process Flow**:
```
1. Detect new file in data/landing/
2. Read metadata + sample data
3. Run validation rules (quality_rules.md)
4. If PASS:
   - Write to raw_file_registry
   - Extract features → window_features
   - Move to data/processed/
5. If FAIL:
   - Write to quarantine_log
   - Move to data/quarantine/
   - Alert if quarantine rate > threshold
```

**Key Features**:
- **Idempotency**: Use (test_id, window_start) as unique key
- **Partial failure handling**: Don't crash on one bad file
- **Backpressure**: Rate limit if database is slow

### 4. Feature Computation (Week 5)

**Purpose**: Transform raw samples into analytics-ready features

**Processing Window**: 1-second (25,600 samples)

**Features Computed**:

**Time Domain** (per axis):
```python
- RMS: √(Σ(x²)/n)
- Peak: max(|x|)
- Crest Factor: peak / RMS
- Kurtosis: measure of impulsiveness
```

**Frequency Domain** (via FFT):
```python
- Band Energies (6 bands):
  * 0-500 Hz      (low frequency)
  * 500-2000 Hz   (gear mesh)
  * 2-5 kHz       (bearing tones)
  * 5-8 kHz       (high frequency)
  * 8-10 kHz      (ultrasonic)
  * 10+ kHz       (aliasing check)
- Dominant Frequency: argmax(FFT)
- Spectral Entropy: disorder in frequency domain
```

**Quality Indicators**:
```python
- is_clipped: peak ≥ 99% of range
- is_stuck: σ < threshold
- has_gaps: missing samples > threshold
- snr_db: signal-to-noise ratio
```

**Why 1-second windows?**
- Balance resolution vs storage
- Aligns with human monitoring cadence
- Captures at least 25 rotations at 1500 RPM

### 5. Monitoring & Observability (Week 6)

**Purpose**: Track pipeline and data health

**Monitoring Tables**:

**pipeline_metrics**:
```sql
- timestamp (per minute)
- files_ingested
- files_quarantined
- rows_written
- ingest_lag_seconds (time from file creation to DB insert)
- error_count
- processing_rate_MB_per_sec
```

**data_quality_metrics** (per session):
```sql
- test_id
- session_start
- total_windows
- missing_windows
- anomaly_windows
- quality_score (0-100)
- flagged_rules (JSON array)
```

**Alerts**:
- Quarantine rate > 5% (email/Slack)
- Ingest lag > 5 minutes
- Error rate spike
- Disk space < 20%

### 6. Power BI Dashboards (Week 7)

**Connection**: DirectQuery or Import mode to MySQL

**Dashboards**:

**1. Session Overview**
- Timeline: phase transitions with RPM overlay
- KPI cards: duration, avg RMS, peak acceleration
- Phase breakdown (pie chart)

**2. Variant Comparison**
- Box plots: RMS distribution by motor_variant
- Scatter: RPM vs vibration level
- Statistical comparison table

**3. Anomaly Board**
- Top 10 anomaly sessions (ranked by anomaly count)
- Drill-through: detailed time-series for selected session
- Anomaly type breakdown

**4. Pipeline Health**
- Ingest lag trend (line chart)
- Quarantine rate (gauge)
- Daily volumes (bar chart)
- Error log table

**Near-Real-Time**:
- Use Power BI streaming dataset for "live" KPI tile
- Refresh DirectQuery every 15-60 seconds

## Data Flow

### Ingestion Flow

```
┌─────────────┐
│  Generator  │
└──────┬──────┘
       │ Creates .parquet
       ↓
┌─────────────┐
│data/landing/│
└──────┬──────┘
       │ Watcher detects
       ↓
┌─────────────────────┐
│ Validation Service  │
│ - Schema check      │
│ - Range check       │
│ - Timestamp check   │
└──────┬──────┬───────┘
       │      │
    PASS    FAIL
       │      │
       ↓      ↓
   ┌─────┐ ┌───────────┐
   │MySQL│ │quarantine/│
   └─────┘ └───────────┘
```

### Feature Flow

```
┌─────────────────┐
│ Raw Samples     │
│ (25.6k samples) │
└────────┬────────┘
         │
         ↓
┌─────────────────────┐
│ Windowing           │
│ (1-second chunks)   │
└────────┬────────────┘
         │
         ↓
┌─────────────────────┐
│ Feature Extraction  │
│ - Time domain       │
│ - FFT → freq domain │
└────────┬────────────┘
         │
         ↓
┌─────────────────────┐
│ MySQL Silver Layer  │
│ window_features     │
└─────────────────────┘
         │
         ↓
┌─────────────────────┐
│    Power BI         │
└─────────────────────┘
```

## Technology Choices

### Why Python?
- Rich scientific libraries: NumPy, SciPy, Pandas
- Fast prototyping for signal processing
- Popular in data engineering

### Why MySQL?
- Proven relational database
- Good for time-series with proper indexing
- Built-in replication for scaling
- Widely supported by BI tools

**Alternatives considered**:
- InfluxDB (time-series native, but less familiar)
- PostgreSQL (TimescaleDB extension viable)

### Why Parquet?
- Columnar format (efficient for analytics)
- Built-in compression
- Schema evolution support
- Native support in Pandas/PyArrow

### Why Power BI?
- Industry-standard BI tool
- DirectQuery for near-real-time
- Streaming datasets available
- Good for demo portfolio

## Scalability Considerations

### Current Design (Single Instance)
- Handle: ~10 benches, ~50 sessions/day
- Storage: ~500 GB/year (with compression)
- Queries: <2 sec for aggregated views

### Scale-Out Strategy

**Horizontal Sharding** (when > 50 benches):
```
- Shard by bench_id or test_id hash
- Separate MySQL instances per shard
- Aggregate layer for cross-shard queries
```

**Time Partitioning**:
```sql
-- MySQL 8.0+ partitioning
PARTITION BY RANGE (UNIX_TIMESTAMP(window_start)) (
    PARTITION p_2026_02 VALUES LESS THAN (UNIX_TIMESTAMP('2026-03-01')),
    PARTITION p_2026_03 VALUES LESS THAN (UNIX_TIMESTAMP('2026-04-01')),
    ...
);
```

**Performance Optimizations**:
- Index on (test_id, window_start) for time-range queries
- Materialized views for common aggregations
- Read replicas for BI queries (isolate from writes)
- SSD storage for database

### Alternative Architecture (Cloud-Native)

For 100+ benches:
```
AWS IoT Core → Kinesis → Lambda → S3 (raw) + RDS (features)
                                 ↓
                            Athena/Redshift (analytics)
                                 ↓
                             QuickSight
```

## Security Considerations

- **Authentication**: No public access, internal network only
- **Encryption**: TLS for MySQL connections
- **PII**: No personally identifiable information in data
- **Access Control**: Read-only accounts for Power BI
- **Audit Log**: Track all data access via `audit_log` table

## Disaster Recovery

- **Backup Strategy**: Daily full + hourly incremental
- **Retention**: 30 days hot, 1 year cold storage
- **RTO**: 4 hours (restore from backup)
- **RPO**: 1 hour (max data loss)

## Development Roadmap

| Week | Milestone | Deliverables |
|------|-----------|-------------|
| 1 | Architecture + Contracts | docs/, data contracts, quality rules |
| 2 | Synthetic Generator | generator/, sample data |
| 3 | MySQL Schema | database/, DDL scripts, indexes |
| 4 | Ingestion Service | pipeline/ingest.py, validation |
| 5 | Feature Computation | pipeline/features.py, FFT logic |
| 6 | Monitoring | monitoring/, health checks, alerts |
| 7 | Power BI Dashboards | dashboards/, .pbix files |
| 8 | Production Readiness | docs/runbook.md, deployment guide |

## Open Questions & Future Work

- **Real-time Processing**: Streaming engine (Flink/Kafka)?
- **ML Integration**: Anomaly detection models (Week 9+)
- **Edge Computing**: Run feature extraction on test bench?
- **Data Retention**: Auto-archive sessions older than 1 year?
- **Multi-Tenancy**: Support multiple customer instances?

## References

- [Data Contract](data_contract.md)
- [Quality Rules](quality_rules.md)
- ISO 10816: Mechanical vibration standards
- SKF Bearing Frequency Calculator

---

**Version**: 1.0  
**Last Updated**: 2026-02-13  
**Author**: NVM Data Pipeline Team
