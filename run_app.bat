@echo off
cd /d "%~dp0"
echo Starting InsightForge...
python -m streamlit run app.py
pause
