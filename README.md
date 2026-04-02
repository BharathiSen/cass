## Carbon-Aware Serverless Scheduler

**Run cloud workloads in the greenest region, automatically.**

CASS-Lite v2 fetches real-time carbon intensity data from 6 global regions, intelligently picks the cleanest region, triggers serverless jobs there, and visualizes everything on a live dashboard.

---
##  Project Structure

```	ext
cass-lite-v2/
├── cloud_functions/        # Unified Production Backend
│   ├── scheduler_function/ # Core scheduling logic, adapters, & ML
│   └── worker_job/         # Basic worker implementations 
├── dashboard/              # Streamlit analytics dashboard
├── docs/                   # Deployment and operational guides
├── monitoring/             # System monitoring JSON policies
├── scripts/                # Essential DevOps & PowerShell scripts
└── requirements.txt        # Root dependencies
```

---

##  Supported Regions (6 Active)

- 🇮🇳 **India (IN)** - ~508 gCO₂/kWh
- 🇫🇮 **Finland (FI)** - ~40 gCO₂/kWh  **Cleanest!**
- 🇩🇪 **Germany (DE)** - ~265 gCO₂/kWh
- **Japan (JP)** - ~502 gCO₂/kWh
- 🇦🇺 **New South Wales, Australia (AU-NSW)** - ~327 gCO₂/kWh
- 🇧🇷 **Central-South Brazil (BR-CS)** - ~161 gCO₂/kWh

**Live carbon intensity data updated every 5 minutes!**

---

##  Sample Output

```
 DEPLOYMENT RECOMMENDATION
 Recommended Region: 🇫🇮 Finland (FI)
 Carbon Intensity: 40 gCO₂/kWh
 Savings vs Average: 260 gCO₂/kWh (86.7% reduction)
 Compared across 6 regions (avg: 300 gCO₂/kWh)
```

---

##  How It Works

1. **Fetch** - Get live carbon intensity from 6 global regions
2. **Analyze** - Compare carbon footprints across regions
3. **Decide** - Select the greenest region (e.g., Finland @ 40 gCO₂/kWh)
4. **Execute** - Trigger Cloud Function in that region
5. **Log** - Save decision to Firestore
6. **Visualize** - Display analytics in Streamlit dashboard

**Result:** Up to 86.7% carbon reduction vs deploying to average region! 🌱

---

## 🚀 Deploy to Google Cloud

### One-Click Deployment (Recommended)

Push a version tag to automatically deploy all services:

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions will automatically deploy:
- ✅ Scheduler Function (Cloud Functions Gen2)
- ✅ Worker Function (Cloud Functions Gen2)
- ✅ Dashboard (Cloud Run)

Watch deployment progress: [GitHub Actions](https://github.com/Bharathis28/cass/actions)

### Manual Deployment

Deploy individual services using gcloud CLI:

**Deploy Scheduler Function:**
```bash
gcloud functions deploy cass-scheduler \
  --gen2 \
  --runtime python312 \
  --region=asia-south1 \
  --source ./cloud_functions/scheduler_function \
  --entry-point=run_scheduler \
  --trigger-http \
  --allow-unauthenticated
```

**Deploy Worker Function:**
```bash
gcloud functions deploy cass-worker \
  --gen2 \
  --runtime python312 \
  --region=asia-south1 \
  --source ./cloud_functions/worker_job \
  --entry-point=run_worker_job \
  --trigger-http \
  --allow-unauthenticated
```

**Deploy Dashboard:**
```bash
cd dashboard
gcloud run deploy cass-lite-dashboard \
  --source . \
  --platform managed \
  --region=asia-south1 \
  --allow-unauthenticated
```

### 🌐 Live Services

- **Dashboard:** [https://cass-lite-dashboard-ocbydgmwia-el.a.run.app](https://cass-lite-dashboard-ocbydgmwia-el.a.run.app)
- **Scheduler API:** [https://cass-scheduler-ocbydgmwia-el.a.run.app](https://cass-scheduler-ocbydgmwia-el.a.run.app)
- **Worker API:** [https://cass-worker-ocbydgmwia-el.a.run.app](https://cass-worker-ocbydgmwia-el.a.run.app)

---

##  Configuration

Edit `scheduler/config.json` to:
- Add your ElectricityMap API key
- Configure region Cloud Function URLs
- Adjust cache TTL settings
- Set Firestore project details

---

##  Firestore Indexes

The project includes a composite index configuration for efficient querying of scheduling decisions.

### Deploy Firestore Indexes

```bash
gcloud firestore indexes create firestore.indexes.json
```

This creates a composite index on the `decisions` collection with:
- **timestamp** (descending) - Latest decisions first
- **region** (ascending) - Grouped by region

The index enables fast queries like:
```javascript
db.collection('decisions')
  .orderBy('timestamp', 'desc')
  .where('region', '==', 'FI')
  .limit(100)
```

### Verify Index Status

```bash
gcloud firestore indexes list
```

**Note:** Index creation can take several minutes. Monitor progress in the [Firebase Console](https://console.firebase.google.com/).

---

##  Exporting Firestore Data to BigQuery

**Optional:** For long-term carbon analytics and advanced querying, you can set up scheduled exports of the Firestore `decisions` collection to BigQuery.

### Step-by-Step Setup

1. **Open GCP Console**
   - Navigate to [BigQuery Data Transfers](https://console.cloud.google.com/bigquery/transfers)
   - Click **Create Transfer**

2. **Configure Source**
   - Source type: Select **Firestore Export**
   - Source project: Select your GCP project (e.g., `cass-lite`)

3. **Set Dataset Name**
   - Dataset ID: `cass_lite_decisions`
   - This dataset will store all exported Firestore data

4. **Configure Schedule**
   - Schedule: **Daily at midnight UTC**
   - This ensures fresh data for daily analytics
   - Optionally adjust to your preferred timezone

5. **Set Destination Table**
   - Destination table: `decisions_export`
   - This table will contain all documents from the `decisions` collection

6. **Review and Create**
   - Review configuration
   - Click **Create** to activate the transfer

### What This Enables

With Firestore data in BigQuery, you can:
- **Long-term analytics** - Query months/years of historical decisions
- **Complex aggregations** - Calculate carbon savings trends over time
- **Data visualization** - Connect to Looker Studio or Data Studio
- **ML/AI analysis** - Train models on carbon scheduling patterns
- **Cost analysis** - Track infrastructure costs alongside carbon metrics

### Example BigQuery Queries

```sql
-- Total carbon savings by region (last 30 days)
SELECT
  region,
  COUNT(*) as decision_count,
  AVG(carbon_intensity) as avg_carbon,
  SUM(savings_gco2) as total_savings
FROM `cass-lite.cass_lite_decisions.decisions_export`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY region
ORDER BY total_savings DESC;

-- Daily carbon savings trend
SELECT
  DATE(timestamp) as date,
  SUM(savings_gco2) as daily_savings,
  AVG(carbon_intensity) as avg_carbon
FROM `cass-lite.cass_lite_decisions.decisions_export`
GROUP BY date
ORDER BY date DESC
LIMIT 30;
```

### Cost Considerations

- **Firestore exports** - Free (no additional cost for exports)
- **BigQuery storage** - ~$0.02 per GB/month
- **BigQuery queries** - First 1 TB/month free
- **Expected cost** - Minimal for typical workloads (~$1-5/month)

**Note:** This is entirely optional. The CASS-Lite dashboard provides real-time analytics without BigQuery.

---



---

## 🧪 Testing

The repository contains unit tests for the scheduler components (cloud_functions/scheduler_function). 

### Running Tests
To run the automated tests using pytest and 
equests-mock:

`ash
# Install test dependencies
pip install pytest requests-mock pytest-cov

# Run all tests with verbose output
cd cloud_functions/scheduler_function
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=term
`

**Testing Coverage Includes:**
- **CarbonFetcher:** Error handling (400, 401, 429, timeouts). Greenest region selection logic.
- **JobRunner:** Retry mechanisms, timeout recoveries, URL logic, and HTTP invocations.


**Built with ❤️ for a greener cloud.**
**Making serverless computing carbon-aware, one deployment at a time.**
