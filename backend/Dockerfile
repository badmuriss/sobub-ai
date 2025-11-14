# ============================================================================
# Stage 1: Test Stage
# Runs tests before building the final image
# ============================================================================
FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04 AS test

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV DATABASE_PATH=/tmp/test_memes.db
ENV AUDIO_DIR=/tmp/test_audio
ENV MODELS_DIR=/tmp/test_models
ENV DATA_DIR=/tmp/test_data
ENV LOGS_DIR=/tmp/test_logs
ENV LOG_FILE=/tmp/test_logs/sobub.log
ENV ENABLE_FILE_LOGGING=false

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies (including test dependencies)
RUN pip3 install --no-cache-dir -r requirements.txt \
    && pip3 install --no-cache-dir -r requirements-dev.txt

# Download NLTK data
RUN python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('punkt_tab')"

# Copy application code and tests
COPY ./app /app/app
COPY ./tests /app/tests
COPY pytest.ini /app/pytest.ini

# Create test directories
RUN mkdir -p /tmp/test_audio /app/data/audio_files

# Run tests
# This will fail the build if tests don't pass
RUN pytest -v --tb=short || (echo "Tests failed! Build aborted." && exit 1)

# ============================================================================
# Stage 2: Production Stage
# Only built if tests pass
# ============================================================================
FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04 AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements (production only)
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Download NLTK data for stemming and tokenization
RUN python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('punkt_tab')"

# Copy application code (from test stage to ensure it's the tested version)
COPY --from=test /app/app /app/app

# Create necessary directories
RUN mkdir -p /app/data/audio_files /app/models /app/data/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Default target is production
FROM production
