"""
Stack Overflow Data Collection DAG

Collects Q&A pairs with code snippets from Stack Overflow.

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
    'stackoverflow_data_collection',
    default_args=default_args,
    description='Collect Q&A pairs from Stack Overflow',
    schedule_interval='@weekly',
    catchup=False,
    tags=['data-collection', 'stackoverflow', 'etl'],
)


def collect_stackoverflow_data(**context):
    """Collect Stack Overflow Q&A"""
    import sys
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    from src.etl.stackoverflow_collector import StackOverflowCollector
    
    collector = StackOverflowCollector()
    collector.collect_all(questions_per_tag=200)
    
    return 'success'


def validate_stackoverflow_data(**context):
    """Validate collected SO data"""
    from pathlib import Path
    import json
    
    output_dir = Path("data/raw/stackoverflow")
    files = list(output_dir.glob("questions_*.json"))
    
    total_questions = 0
    for file in files:
        with open(file) as f:
            data = json.load(f)
            total_questions += len(data)
    
    print(f"✅ Collected {total_questions} questions from {len(files)} tags")
    
    context['ti'].xcom_push(key='so_count', value=total_questions)
    return total_questions


# Define tasks
collect = PythonOperator(
    task_id='collect_stackoverflow',
    python_callable=collect_stackoverflow_data,
    dag=dag,
)

validate = PythonOperator(
    task_id='validate_stackoverflow',
    python_callable=validate_stackoverflow_data,
    dag=dag,
)

collect >> validate
