@echo off
rem Starts the Explorer Workbook web form and opens it in your browser.
rem If it is already running, this opens the existing tab instead of
rem starting a second copy. The server keeps running in its own window
rem - close that window, or press Ctrl+C in it, to stop it.
rem
rem NOTE: keep this file plain ASCII. cmd.exe's batch parser can choke on
rem non-ASCII punctuation (smart quotes, em dashes) saved as UTF-8, and the
rem failure mode is a cryptic "'x' is not recognized" pointing at the wrong
rem line entirely.

cd /d "%~dp0"

set PORT=8000
set URL=http://127.0.0.1:%PORT%

call :check_status
if %STATUS%==0 (
    echo Explorer Workbook is already running at %URL% - opening it instead of starting another copy.
    start "" "%URL%"
    goto :eof
)
if %STATUS%==2 (
    echo Something else is already listening on port %PORT%, and it does not look like the
    echo Explorer Workbook service. Stop that program first, or change PORT near the top of
    echo this file to use a different port.
    pause
    goto :eof
)

start "Explorer Workbook - Web" cmd /k python -m src.web --port %PORT%

echo Waiting for the server to start...
:wait
ping -n 2 127.0.0.1 >nul
call :check_status
if not %STATUS%==0 goto wait

start "" "%URL%"
goto :eof

rem Sets STATUS: 0 = our service is answering at %URL%, 1 = nothing is
rem listening there yet, 2 = something else owns the port.
:check_status
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%URL%/' -UseBasicParsing -TimeoutSec 2; if ($r.Content -match 'Trip Book Maker') { exit 0 } else { exit 2 } } catch { exit 1 }"
set STATUS=%errorlevel%
goto :eof
