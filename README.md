# Forecasting Ethnic Composition Under Scenario-Based Migration Shocks

Using time-series and NLP-derived geopolitical signals to support anticipatory policy planning

Overview

This repository contains the code, notebooks, report and a Dash app for a Bachelor's graduation project that integrates UN demographic data, UN International Migrant Stock, and GDELT news-derived NLP signals to forecast ethnic composition under scenario-based migration shocks.

Repository contents

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



Author

Mohammad Javan Samboeputra Herlambang
