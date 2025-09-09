@echo off
REM PPE Detector Docker Build and Run Script for Windows
REM Supports both x86_64 and ARM64 platforms

setlocal enabledelayedexpansion

REM Colors are not easily available in batch, using simple echo
set "INFO_PREFIX=[INFO]"
set "SUCCESS_PREFIX=[SUCCESS]"
set "WARNING_PREFIX=[WARNING]"
set "ERROR_PREFIX=[ERROR]"

:main
set "command=%~1"
set "arg2=%~2"

if "%command%"=="" set "command=help"
if "%command%"=="help" goto show_usage
if "%command%"=="--help" goto show_usage
if "%command%"=="-h" goto show_usage
if "%command%"=="detect" goto detect_platform
if "%command%"=="check" goto check_requirements
if "%command%"=="build" goto build_image
if "%command%"=="run" goto run_app

echo %ERROR_PREFIX% Unknown command: %command%
goto show_usage

:detect_platform
echo %INFO_PREFIX% Detecting platform...
REM Windows systems are typically x86_64
echo %INFO_PREFIX% Detected platform: x86_64
goto :eof

:check_requirements
echo %INFO_PREFIX% Checking system requirements...

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR_PREFIX% Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)
echo %SUCCESS_PREFIX% Docker is installed

REM Check NVIDIA Docker support
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo %WARNING_PREFIX% NVIDIA Docker runtime not available or GPU not detected.
    echo %INFO_PREFIX% The application will run in CPU mode.
) else (
    echo %SUCCESS_PREFIX% NVIDIA Docker runtime is available
)

echo %INFO_PREFIX% Platform: x86_64
goto :eof

:build_image
echo %INFO_PREFIX% Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR_PREFIX% Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

set "platform=%arg2%"
if "%platform%"=="" set "platform=x86_64"

echo %INFO_PREFIX% Building Docker image for platform: %platform%

if "%platform%"=="jetson" (
    docker build -f Dockerfile.jetson -t ppe-detector-jetson:latest .
    if errorlevel 1 (
        echo %ERROR_PREFIX% Failed to build Jetson image
        exit /b 1
    )
    echo %SUCCESS_PREFIX% Jetson image built successfully
) else (
    docker build -f Dockerfile -t ppe-detector:latest .
    if errorlevel 1 (
        echo %ERROR_PREFIX% Failed to build x86_64 image
        exit /b 1
    )
    echo %SUCCESS_PREFIX% x86_64 image built successfully
)
goto :eof

:run_app
echo %INFO_PREFIX% Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR_PREFIX% Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

set "mode=%arg2%"
if "%mode%"=="" set "mode=production"

echo %INFO_PREFIX% Running PPE detector on x86_64 in %mode% mode

REM Ensure required directories exist
if not exist "input_files" mkdir "input_files"
if not exist "output_files" mkdir "output_files"
if not exist "models" mkdir "models"
if not exist "results" mkdir "results"

if "%mode%"=="development" (
    docker-compose --profile dev up ppe-detector-dev
) else (
    docker-compose up ppe-detector
)
goto :eof

:show_usage
echo Usage: %0 [COMMAND] [OPTIONS]
echo.
echo Commands:
echo   build [platform]     Build Docker image (x86_64 only on Windows)
echo   run [mode]          Run application (production^|development, default: production)
echo   detect              Detect current platform
echo   check               Check system requirements
echo   help                Show this help message
echo.
echo Platforms:
echo   x86_64              Standard x86_64 systems with NVIDIA GPU
echo   jetson              NVIDIA Jetson devices (build only, run on target device)
echo.
echo Examples:
echo   %0 build                    # Build for x86_64 platform
echo   %0 build jetson            # Cross-build for Jetson platform
echo   %0 run                     # Run in production mode
echo   %0 run development         # Run in development mode
echo   %0 check                   # Check system requirements
goto :eof