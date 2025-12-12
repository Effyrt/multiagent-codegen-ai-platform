FROM apache/airflow:2.10.4-python3.12

# Switch to root for system packages
USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Copy requirements file
COPY requirements.txt /requirements.txt

# Install Python dependencies (removed --user flag)
RUN pip install --no-cache-dir -r /requirements.txt

# Verify installations
RUN pip list | grep -E "(openai|pinecone|fastapi|streamlit|crewai)" || true

# Set working directory
WORKDIR /opt/airflow