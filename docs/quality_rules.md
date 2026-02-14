# Data Quality Rules

## Overview

This document defines validation rules and quality checks applied during data ingestion. All data must pass these checks before being loaded into the silver layer.

## Validation Levels

1. **Blocking**: Data fails ingestion, sent to quarantine
2. **Warning**: Data is ingested but flagged for review
3. **Info**: Logged for observability, no action required

## Rule Categories

### 1. Schema Validation (Blocking)

| Rule ID | Description | Action |
|---------|-------------|--------|
| `SCH-001` | All required metadata fields present | Reject if missing |
| `SCH-002` | Field types match contract | Reject if type mismatch |
| `SCH-003` | Timestamp format is ISO 8601 with timezone | Reject if invalid |
| `SCH-004` | test_id is valid UUID format | Reject if invalid |

### 2. Range Validation

#### Accelerometer Data

| Rule ID | Field | Range | Level | Action |
|---------|-------|-------|-------|--------|
| `RNG-001` | `acc_x` | -200 to +200 m/s² | Blocking | Reject if outside ±200 |
| `RNG-002` | `acc_y` | -200 to +200 m/s² | Blocking | Reject if outside ±200 |
| `RNG-003` | `acc_z` | -200 to +200 m/s² | Blocking | Reject if outside ±200 |
| `RNG-004` | `acc_*` | Suspicious if > 100 m/s² sustained | Warning | Flag for review |
| `RNG-005` | `acc_*` | Stuck-at detection: same value for > 100 samples | Warning | Flag sensor fault |

**Stuck-at Detection Algorithm**:
```python
if std_deviation(last_100_samples) < 0.001:
    flag_as_stuck_sensor()
```

#### RPM Data

| Rule ID | Field | Range | Level | Action |
|---------|-------|-------|-------|--------|
| `RNG-010` | `rpm` | 0 to 12,000 | Blocking | Reject if outside range |
| `RNG-011` | `rpm` | Acceleration limit: < 5000 RPM/sec | Warning | Flag unrealistic change |
| `RNG-012` | `rpm` | Phase mismatch: idle phase but RPM > 500 | Warning | Flag phase labeling issue |

### 3. Timestamp Continuity

| Rule ID | Description | Tolerance | Level | Action |
|---------|-------------|-----------|-------|--------|
| `TS-001` | Timestamps are monotonically increasing | - | Blocking | Reject if out-of-order |
| `TS-002` | Sample interval consistency | ±5% of 39.0625 µs | Warning | Flag timing jitter |
| `TS-003` | No duplicate timestamps | - | Blocking | Reject duplicates |
| `TS-004` | Gap detection (missing blocks) | > 100 ms gap | Warning | Flag as dropout |

**Expected Sample Interval**: 
- 25.6 kHz = 1 sample every 39.0625 microseconds
- Tolerance: 37.1 to 41.0 microseconds

**Gap Handling**:
```
Gap < 10 ms: Interpolate (info log)
Gap 10-100 ms: Flag warning, create NaN window
Gap > 100 ms: Major dropout, quarantine session
```

### 4. Missing Data Blocks

| Rule ID | Description | Threshold | Level | Action |
|---------|-------------|-----------|-------|--------|
| `MD-001` | Missing sample percentage per session | > 5% | Blocking | Reject session |
| `MD-002` | Missing sample percentage per session | 1-5% | Warning | Ingest with flag |
| `MD-003` | Missing metadata fields | Any required field | Blocking | Reject session |
| `MD-004` | Missing phase labels | > 10% of samples | Warning | Ingest with unknown phase |

### 5. Statistical Anomalies (Warning Level)

| Rule ID | Description | Condition | Action |
|---------|-------------|-----------|--------|
| `STAT-001` | RMS spike | RMS > 3× rolling median | Flag window |
| `STAT-002` | Zero variance | σ < 0.001 for > 1 second | Flag stuck sensor |
| `STAT-003` | Clipping detection | > 5% samples at exactly ±200 | Flag clipped data |
| `STAT-004` | SNR degradation | SNR < 10 dB | Flag noisy data |

### 6. Cross-Field Consistency

| Rule ID | Description | Level | Action |
|---------|-------------|-------|--------|
| `CONS-001` | Phase = idle but RPM > 500 | Warning | Flag metadata issue |
| `CONS-002` | Phase = steady but RPM variance > 10% | Warning | Flag unstable operation |
| `CONS-003` | session_end < session_start | Blocking | Reject metadata |
| `CONS-004` | RPM timestamp outside session window | Warning | Trim or flag |

## Quarantine Process

When data fails blocking validation:

1. **Move to Quarantine**: Copy file to `data/quarantine/` folder
2. **Log Error**: Write to `quarantine_log` table with:
   - `test_id`
   - `quarantine_timestamp`
   - `failed_rules` (JSON array)
   - `error_details`
   - `file_path`
3. **Alert**: Send notification if quarantine rate > 5%
4. **Manual Review**: Operator can reprocess after fixes

## Quality Metrics (Week 6)

Track these metrics for pipeline health:

- **Pass Rate**: % sessions passing all blocking rules
- **Quarantine Rate**: % sessions in quarantine
- **Warning Rate**: % sessions with warnings
- **Gap Rate**: Average gap percentage per session
- **Stuck Sensor Rate**: % sessions with stuck sensors

## Implementation Notes

### Validation Order

```
1. Schema validation (fast fail)
2. Range validation (per-sample)
3. Timestamp continuity (sequential)
4. Statistical checks (windowed)
5. Cross-field consistency (session-level)
```

### Performance Considerations

- Run blocking checks during streaming ingestion
- Defer statistical checks to post-ingestion job
- Use sampling for large files (validate every Nth sample)
- Parallelize validation across files

## Version History

- **v1.0** (2026-02-13): Initial quality rules
