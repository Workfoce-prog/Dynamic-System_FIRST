# FIRST Dynamic System — Streamlit Cloud App

## Files
- `streamlit_app.py`  ← **Set this as the Main file** in Streamlit Cloud.
- `first_dynamic_model.py`
- `sample_first_panel.csv`
- `requirements.txt`

## Deploy (Streamlit Cloud)
1. Upload these files to your GitHub repo root (branch `main`).
2. In Streamlit Cloud → *App Settings*:
   - **Main file path**: `streamlit_app.py`
   - **Branch**: `main`
3. Save and **Redeploy**.

## Local run
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

If you still see a blank page, temporarily set the main file to a tiny debug app that prints the file tree to verify paths.
