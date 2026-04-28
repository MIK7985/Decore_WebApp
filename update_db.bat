@echo off
echo =========================================
echo Updating Database for Inventory Module...
echo =========================================

echo Activating virtual environment...
call .\venv\Scripts\activate.bat

echo.
echo Running makemigrations...
python manage.py makemigrations

echo.
echo Running migrate...
python manage.py migrate

echo.
echo =========================================
echo Done! If you see "OK" above, it worked.
echo You can now close this window and restart your server.
echo =========================================
pause
