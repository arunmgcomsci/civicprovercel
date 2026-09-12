@echo off
title CivicPro Server
cd /d "%~dp0"
echo ==============================================
echo        Starting CivicPro Web Application       
echo ==============================================
echo Opening http://127.0.0.1:8000/ in your browser...
start http://127.0.0.1:8000/
echo.
python manage.py runserver 127.0.0.1:8000
pause
