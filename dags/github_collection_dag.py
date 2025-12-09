"""
GitHub Data Collection DAG

Orchestrates collection of code snippets from 50+ GitHub repositories.

Schedule: Weekly
Owner: Hemanth Rayudu
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup
import json
from pathlib import Path

# Default arguments for all tasks
default_args = {
    'owner': 'hemanth',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 1),
    'email': ['hemanth@example.com'],  # Update with your email
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=4),
}

# Create DAG
dag = DAG(
    'github_data_collection',
    default_args=default_args,
    description='Collect code snippets from GitHub repositories',
    schedule_interval='@weekly',  # Run once per week
    catchup=False,
    max_active_runs=1,
    tags=['data-collection', 'github', 'etl'],
)


# Task functions
def check_github_token(**context):
    """Check if GitHub token is configured"""
    import os
    
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        raise ValueError(
            "GITHUB_TOKEN not found! "
            "Please set it in Airflow Variables or environment."
        )
    
    print(f"✅ GitHub token configured")
    context['ti'].xcom_push(key='github_token_status', value='configured')
    return 'configured'


def collect_github_repos(**context):
    """Collect code from GitHub repositories"""
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    from src.etl.github_collector_expanded import ExpandedGitHubCollector
    
    print("=" * 60)
    print("Starting GitHub collection...")
    print("=" * 60)
    
    collector = ExpandedGitHubCollector()
    results = collector.collect_all()
    
    # Push results to XCom for next tasks
    context['ti'].xcom_push(key='collection_results', value=results)
    
    print(f"✅ Collection complete!")
    return results


def validate_collected_data(**context):
    """Validate collected data quality"""
    from pathlib import Path
    import json
    
    output_dir = Path("data/raw/github_expanded")
    
    # Count collected files
    repo_files = list(output_dir.glob("*.json"))
    total_files = len(repo_files)
    
    # Read and validate each file
    total_snippets = 0
    valid_files = 0
    
    for file in repo_files:
        try:
            with open(file) as f:
                data = json.load(f)
                if isinstance(data, list):
                    total_snippets += len(data)
                    valid_files += 1
        except Exception as e:
            print(f"⚠️  Error validating {file.name}: {e}")
    
    results = {
        'total_files': total_files,
        'valid_files': valid_files,
        'total_snippets': total_snippets,
        'average_per_file': total_snippets / max(valid_files, 1)
    }
    
    print(f"✅ Validation complete:")
    print(f"   Files: {valid_files}/{total_files}")
    print(f"   Snippets: {total_snippets}")
    
    # Push to XCom
    context['ti'].xcom_push(key='validation_results', value=results)
    
    # Fail if no data collected
    if total_snippets == 0:
        raise ValueError("No snippets collected!")
    
    return results


def process_and_clean_data(**context):
    """Clean and deduplicate collected data"""
    import sys
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # This would call your data processing script
    # For now, we'll create a placeholder
    
    print("=" * 60)
    print("Processing and cleaning data...")
    print("=" * 60)
    
    # TODO: Implement actual processing
    # from src.etl.data_processor import DataProcessor
    # processor = DataProcessor()
    # processor.process_all()
    
    results = {
        'status': 'processed',
        'clean_snippets': 0,  # Will be updated when processor is implemented
    }
    
    context['ti'].xcom_push(key='processing_results', value=results)
    
    print("✅ Processing complete!")
    return results


def generate_collection_report(**context):
    """Generate summary report of collection"""
    from pathlib import Path
    import json
    from datetime import datetime
    
    # Get results from previous tasks
    ti = context['ti']
    validation = ti.xcom_pull(key='validation_results', task_ids='validate_data')
    processing = ti.xcom_pull(key='processing_results', task_ids='process_data')
    
    report = {
        'dag_run_id': context['dag_run'].run_id,
        'execution_date': context['execution_date'].isoformat(),
        'collection': validation,
        'processing': processing,
        'timestamp': datetime.now().isoformat()
    }
    
    # Save report
    report_dir = Path("data/raw/github_expanded")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = report_dir / f"dag_report_{context['ds']}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Report saved to {report_file}")
    return report


def send_success_notification(**context):
    """Send success notification"""
    ti = context['ti']
    validation = ti.xcom_pull(key='validation_results', task_ids='validate_data')
    
    message = f"""
    ✅ GitHub Data Collection DAG Completed Successfully!
    
    Run ID: {context['dag_run'].run_id}
    Execution Date: {context['execution_date']}
    
    Results:
    - Files Collected: {validation['total_files']}
    - Snippets Collected: {validation['total_snippets']}
    - Average per File: {validation['average_per_file']:.1f}
    
    Next: Run embedding generation DAG
    """
    
    print(message)
    # TODO: Send email or Slack notification
    return 'success'


# Define tasks
check_token = PythonOperator(
    task_id='check_github_token',
    python_callable=check_github_token,
    dag=dag,
)

collect_repos = PythonOperator(
    task_id='collect_github_repos',
    python_callable=collect_github_repos,
    dag=dag,
)

validate_data = PythonOperator(
    task_id='validate_data',
    python_callable=validate_collected_data,
    dag=dag,
)

process_data = PythonOperator(
    task_id='process_data',
    python_callable=process_and_clean_data,
    dag=dag,
)

generate_report = PythonOperator(
    task_id='generate_report',
    python_callable=generate_collection_report,
    dag=dag,
)

send_notification = PythonOperator(
    task_id='send_notification',
    python_callable=send_success_notification,
    dag=dag,
)

# Define task dependencies
check_token >> collect_repos >> validate_data >> process_data >> generate_report >> send_notification

# Optional: Add parallel data quality checks
with TaskGroup('data_quality_checks', dag=dag) as quality_checks:
    
    check_syntax = BashOperator(
        task_id='check_code_syntax',
        bash_command='echo "Checking code syntax..."',
    )
    
    check_duplicates = BashOperator(
        task_id='check_duplicates',
        bash_command='echo "Checking for duplicates..."',
    )
    
    check_quality = BashOperator(
        task_id='check_quality_scores',
        bash_command='echo "Checking quality scores..."',
    )
    
    # Run quality checks in parallel
    [check_syntax, check_duplicates, check_quality]

# Add quality checks after validation
validate_data >> quality_checks >> process_data
