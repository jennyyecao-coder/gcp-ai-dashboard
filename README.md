# Online Retail Dashboard

An interactive Streamlit dashboard that connects to Google BigQuery to visualise customer, product, and market insights from the `jennys-first-project.sales_data.online_retail` dataset.

**Live app:** https://online-retail-dashboard-802296198860.us-central1.run.app

## Features

- **KPI metrics** — total revenue, orders, unique customers, and products at a glance
- **Customer Insights** — top customers by revenue, customer distribution by country, monthly revenue trend
- **Product Insights** — top products by revenue and units sold, product search
- **Market Insights** — revenue and orders by country, average order value, country summary table
- **Sidebar filters** — filter all charts by date range and country

## Tech stack

- [Streamlit](https://streamlit.io) — dashboard framework
- [Google BigQuery](https://cloud.google.com/bigquery) — data source
- [Pandas](https://pandas.pydata.org) — data manipulation
- Deployed on [Google Cloud Run](https://cloud.google.com/run)

## Local development

**Prerequisites:** Python 3.11+, `gcloud` CLI authenticated with application default credentials.

```bash
# Authenticate
gcloud auth application-default login

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
source venv/bin/activate       # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will be available at http://localhost:8501.

## Deployment (Google Cloud Run)

```bash
gcloud run deploy online-retail-dashboard \
  --source . \
  --project jennys-first-project \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account retail-dashboard-sa@jennys-first-project.iam.gserviceaccount.com
```

The Cloud Run service account (`retail-dashboard-sa`) requires the following IAM roles on the project:
- `roles/bigquery.dataViewer`
- `roles/bigquery.jobUser`
