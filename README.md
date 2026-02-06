# Forecasting Ethnic Composition Under Scenario-Based Migration Shocks

Using time-series and NLP-derived geopolitical signals to support anticipatory policy planning

Overview

This repository contains the code, notebooks, report and a Dash app for a Bachelor's graduation project that integrates UN demographic data, UN International Migrant Stock, and GDELT news-derived NLP signals to forecast ethnic composition under scenario-based migration shocks.

Repository contents (top-level)

- Notebooks:
  - 1.1-Data Preprocessing.ipynb
  - 1.2-Exploratory Data Analysis.ipynb
  - 1.3-Feature Engineering.ipynb
  - 2.1-GDELT.ipynb
  - 2.2-NLP Topics.ipynb
  - 3.1-Final Panel Builder 2.0.ipynb
  - 3.2-Modeling 2.0.ipynb
  - 3.3-Migration Delta 2.0.ipynb
  - 4.0-build_master_dataset.ipynb
- Application:
  - app.py — Dash/Plotly dashboard entrypoint
- Report:
  - Forecasting Ethnic Composition Under Scenario-Based Migration Shocks Using Time-Series and NLP To Support Policy Planning (1).pdf — final thesis/report
- Directories:
  - assets/ — static assets used by the app or notebooks
  - data/ — placeholder for raw and processed datasets (not tracked here)
  - Imports/ — supplementary import files or scripts

Quick summary

- Goal: forecast ethnic composition under volatile geopolitical conditions by combining structured demographic time-series with unstructured global news signals (GDELT → BERTopic / sentiment / intensity) and run scenario simulations (conflict, aid changes, migration pressure).
- Countries in example analysis: United States, Malaysia, Indonesia
- Historical period covered in analysis: 1996–2024; forecast horizon in notebooks: 2025–2035

Quick start

1. Clone the repo

   git clone https://github.com/Vansaher/Forecasting-Ethnic-composition-Using-time-series-and-Geopolitical-NLP-to-Support-Policy-Planning.git
   cd Forecasting-Ethnic-composition-Using-time-series-and-Geopolitical-NLP-to-Support-Policy-Planning

2. Create and activate a virtual environment

   python -m venv .venv
   source .venv/bin/activate    # Windows: .venv\Scripts\activate

3. Install dependencies

   If a requirements.txt exists, install it:
     pip install -r requirements.txt

   Otherwise, install the main packages used by the notebooks and app:
     pip install pandas numpy scikit-learn xgboost bertopic sentence-transformers plotly dash matplotlib seaborn google-cloud-bigquery jupyter

4. Place input data

   - Raw UN ethnic composition and UN International Migrant Stock files should be placed in data/ (or the locations expected by the notebooks).
   - GDELT extracts can be downloaded or queried from BigQuery and saved under data/ as CSVs or parquet files. If using BigQuery, set GOOGLE_APPLICATION_CREDENTIALS to your service account key.
   - The notebooks expect processed/cleaned datasets to be available; run the preprocessing notebooks to build them.

5. Reproduce notebooks (recommended order)

   1. 1.1-Data Preprocessing.ipynb
   2. 1.2-Exploratory Data Analysis.ipynb
   3. 1.3-Feature Engineering.ipynb
   4. 2.1-GDELT.ipynb
   5. 2.2-NLP Topics.ipynb
   6. 3.1-Final Panel Builder 2.0.ipynb
   7. 3.2-Modeling 2.0.ipynb
   8. 3.3-Migration Delta 2.0.ipynb
   9. 4.0-build_master_dataset.ipynb

6. Run the dashboard (simple local run)

   python app.py
   # open http://127.0.0.1:8050 in your browser

Notes and alignment with repository files

- The repository currently includes multiple analysis notebooks (1.x–4.0), an app.py dashboard, a thesis PDF, and top-level directories (assets/, data/, Imports/).
- There is no requirements.txt or LICENSE in the repo root; adding these is recommended for reproducibility and clarity.
- The app.py depends on processed dataset files in data/ — review app.py for exact file paths and place the processed inputs accordingly.
- The large PDF report is included at the top level; you may move it to docs/ if you prefer a cleaner layout.

Suggested next steps (I can help with any of these)
- Add a pinned requirements.txt (I can generate one based on the notebooks and app imports).
- Add a LICENSE file (MIT or another preferred license).
- Create data/README.md describing the expected filenames and formats, or add a small sample dataset in data/sample/ for demoing the app without the full dataset.
- Optional: commit a .env.example documenting required environment variables (e.g., GOOGLE_APPLICATION_CREDENTIALS).

Author

Mohammad Javan Samboeputra Herlambang (they)