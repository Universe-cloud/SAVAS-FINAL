@echo off
cd /d "%~dp0"
echo === SASVA LOCALHOST TEST ===
echo Installing minimal requirements...
py -m pip install --quiet streamlit python-dotenv pandas deep-translator
echo.
echo Starting SASVA on http://localhost:8501
echo Keep this window open!
echo.
py -m streamlit run app.py --server.port 8501
pause
