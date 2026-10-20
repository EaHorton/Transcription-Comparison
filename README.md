# Transcription Atlas

A small Flask app for comparing transcription services through structured ratings and free-form research notes.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug
```

Open http://127.0.0.1:5000. Reviews are stored in `transcription_comparison.db` next to the app and persist between runs.

The app includes pages for Transkribus, Seeklight, Archivault, and AI-Vision OCR, plus a Comparison page with average-score donuts and category-by-category visualizations.
