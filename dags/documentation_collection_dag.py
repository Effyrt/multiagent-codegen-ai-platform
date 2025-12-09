"""
Documentation Collection DAG

Scrapes code examples from official framework documentation.

Schedule: Weekly
Owner: Hemanth Rayudu
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'hemanth',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 1),
    'email': ['hemanth@example.com'],
    'email_on_failure': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'documentation_collection',
    default_args=default_args,
    description='Collect code examples from official documentation',
    schedule_interval='@weekly',
    catchup=False,
    tags=['data-collection', 'documentation', 'etl'],
)


def collect_documentation(**context):
    """Collect documentation examples"""
    import sys
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    from src.etl.docs_collector import DocsCollector
    
    collector = DocsCollector()
    collector.collect_all()
    
    return 'success'


def validate_documentation(**context):
    """Validate collected docs"""
    from pathlib import Path
    import json
    
    output_dir = Path("data/raw/documentation")
    files = list(output_dir.glob("*_docs.jsonl"))
    
    total_snippets = 0
    for file in files:
        with open(file) as f:
            total_snippets += sum(1 for _ in f)
    
    print(f"✅ Collected {total_snippets} examples from {len(files)} frameworks")
    
    context['ti'].xcom_push(key='docs_count', value=total_snippets)
    return total_snippets


# Define tasks
collect = PythonOperator(
    task_id='collect_documentation',
    python_callable=collect_documentation,
    dag=dag,
)

validate = PythonOperator(
    task_id='validate_documentation',
    python_callable=validate_documentation,
    dag=dag,
)

collect >> validate
