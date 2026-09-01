@echo off
echo Starting SmileCare Dental Hospital Server...
echo.
echo Website: http://127.0.0.1:8000/
echo Admin Panel: http://127.0.0.1:8000/admin-panel/
echo Admin Login: admin / admin123
echo.
echo Press CTRL+C to stop the server.
echo.
cd /d "%~dp0"

python manage.py runserver

