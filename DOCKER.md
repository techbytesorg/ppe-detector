# Docker Setup and Usage Guide

## Prerequisites

### For x86_64 Systems
- Docker installed on your system
- NVIDIA Docker runtime (for GPU support)
- NVIDIA GPU with CUDA support (recommended)

### For NVIDIA Jetson Devices
- Docker installed on your Jetson device
- JetPack 5.x or later
- NVIDIA Container Runtime for Jetson

## Building the Docker Image

### Automatic Platform Detection (Recommended)
```bash
# Make the script executable and use it
chmod +x docker-run.sh
./docker-run.sh build
```

### Manual Platform Selection

#### For x86_64 Systems
```bash
# Build the Docker image for x86_64
docker build -t ppe-detector:latest .
```

#### For NVIDIA Jetson Devices
```bash
# Build the Docker image for Jetson
docker build -f Dockerfile.jetson -t ppe-detector-jetson:latest .
```

## Running with Docker Compose (Recommended)

### For x86_64 Systems

#### Production Use
```bash
# Run the PPE detector
docker-compose up ppe-detector
```

#### Development
```bash
# Run in development mode with interactive shell
docker-compose --profile dev up ppe-detector-dev
```

### For NVIDIA Jetson Devices

#### Production Use
```bash
# Run the PPE detector on Jetson
docker-compose -f docker-compose.jetson.yml up ppe-detector-jetson
```

#### Development
```bash
# Run in development mode on Jetson
docker-compose -f docker-compose.jetson.yml --profile dev up ppe-detector-jetson-dev
```

### Using the Automated Script
```bash
# Run in production mode (auto-detects platform)
./docker-run.sh run

# Run in development mode
./docker-run.sh run development
```

## Running with Docker Commands

### x86_64 Systems

#### Basic Usage
```bash
# Run with video file processing
docker run --rm --gpus all \
  -v $(pwd)/input_files:/app/input_files \
  -v $(pwd)/output_files:/app/output_files \
  -v $(pwd)/models:/app/models \
  ppe-detector:latest
```

#### Webcam Usage
```bash
# Run with webcam access (Linux)
docker run --rm --gpus all \
  --device=/dev/video0:/dev/video0 \
  -v $(pwd)/output_files:/app/output_files \
  -v $(pwd)/models:/app/models \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  ppe-detector:latest
```

### NVIDIA Jetson Devices

#### Basic Usage
```bash
# Run with video file processing on Jetson
docker run --rm --runtime nvidia \
  -v $(pwd)/input_files:/app/input_files \
  -v $(pwd)/output_files:/app/output_files \
  -v $(pwd)/models:/app/models \
  ppe-detector-jetson:latest
```

#### CSI Camera Usage (Jetson-specific)
```bash
# Run with CSI camera on Jetson
docker run --rm --runtime nvidia \
  --device=/dev/video0:/dev/video0 \
  --device=/dev/i2c-0:/dev/i2c-0 \
  --device=/dev/i2c-1:/dev/i2c-1 \
  -v $(pwd)/output_files:/app/output_files \
  -v $(pwd)/models:/app/models \
  --privileged \
  ppe-detector-jetson:latest
```

### Interactive Development
```bash
# x86_64 systems
docker run -it --rm --gpus all \
  -v $(pwd):/app \
  --device=/dev/video0:/dev/video0 \
  ppe-detector:latest /bin/bash

# Jetson devices
docker run -it --rm --runtime nvidia \
  -v $(pwd):/app \
  --device=/dev/video0:/dev/video0 \
  --privileged \
  ppe-detector-jetson:latest /bin/bash
```

## Environment Variables

- `CUDA_VISIBLE_DEVICES`: Set GPU device (default: 0)
- `NVIDIA_VISIBLE_DEVICES`: Set NVIDIA GPU visibility (default: all)

## Volume Mounts

- `/app/input_files`: Input video files
- `/app/output_files`: Processed video outputs
- `/app/models`: YOLO model files
- `/app/results`: Analysis results

## Troubleshooting

### Platform Detection
```bash
# Check current platform
./docker-run.sh detect

# Check system requirements
./docker-run.sh check
```

### GPU Support Issues

#### x86_64 Systems
```bash
# Check NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
```

#### Jetson Devices
```bash
# Check Jetson GPU access
docker run --rm --runtime nvidia nvcr.io/nvidia/l4t-base:r35.2.1 tegrastats

# Check CUDA availability
docker run --rm --runtime nvidia nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3 \
  python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Camera Access Issues

#### General
```bash
# List available video devices
ls /dev/video*

# Check camera permissions
sudo chmod 666 /dev/video0
```

#### Jetson CSI Camera
```bash
# Test CSI camera
gst-launch-1.0 nvarguscamerasrc ! nvoverlaysink

# Check camera sensor
v4l2-ctl --list-devices
```

### Memory Issues
```bash
# x86_64: Run with memory limit
docker run --rm --gpus all --memory=8g ppe-detector:latest

# Jetson: Monitor memory usage
sudo tegrastats
```

### Performance Optimization

#### Jetson-specific
```bash
# Set maximum performance mode
sudo nvpmodel -m 0
sudo jetson_clocks

# Check current power mode
sudo nvpmodel -q
```

## Configuration

Modify the `main.py` file to change:
- Video input source
- Detection thresholds
- Output settings
- Jetson-specific configurations