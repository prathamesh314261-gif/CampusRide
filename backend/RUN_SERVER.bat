@echo off
echo =======================================
echo     CampusRide Backend Server
echo =======================================
cd /d "%~dp0"
echo Checking port 15501...
python -c "import subprocess; out = subprocess.check_output('netstat -ano', text=True); [subprocess.run(['taskkill', '/F', '/PID', l.strip().split()[-1]], capture_output=True) for l in out.splitlines() if ':15501' in l and 'LISTENING' in l]"
echo Starting FastAPI server on http://127.0.0.1:15501...
python -m uvicorn main:app --host 0.0.0.0 --port 15501 --reload
pause
