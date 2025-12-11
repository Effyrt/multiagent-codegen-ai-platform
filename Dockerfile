FROM apache/airflow:latest-python3.12

# Switch to airflow user (very important)
USER airflow

# Copy requirements
COPY requirements.txt /requirements.txt

# Install dependencies using airflow user
RUN pip install --user --no-cache-dir -r /requirements.txt

# Show installed libs
RUN pip list

RUN pip install openai==0.28
