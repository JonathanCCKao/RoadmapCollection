@echo off
:: 切換工作目錄至此批次檔所在的資料夾，確保路徑正確
cd /d "%~dp0"

echo ====================================================================
echo  Moxa Swap Switch Project Gantt Roadmap - Confluence Auto Sync Tool
echo ====================================================================
echo.
echo [INFO] Starting synchronization script...
echo.

python main.py

echo.
echo ====================================================================
echo [INFO] Sync process completed.
echo.
pause
