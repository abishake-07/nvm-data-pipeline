# Data Contract

## Overview

This document defines the data structures, formats, and agreements for the NVM vibration monitoring pipeline.

## Entities

### 1. Sensor Data (High-Frequency Vibration)

**Source**: 3-axis accelerometers on motor test bench

| Field | Type | Unit | Sampling Rate | Description |
|-------|------|------|---------------|-------------|
| `timestamp` | datetime | UTC | 25.6 kHz | Microsecond precision timestamp |
| `acc_x` | float32 | m/s² | 25.6 kHz | X-axis acceleration |
| `acc_y` | float32 | m/s² | 25.6 kHz | Y-axis acceleration |
| `acc_z` | float32 | m/s² | 25.6 kHz | Z-axis acceleration |

**Expected Range**: -200 to +200 m/s²

### 2. RPM Data (Rotational Speed)

**Source**: Optical or magnetic encoder

| Field | Type | Unit | Sampling Rate | Description |
|-------|------|------|---------------|-------------|
| `timestamp` | datetime | UTC | 10-100 Hz | Event timestamp |
| `rpm` | float32 | RPM | Variable | Rotations per minute |

**Expected Range**: 0 to 12,000 RPM

### 3. Session Metadata

**Lifecycle**: Created at test start, updated throughout session

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `test_id` | string (UUID) | ✓ | Unique test session identifier |
| `bench_id` | string | ✓ | Test bench identifier (e.g., "BENCH-01") |
| `motor_variant` | string | ✓ | Motor model/variant code |
| `firmware_version` | string | ✓ | Motor controller firmware version |
| `session_start` | datetime | ✓ | Session start time (UTC) |
| `session_end` | datetime |  | Session end time (UTC) |
| `operator_id` | string |  | Operator or system identifier |
| `test_purpose` | enum |  | production, validation, R&D, stress_test |

### 4. Phase Information

**Lifecycle**: Transitions recorded during test execution

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `phase` | enum | `idle`, `run-up`, `steady`, `run-down` | Current test phase |
| `phase_start` | datetime | - | Phase start timestamp |
| `target_rpm` | float32 | - | Target RPM for this phase |
| `duration_sec` | float32 | - | Expected phase duration |

**Phase Definitions**:
- **idle**: Motor stopped or minimal rotation (< 100 RPM)
- **run-up**: Accelerating from idle to target speed
- **steady**: Operating at stable target RPM (±2% tolerance)
- **run-down**: Decelerating from steady state to idle

## Data Formats

### Raw File Format (Week 2)

**Format**: Parquet (compressed with Snappy)

**File Naming Convention**:
```
{test_id}_{bench_id}_{timestamp}.parquet
Example: a3f5d890-bench01-20260213T143022Z.parquet
```

**Schema**:
```python
{
    "metadata": {
        "test_id": "uuid",
        "bench_id": "string",
        "motor_variant": "string",
        "firmware_version": "string",
        "session_start": "timestamp",
        "sampling_rate_hz": 25600
    },
    "samples": [
        {
            "timestamp": "2026-02-13T14:30:22.000000Z",
            "acc_x": -1.234,
            "acc_y": 0.567,
            "acc_z": 9.823,
            "rpm": 1500.5,  # Optional, may be null
            "phase": "steady"
        }
        # ... continues
    ]
}
```

### Feature File Format (Week 5)

**Format**: JSON Lines or CSV

**One row per second window**:
```json
{
    "test_id": "a3f5d890",
    "window_start": "2026-02-13T14:30:22.000000Z",
    "rms_x": 2.345,
    "rms_y": 1.987,
    "rms_z": 10.234,
    "peak_x": 12.4,
    "crest_factor_x": 5.28,
    "band_energy_0_500hz": 0.234,
    "band_energy_500_2000hz": 0.456,
    "phase": "steady",
    "rpm_avg": 1500.2
}
```

## Quality Rules

See [quality_rules.md](quality_rules.md) for detailed validation specifications.

## Versioning

- **Version**: 1.0
- **Last Updated**: 2026-02-13
- **Change Log**: Initial version
