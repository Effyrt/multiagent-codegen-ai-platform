FROM apache/airflow:2.8.0-python3.11

USER root

# Install git for cloning repos
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean

USER airflow

# Install all CodeGen AI dependencies
RUN pip install --no-cache-dir \
    pinecone-client==3.0.0 \
    openai==1.3.7 \
    python-dotenv==1.0.0 \
    requests==2.31.0 \
    beautifulsoup4==4.12.2

