# Use official PyTorch image with CUDA 11.7
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CFLAGS="-std=c++17"
ENV CXXFLAGS="-std=c++17"
ENV TORCH_CUDA_ARCH_LIST="7.5"
ENV FORCE_CUDA=1
ENV MMCV_WITH_OPS=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    ca-certificates \
    build-essential \
    cmake \
    pkg-config \
    libx11-dev \
    libatlas-base-dev \
    libgtk-3-dev \
    libboost-python-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt 

RUN pip install --no-cache-dir -U openmim 

RUN mim install mmengine 
RUN mim install mmcv && \
    mim install mmdet && \
    mim install mmpose

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p \
    app/inputs/images \
    app/inputs/audio \
    app/outputs/videos \
    app/musetalk/models \
    app/musetalk/results \
    /app/models/musetalkV15 \
    /app/models/whisper

# Set environment variables
ENV PYTHONPATH=/app:/app/musetalk
ENV HOST=0.0.0.0
ENV PORT=8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "app/api.py", "--host", "0.0.0.0", "--port", "8000"] 