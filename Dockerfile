# Use NVIDIA CUDA base image
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Miniconda
ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh

# Add conda to path
ENV PATH $CONDA_DIR/bin:$PATH

# Set working directory
WORKDIR /app

# Copy environment file
COPY environment.yml .

# Create conda environment with retry logic
RUN conda config --set ssl_verify false && \
    conda config --set channel_priority flexible && \
    conda config --set pip_interop_enabled True && \
    conda clean -afy && \
    for i in {1..3}; do \
        conda env create -f environment.yml && break || \
        if [ $i -eq 3 ]; then exit 1; fi; \
        echo "Retry $i failed, waiting before next attempt..." && \
        sleep 10; \
    done

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p \
    app/inputs/images \
    app/inputs/audio \
    app/outputs/videos \
    app/musetalk/models \
    app/musetalk/results

# Set environment variables
ENV PYTHONPATH=/app:/app/musetalk
ENV HOST=0.0.0.0
ENV PORT=8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Expose port
EXPOSE 8000

# Run the application using conda run
CMD ["/bin/bash", "-c", "source /opt/conda/etc/profile.d/conda.sh && conda activate MuseTalk && python app/api.py --host 0.0.0.0 --port 8000"] 