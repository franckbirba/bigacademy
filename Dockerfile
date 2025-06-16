FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for Argilla integration
RUN pip install argilla pandas

# Copy BigAcademy source code
COPY bigacademy/ ./bigacademy/
COPY configs/ ./configs/
COPY setup.py .
COPY README.md .

# Install BigAcademy in development mode
RUN pip install -e .

# Create directories
RUN mkdir -p /app/datasets /app/data /app/scripts

# Copy integration scripts
COPY scripts/ ./scripts/

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["/bin/bash"]