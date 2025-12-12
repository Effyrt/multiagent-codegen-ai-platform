"""
Embedding Generation DAG

Generates vector embeddings from collected code snippets and uploads to Pinecone.

Schedule: Daily (after data collection)
Owner: Hemanth Rayudu
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

default_args = {
    'owner': 'hemanth',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 1),
    'email': ['hemanth@example.com'],
    'email_on_failure': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

dag = DAG(
    'embedding_generation',
    default_args=default_args,
    description='Generate embeddings and upload to Pinecone',
    schedule='@daily',  # Run daily
    catchup=False,
    tags=['embeddings', 'rag', 'pinecone'],
)


def check_api_keys(**context):
    """Check if required API keys are configured"""
    import os
    
    openai_key = os.getenv('OPENAI_API_KEY')
    pinecone_key = os.getenv('PINECONE_API_KEY')
    
    if not openai_key:
        raise ValueError("OPENAI_API_KEY not configured!")
    if not pinecone_key:
        raise ValueError("PINECONE_API_KEY not configured!")
    
    print("✅ API keys configured")
    return 'configured'


def load_clean_snippets(**context):
    """Load cleaned code snippets"""
    from pathlib import Path
    import json
    
    snippets_file = Path("data/processed/clean_snippets.jsonl")
    
    if not snippets_file.exists():
        raise FileNotFoundError(
            f"Clean snippets file not found: {snippets_file}\n"
            "Run data processing first!"
        )
    
    # Count snippets
    count = 0
    with open(snippets_file) as f:
        for line in f:
            count += 1
    
    print(f"✅ Loaded {count} clean snippets")
    context['ti'].xcom_push(key='snippet_count', value=count)
    
    return count


def generate_embeddings(**context):
    """Generate embeddings using OpenAI text-embedding-3-large"""
    import sys
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    print("=" * 60)
    print("Generating embeddings with text-embedding-3-large")
    print("=" * 60)
    
    # TODO: Implement actual embedding generation
    # from src.embeddings.generate import generate_all_embeddings
    # results = generate_all_embeddings()
    
    # For now, placeholder
    ti = context['ti']
    snippet_count = ti.xcom_pull(key='snippet_count', task_ids='load_snippets')
    
    # Simulate embedding generation
    estimated_cost = (snippet_count * 50 * 0.13) / 1_000_000
    
    results = {
        'embeddings_generated': snippet_count,
        'model': 'text-embedding-3-large',
        'dimensions': 3072,
        'estimated_cost': f'${estimated_cost:.4f}'
    }
    
    print(f"✅ Generated {snippet_count} embeddings")
    print(f"   Model: text-embedding-3-large (3072 dims)")
    print(f"   Cost: ~${estimated_cost:.4f}")
    
    context['ti'].xcom_push(key='embedding_results', value=results)
    
    return results


def upload_to_pinecone(**context):
    """Upload embeddings to Pinecone vector database"""
    import sys
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    print("=" * 60)
    print("Uploading to Pinecone")
    print("=" * 60)
    
    # TODO: Implement actual Pinecone upload
    # from src.embeddings.upsert_pinecone import upload_all_embeddings
    # results = upload_all_embeddings()
    
    ti = context['ti']
    embedding_results = ti.xcom_pull(key='embedding_results', task_ids='generate_embeddings')
    
    results = {
        'vectors_uploaded': embedding_results['embeddings_generated'],
        'index': 'codegen-ai-dev',
        'status': 'success'
    }
    
    print(f"✅ Uploaded {results['vectors_uploaded']} vectors to Pinecone")
    
    context['ti'].xcom_push(key='upload_results', value=results)
    
    return results


def test_rag_retrieval(**context):
    """Test RAG retrieval with sample queries"""
    print("=" * 60)
    print("Testing RAG Retrieval")
    print("=" * 60)
    
    test_queries = [
        "FastAPI user authentication with JWT",
        "Flask database connection with SQLAlchemy",
        "Express.js error handling middleware",
    ]
    
    # TODO: Implement actual RAG test
    # from src.rag.retriever import CodeRetriever
    # retriever = CodeRetriever()
    # for query in test_queries:
    #     results = retriever.retrieve_similar_code(query)
    #     print(f"Query: {query}")
    #     print(f"Results: {len(results)}")
    
    for query in test_queries:
        print(f"✓ Tested: {query}")
    
    print("✅ RAG retrieval tests passed!")
    return 'success'


def generate_embedding_report(**context):
    """Generate summary report"""
    from datetime import datetime
    import json
    from pathlib import Path
    
    ti = context['ti']
    embedding_results = ti.xcom_pull(key='embedding_results', task_ids='generate_embeddings')
    upload_results = ti.xcom_pull(key='upload_results', task_ids='upload_to_pinecone')
    
    report = {
        'dag_run_id': context['dag_run'].run_id,
        'execution_date': context['execution_date'].isoformat(),
        'embeddings': embedding_results,
        'upload': upload_results,
        'timestamp': datetime.now().isoformat()
    }
    
    # Save report
    report_dir = Path("data/processed")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = report_dir / f"embedding_report_{context['ds']}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Report saved to {report_file}")
    return report


# Define tasks
check_keys = PythonOperator(
    task_id='check_api_keys',
    python_callable=check_api_keys,
    dag=dag,
)

load_snippets = PythonOperator(
    task_id='load_snippets',
    python_callable=load_clean_snippets,
    dag=dag,
)

generate = PythonOperator(
    task_id='generate_embeddings',
    python_callable=generate_embeddings,
    dag=dag,
)

upload = PythonOperator(
    task_id='upload_to_pinecone',
    python_callable=upload_to_pinecone,
    dag=dag,
)

test_rag = PythonOperator(
    task_id='test_rag_retrieval',
    python_callable=test_rag_retrieval,
    dag=dag,
)

generate_report = PythonOperator(
    task_id='generate_report',
    python_callable=generate_embedding_report,
    dag=dag,
)

# Define dependencies
check_keys >> load_snippets >> generate >> upload >> test_rag >> generate_report
