@echo off
set OPENBLAS_NUM_THREADS=1
set GOTO_NUM_THREADS=1
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
if not exist .venv py -m venv .venv
call .venv\Scripts\activate.bat
py -m pip install -r requirements.txt
py -m streamlit run app.py
pause
