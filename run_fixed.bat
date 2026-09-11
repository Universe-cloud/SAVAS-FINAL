@echo off
cd /d "%~dp0"
echo === SASVA - Clean Production Portal - Starting ===
echo Current folder: %CD%
echo.
echo Installing requirements (if needed)...
python -m pip install --user -r requirements_simple.txt
if %errorlevel% neq 0 (
    py -m pip install --user -r requirements_simple.txt
)
echo.
echo === Starting on http://localhost:8501 ===
echo Keep this window OPEN
echo.
python -m streamlit run app.py --server.port 8501
if %errorlevel% neq 0 (
    py -m streamlit run app.py --server.port 8501
)
pause
