@echo off
chcp 65001 > nul
cd /d %~dp0
echo ==========================================
echo   AI Agent Activity Automation System
echo ==========================================
echo [1/1] Running Python script...
"C:\Users\natum\anaconda3\python.exe" record_agent.py
echo ==========================================
echo 処理が終了しました。このウィンドウを閉じることができます。
pause
