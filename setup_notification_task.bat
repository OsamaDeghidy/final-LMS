@echo off
echo ===================================================
echo Setting up Meeting Notification Scheduled Task
echo ===================================================
echo.

set TASK_NAME=LMS_Meeting_Notifications
set SCRIPT_PATH=%~dp0send_notifications.bat
set CURRENT_DIR=%~dp0

echo Task Name: %TASK_NAME%
echo Script Path: %SCRIPT_PATH%
echo.

echo Creating scheduled task to run every 5 minutes...
schtasks /create /tn %TASK_NAME% /tr "%SCRIPT_PATH%" /sc minute /mo 5 /ru "%USERNAME%" /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Task created successfully!
    echo The notification system will check for pending notifications every 5 minutes.
) else (
    echo.
    echo Failed to create task. Please run this script as administrator.
)

echo.
echo To verify the task was created, open Task Scheduler and look for "%TASK_NAME%"
echo.
pause
