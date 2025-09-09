#!/bin/bash

# PPE Detector Docker Build and Run Script
# Supports both x86_64 and Jetson platforms

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect platform
detect_platform() {
    if [ -f "/etc/nv_tegra_release" ]; then
        echo "jetson"
    else
        arch=$(uname -m)
        if [ "$arch" = "x86_64" ]; then
            echo "x86_64"
        elif [ "$arch" = "aarch64" ] || [ "$arch" = "arm64" ]; then
            if [ -f "/proc/device-tree/model" ] && grep -q "NVIDIA" /proc/device-tree/model; then
                echo "jetson"
            else
                echo "arm64"
            fi
        else
            echo "unknown"
        fi
    fi
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
}

# Check if NVIDIA Docker runtime is available
check_nvidia_docker() {
    if ! docker run --rm --gpus all nvidia/cuda:11.0-base-ubuntu20.04 nvidia-smi &> /dev/null; then
        print_warning "NVIDIA Docker runtime not available or GPU not detected."
        print_info "The application will run in CPU mode."
        return 1
    fi
    return 0
}

# Build Docker image
build_image() {
    local platform=$1
    
    print_info "Building Docker image for platform: $platform"
    
    if [ "$platform" = "jetson" ]; then
        docker build -f Dockerfile.jetson -t ppe-detector-jetson:latest .
        print_success "Jetson image built successfully"
    else
        docker build -f Dockerfile -t ppe-detector:latest .
        print_success "x86_64 image built successfully"
    fi
}

# Run application
run_app() {
    local platform=$1
    local mode=$2  # "production" or "development"
    
    print_info "Running PPE detector on $platform in $mode mode"
    
    # Ensure required directories exist
    mkdir -p input_files output_files models results
    
    if [ "$platform" = "jetson" ]; then
        if [ "$mode" = "development" ]; then
            docker-compose -f docker-compose.jetson.yml --profile dev up ppe-detector-jetson-dev
        else
            docker-compose -f docker-compose.jetson.yml up ppe-detector-jetson
        fi
    else
        if [ "$mode" = "development" ]; then
            docker-compose --profile dev up ppe-detector-dev
        else
            docker-compose up ppe-detector
        fi
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build [platform]     Build Docker image (auto-detects platform if not specified)"
    echo "  run [mode]          Run application (production|development, default: production)"
    echo "  detect              Detect current platform"
    echo "  check               Check system requirements"
    echo "  help                Show this help message"
    echo ""
    echo "Platforms:"
    echo "  x86_64              Standard x86_64 systems with NVIDIA GPU"
    echo "  jetson              NVIDIA Jetson devices (Nano, Xavier, Orin, etc.)"
    echo ""
    echo "Examples:"
    echo "  $0 build                    # Auto-detect platform and build"
    echo "  $0 build jetson            # Build for Jetson platform"
    echo "  $0 run                     # Run in production mode"
    echo "  $0 run development         # Run in development mode"
    echo "  $0 check                   # Check system requirements"
}

# Main script logic
main() {
    local command=${1:-help}
    local arg2=$2
    
    case $command in
        "detect")
            platform=$(detect_platform)
            print_info "Detected platform: $platform"
            ;;
        "check")
            check_docker
            if check_nvidia_docker; then
                print_success "NVIDIA Docker runtime is available"
            fi
            platform=$(detect_platform)
            print_info "Platform: $platform"
            ;;
        "build")
            check_docker
            platform=${arg2:-$(detect_platform)}
            build_image "$platform"
            ;;
        "run")
            check_docker
            mode=${arg2:-production}
            platform=$(detect_platform)
            run_app "$platform" "$mode"
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"