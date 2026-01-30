# real-estate-scraping-pipeline-dashboard
End-to-end real estate data pipeline (cleaning, analysis and Streamlit dashboard).
# Real Estate Data Pipeline and Dashboard

This project implements an end-to-end data pipeline for real estate listings,
from raw data ingestion to cleaning, analysis and interactive visualization.

## Objective
- Build a reproducible data pipeline
- Clean and structure raw real estate data
- Provide analytical insights through a Streamlit dashboard

## Workflow
1. Raw data ingestion (CSV)
2. Data cleaning and transformation
3. Feature engineering
4. Exploratory analysis
5. Interactive dashboard

## Project Structure
- `run_pipeline.py`: executes the full data processing pipeline
- `dashboard.py`: Streamlit dashboard for data exploration
- `pipeline_clean_analyse.ipynb`: exploratory and validation notebook
- `requirements.txt`: project dependencies

## Tools
Python, Pandas, NumPy, PyArrow, Streamlit

## How to Run
```bash
python3 run_pipeline.py
python3 -m streamlit run dashboard.py
