FROM apache/airflow:2.8.0-python3.11

USER root
RUN apt-get update && apt-get install -y git curl && apt-get clean

USER airflow

COPY requirements-cloud.txt /opt/airflow/requirements.txt
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt

COPY airflow/dags /opt/airflow/dags

# Use SequentialExecutor for demo (no external DB needed)
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__CORE__EXECUTOR=SequentialExecutor
ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=sqlite:////opt/airflow/airflow.db

EXPOSE 8080

# Simpler initialization
RUN airflow db init

CMD ["airflow", "webserver"]
