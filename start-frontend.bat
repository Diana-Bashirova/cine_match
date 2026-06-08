@echo off
cd frontend
start http://127.0.0.1:3000
python -m http.server 3000
