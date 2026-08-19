@echo off
:: 切換工作目錄至此批次檔所在的資料夾，確保環境路徑正確
cd /d "%~dp0"

:: 執行自動化檢查與繪圖同步程式
python main.py
