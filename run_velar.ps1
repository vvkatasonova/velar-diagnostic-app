$env:OPENBLAS_NUM_THREADS="1"
$env:GOTO_NUM_THREADS="1"
$env:OMP_NUM_THREADS="1"
$env:MKL_NUM_THREADS="1"

if (-not (Test-Path ".venv")) {
    py -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m streamlit run app.py
