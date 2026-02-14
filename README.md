# NVM Data Pipeline

A production-grade vibration monitoring data pipeline for motor test bench analytics.

## Project Overview

This project simulates a real-world industrial IoT pipeline that:
- Captures high-frequency vibration data from motor test benches
- Validates and ingests data with fault tolerance
- Computes features for predictive maintenance
- Provides near-real-time dashboards for monitoring
- Implements data quality checks and observability

## Tech Stack

- **Data Generation**: Python (NumPy, Pandas, SciPy)
- **Database**: MySQL (Bronze/Silver layers)
- **ETL Pipeline**: Python
- **Visualization**: Power BI
- **Monitoring**: Custom Python + MySQL

## Project Structure

```
nvm-data-pipeline/
├── docs/                   # Architecture & contracts
├── generator/              # Synthetic data generation
├── database/               # SQL schemas (bronze/silver)
├── pipeline/               # ETL & feature computation
├── monitoring/             # Pipeline health checks
├── dashboards/             # Power BI reports
└── data/                   # Landing, processed, quarantine
```

## 8-Week Development Plan

- **Week 1**: Architecture + Data Contracts ✓ (Current)
- **Week 2**: Synthetic Test Data Generator
- **Week 3**: MySQL Schema (Bronze/Silver)
- **Week 4**: Ingestion + Validation Service
- **Week 5**: Feature Computation Pipeline
- **Week 6**: Monitoring + Automation
- **Week 7**: Power BI Dashboards
- **Week 8**: Documentation + Production Readiness

## Getting Started

See [docs/architecture.md](docs/architecture.md) for system design.

## License

Educational project for portfolio demonstration.
