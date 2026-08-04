@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo      TESTES AUTOMATIZADOS AFGMED
echo ========================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

%PYTHON% -m pip install -r requirements-test.txt
if errorlevel 1 (
    echo.
    echo Nao foi possivel instalar o pytest.
    pause
    exit /b 1
)

%PYTHON% -m pytest -v

echo.
if errorlevel 1 (
    echo Existem testes com falha. Veja os detalhes acima.
) else (
    echo Todos os testes passaram.
)
pause
