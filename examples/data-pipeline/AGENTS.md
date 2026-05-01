# Data Analytics Pipeline - Agent Knowledge Base

## 🎯 Project Overview
**Domain**: Data Engineering (Python + Apache Airflow)  
**Type**: ETL pipeline for customer analytics  
**Scale**: ~30K LOC, 45 DAGs, 2TB daily processing  
**Team Size**: 6 data engineers

## 📁 Architecture Map

```
src/
├── dags/                   # Airflow DAG definitions
│   ├── ingestion/         # Data ingestion DAGs
│   ├── transformation/    # ETL transformation DAGs
│   └── reporting/         # Analytics & reporting DAGs
├── operators/             # Custom Airflow operators
│   ├── s3_operators.py
│   ├── snowflake_operators.py
│   └── validation_operators.py
├── transformations/       # Data transformation logic
│   ├── cleansing/
│   ├── enrichment/
│   └── aggregation/
├── utils/
│   ├── db_connectors.py
│   ├── data_quality.py
│   └── monitoring.py
└── config/
    ├── schemas/           # Data schemas (JSON Schema)
    └── connections.yaml   # Connection configs
```

## 🔑 Core Systems

### 1. Data Ingestion Layer
- **Entry**: `src/dags/ingestion/customer_events_dag.py`
- **Sources**: Kafka, REST APIs, S3 buckets
- **Frequency**: Real-time (Kafka) + Batch (hourly)
- **Volume**: 50M events/day
- **Storage**: Raw data → S3 (Parquet format)

### 2. Transformation Pipeline
- **Orchestrator**: Apache Airflow 2.7
- **Compute**: AWS EMR (Spark 3.4)
- **Pattern**: Bronze → Silver → Gold layers
- **Validation**: Great Expectations framework
- **Lineage**: OpenLineage integration

### 3. Data Warehouse
- **Platform**: Snowflake
- **Schema**: Star schema (fact + dimension tables)
- **Partitioning**: By date and customer_id
- **Clustering**: On frequently queried columns
- **Retention**: 2 years hot, 5 years cold storage

### 4. Monitoring & Alerting
- **Metrics**: Prometheus + Grafana
- **Logs**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Alerts**: PagerDuty integration
- **SLAs**: 99.9% uptime, < 2hr data freshness

## 🛠️ Slash Commands

### /trace-dag-failure
**Purpose**: Debug failed Airflow DAG runs  
**Usage**: When DAG execution fails  
**Analyzes**:
1. Task dependency chain
2. Upstream data availability
3. Resource constraints (memory, CPU)
4. External service timeouts

**Example**:
```bash
/trace-dag-failure customer_analytics_daily
# Output: Task 'validate_schema' failed at 03:15 UTC
# Cause: Schema mismatch in customer_events table
# Fix: Update schema in config/schemas/customer_events.json
```

### /validate-data-quality
**Purpose**: Check data quality rules  
**Usage**: Before promoting data to production  
**Validates**:
1. Null value percentages
2. Duplicate records
3. Referential integrity
4. Business rule compliance

**Example**:
```bash
/validate-data-quality silver.customer_transactions
# Checks: 
# - customer_id NOT NULL: ✓ 100%
# - amount > 0: ✗ 0.02% violations (500 records)
# - valid_date range: ✓ All within bounds
```

### /optimize-spark-job
**Purpose**: Improve Spark job performance  
**Usage**: When jobs exceed SLA  
**Analyzes**:
1. Data skew in partitions
2. Shuffle operations
3. Memory usage patterns
4. Broadcast join opportunities

**Example**:
```bash
/optimize-spark-job transformations/aggregation/daily_summary.py
# Suggestions:
# - Repartition by customer_id (currently skewed)
# - Broadcast small dimension tables
# - Increase executor memory to 8GB
# - Cache intermediate results
```

### /check-lineage
**Purpose**: Trace data lineage and dependencies  
**Usage**: Impact analysis for schema changes  
**Maps**:
1. Upstream data sources
2. Transformation steps
3. Downstream consumers
4. Business reports affected

**Example**:
```bash
/check-lineage gold.customer_lifetime_value
# Upstream: silver.transactions, silver.customers
# Transformations: 3 aggregation steps
# Downstream: 12 dashboards, 5 ML models
# Impact: HIGH - Used in executive reports
```

## 🧩 Pipeline Patterns

### Incremental Load Pattern
```python
# src/dags/ingestion/incremental_load_dag.py
def load_incremental_data(**context):
    last_run = context['prev_execution_date']
    new_data = extract_since(last_run)
    validate_and_load(new_data)
    update_watermark(context['execution_date'])
```

### Idempotent Transformation
```python
# src/transformations/cleansing/deduplicate.py
def deduplicate_records(df, partition_key):
    # Always produces same output for same input
    return df.dropDuplicates([partition_key, 'event_timestamp'])
```

### Data Quality Gate
```python
# src/operators/validation_operators.py
class DataQualityOperator(BaseOperator):
    def execute(self, context):
        results = run_expectations(self.dataset)
        if results.success_percent < self.threshold:
            raise AirflowException("Quality check failed")
```

## 📊 Data Flow

### Customer Analytics Flow
1. **Ingestion**: Kafka → S3 (raw events, Parquet)
2. **Bronze Layer**: Raw data with metadata
3. **Silver Layer**: Cleaned, deduplicated, validated
4. **Gold Layer**: Business-level aggregations
5. **Consumption**: Snowflake → BI tools (Tableau, Looker)

### Real-time vs Batch
- **Real-time**: Kafka Streams → Redis (last 24h)
- **Batch**: Airflow DAGs → S3 → Snowflake (historical)
- **Lambda Architecture**: Merge real-time + batch views

## 🔍 Common Issues & Solutions

### Issue: DAG not triggering on schedule
**Location**: `src/dags/transformation/daily_aggregation_dag.py`  
**Cause**: Incorrect `schedule_interval` format  
**Fix**: Use cron expression or timedelta, not string

### Issue: Out of memory in Spark job
**Location**: `src/transformations/aggregation/customer_summary.py`  
**Cause**: Large shuffle without proper partitioning  
**Fix**: Repartition before groupBy, increase executor memory

### Issue: Data freshness SLA breach
**Location**: `src/dags/ingestion/customer_events_dag.py`  
**Cause**: Upstream API rate limiting  
**Fix**: Implement exponential backoff, parallel ingestion

### Issue: Schema evolution breaking pipeline
**Location**: `src/utils/schema_registry.py`  
**Cause**: No backward compatibility check  
**Fix**: Use Avro schema registry with compatibility rules

## 🚀 Performance Metrics

- **Data Freshness**: < 2 hours (p95)
- **Pipeline Success Rate**: 99.5%
- **Processing Throughput**: 2TB/day
- **Query Performance**: < 5s (p95) on Snowflake
- **Cost Efficiency**: $0.15 per GB processed

## 🔐 Security & Compliance

- ✅ Data encryption at rest (S3, Snowflake)
- ✅ Encryption in transit (TLS 1.3)
- ✅ PII masking in non-prod environments
- ✅ GDPR compliance (data retention policies)
- ✅ Role-based access control (RBAC)
- ✅ Audit logging (all data access tracked)

## 📚 Key Dependencies

```python
# requirements.txt
apache-airflow==2.7.0
pyspark==3.4.0
great-expectations==0.17.0
snowflake-connector-python==3.0.0
kafka-python==2.0.2
boto3==1.28.0
pandas==2.0.0
pyarrow==12.0.0
```

## 🎓 Onboarding Guide

### Day 1: Environment Setup
1. Install Python 3.10 and dependencies
2. Configure AWS credentials
3. Set up local Airflow instance
4. Connect to dev Snowflake account

### Week 1: Core Concepts
- Understand Bronze/Silver/Gold architecture
- Learn Airflow DAG patterns
- Study data quality framework
- Review schema evolution process

### Month 1: Pipeline Development
- Build new ingestion DAG
- Implement data quality checks
- Optimize existing transformations
- Deploy to staging environment

## 📈 Monitoring Dashboard

### Key Metrics to Watch
1. **DAG Success Rate**: Target > 99%
2. **Data Freshness**: Target < 2 hours
3. **Cost per GB**: Target < $0.20
4. **Query Performance**: Target < 5s p95
5. **Storage Growth**: Monitor for anomalies

### Alert Thresholds
- **Critical**: DAG failure, data quality < 95%
- **Warning**: Latency > 3 hours, cost spike > 20%
- **Info**: Schema changes, new data sources

---

**Last Updated**: 2026-05-01  
**Maintained By**: Data Engineering Team  
**Questions?**: #data-eng-help on Slack