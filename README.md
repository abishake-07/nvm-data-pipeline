# NVM Data Pipeline

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> A production-grade industrial IoT data pipeline for real-time vibration monitoring and predictive maintenance analytics on motor test benches.

## 📋 Overview

The NVM Data Pipeline is an end-to-end solution for ingesting, validating, and analyzing high-frequency vibration data from industrial motor test benches. Built with industry best practices, it demonstrates scalable data engineering patterns suitable for real-world IoT and predictive maintenance applications.

### Business Value

- **Early Fault Detection**: Identify bearing failures, misalignment, and imbalance before catastrophic failure
- **Data Quality Assurance**: Automated validation with quarantine processes to prevent bad data from polluting analytics
- **Near Real-Time Insights**: Sub-minute latency from sensor to dashboard for operational monitoring
- **Scalable Architecture**: Medallion architecture (Bronze/Silver) ready for multi-site deployment

### Use Cases

- Quality assurance testing in motor manufacturing
- Condition-based maintenance programs
- R&D testing for new motor variants
- Stress testing and reliability engineering

## 🔑 Key Features

### Data Ingestion & Validation
- **High-frequency data capture**: 25.6 kHz sampling rate (3-axis accelerometers)
- **Schema validation**: Contract-based validation with automatic quarantine
- **Fault tolerance**: Graceful handling of sensor failures, dropouts, and data corruption
- **Idempotent processing**: Safe reprocessing without duplicates

### Feature Engineering
- **Time-domain features**: RMS, peak, crest factor, kurtosis
- **Frequency-domain analysis**: FFT-based band energy extraction
- **Bearing diagnostics**: BPFO, BPFI, BSF, FTF frequency detection
- **1-second windowing**: 25,600 samples aggregated per feature vector

### Data Quality & Monitoring
- **Quality rules engine**: Range checks, timestamp continuity, gap detection
- **Pipeline health metrics**: Ingestion lag, throughput, error rates
- **Data quality scoring**: Per-session quality assessment
- **Alerting**: Automated notifications on quality degradation

### Analytics & Visualization
- **Power BI dashboards**: Session overview, variant comparison, anomaly detection
- **Near real-time updates**: DirectQuery mode with sub-minute refresh
- **Drill-through analysis**: Detailed time-series investigation
- **KPI tracking**: Operational metrics and trend analysis

## 🏗️ Architecture

### System Design

```
┌─────────────────┐
│  Test Bench     │
│  Sensors        │
│  - 3× Accel     │──┐  25.6 kHz
│  - 1× RPM       │  │  vibration data
└─────────────────┘  │
                     ↓
         ┌───────────────────────┐
         │  Data Landing Zone    │
         │  (File Watcher)       │
         └───────────┬───────────┘
                     ↓
         ┌───────────────────────┐
         │  Validation Service   │
         │  - Schema checks      │
         │  - Range validation   │
         │  - Quality rules      │
         └─────┬─────────────┬───┘
           PASS│         FAIL│
               ↓             ↓
         ┌─────────┐   ┌──────────┐
         │  MySQL  │   │Quarantine│
         │ Bronze/ │   │  Zone    │
         │ Silver  │   └──────────┘
         └────┬────┘
              ↓
    ┌────────────────────┐
    │ Feature Extraction │
    │ - Windowing        │
    │ - FFT              │
    │ - Aggregation      │
    └─────────┬──────────┘
              ↓
    ┌────────────────────┐
    │   Power BI         │
    │   Dashboards       │
    └────────────────────┘
```

### Medallion Architecture

- **Bronze Layer** (Raw): Immutable landing zone with audit trail
- **Silver Layer** (Curated): Validated, cleaned, and feature-enriched data optimized for analytics

See [`docs/architecture.md`](docs/architecture.md) for detailed system design.

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Data Generation** | Python, NumPy, SciPy | Synthetic vibration signal generation |
| **Data Storage** | MySQL 8.0+ | Time-series optimized relational database |
| **ETL Pipeline** | Python, Pandas, PyArrow | Data ingestion and transformation |
| **Feature Extraction** | NumPy, SciPy (FFT) | Signal processing and analytics |
| **Visualization** | Power BI Desktop | Interactive dashboards |
| **Orchestration** | Python (file watcher) | Event-driven automation |
| **File Format** | Parquet (Snappy) | Compressed columnar storage |

## 📁 Project Structure

```
nvm-data-pipeline/
├── docs/
│   ├── architecture.md        # System design & components
│   ├── data_contract.md       # Entity schemas & formats
│   └── quality_rules.md       # Validation specifications
├── generator/
│   ├── config.py              # Physics & session parameters
│   ├── signal_generator.py    # Vibration synthesis engine
│   ├── phases.py              # Test phase management
│   ├── anomalies.py           # Fault injection logic
│   └── main.py                # Generator CLI
├── database/
│   ├── bronze/
│   │   └── schema.sql         # Raw data registry
│   └── silver/
│       └── schema.sql         # Feature tables
├── pipeline/
│   ├── ingest.py              # Validation & loading
│   ├── features.py            # Feature computation
│   └── config.py              # Pipeline configuration
├── monitoring/
│   ├── health.py              # Pipeline metrics
│   └── alerts.py              # Notification system
├── dashboards/
│   └── nvm_analytics.pbix     # Power BI report
├── data/
│   ├── landing/               # Incoming files
│   ├── processed/             # Validated files
│   └── quarantine/            # Rejected files
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- MySQL 8.0+
- Power BI Desktop (for visualization)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/abishake-07/nvm-data-pipeline.git
   cd nvm-data-pipeline
   ```

2. **Set up Python environment**
   ```bash
   # Using uv (recommended - faster)
   uv venv
   .\.venv\Scripts\Activate.ps1  # Windows
   uv pip install -r requirements.txt

   # Or using pip
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

3. **Configure MySQL database**
   ```sql
   CREATE DATABASE nvm_pipeline;
   -- Run schema files in database/bronze/ and database/silver/
   ```

4. **Set environment variables**
   ```bash
   # Create .env file
   DB_HOST=localhost
   DB_USER=your_user
   DB_PASSWORD=your_password
   DB_NAME=nvm_pipeline
   ```

### Quick Start

1. **Generate synthetic test data**
   ```bash
   python generator/main.py --sessions 5 --duration 180
   ```

2. **Run ingestion pipeline**
   ```bash
   python pipeline/ingest.py --watch data/landing/
   ```

3. **Open Power BI dashboard**
   ```bash
   # Open dashboards/nvm_analytics.pbix
   # Configure data source connection to MySQL
   ```

## 📖 Documentation

- **[Architecture](docs/architecture.md)**: System design, components, and data flow
- **[Data Contract](docs/data_contract.md)**: Entity schemas, formats, and conventions
- **[Quality Rules](docs/quality_rules.md)**: Validation specifications and thresholds

## 📊 Data Quality Metrics

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| **Ingestion Success Rate** | > 98% | < 95% |
| **Quarantine Rate** | < 2% | > 5% |
| **Ingestion Lag** | < 30s | > 60s |
| **Data Completeness** | > 99% | < 95% |
| **Timestamp Continuity** | > 99.9% | < 99% |

## 🤝 Contributing

This is a portfolio/educational project, but feedback and suggestions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/improvement`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Abishake**
- GitHub: [@abishake-07](https://github.com/abishake-07)

## 🙏 Acknowledgments

- Vibration analysis based on ISO 10816 standards
- Bearing frequency calculations from SKF engineering data
- Inspired by real-world industrial IoT architectures

---

**Note**: This is a demonstration project using synthetic data. For production deployment with real sensors, additional considerations for hardware integration, security, and regulatory compliance are required.
