"""
AI Codegen Ingestion DAG - Fixed Import Version
"""

from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator  # 修复导入
from pathlib import Path
import sys

# ============================================================
# Add src/ to Python path
# ============================================================

BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
sys.path.insert(0, str(SRC_DIR))


# ============================================================
# Import your pipeline modules (fixed)
# ============================================================

# GitHub ETL
try:
    from etl.github_collect import collect_repo
except ImportError as e:
    print(f"Warning: Could not import github_collect: {e}")
    collect_repo = None

# AST Parser
try:
    from processing.ast_parser import parse_multiple_repos
except ImportError as e:
    print(f"Warning: Could not import ast_parser: {e}")
    parse_multiple_repos = None

# Code cleaning (correct function name)
try:
    from processing.code_cleaner import clean_snippet_corpus
except ImportError as e:
    print(f"Warning: Could not import code_cleaner: {e}")
    clean_snippet_corpus = None

# Snippet Builder
try:
    from processing.snippet_builder import build_snippet_corpus
except ImportError as e:
    print(f"Warning: Could not import snippet_builder: {e}")
    build_snippet_corpus = None

# Embeddings
try:
    from embeddings.embed_pipeline import run_embedding_pipeline
except ImportError as e:
    print(f"Warning: Could not import embed_pipeline: {e}")
    run_embedding_pipeline = None

# RAG Test
try:
    from rag.rag_pipeline import run_rag_test
except ImportError as e:
    print(f"Warning: Could not import rag_pipeline: {e}")
    run_rag_test = None


# ============================================================
# Wrapper tasks for Airflow
# ============================================================

def task_collect_repo(**context):
    raw_dir = DATA_DIR / "raw"
    raw_dir.mkdir(exist_ok=True, parents=True)
    if collect_repo:
        collect_repo(str(raw_dir))
        print("✓ GitHub repo collection completed.")
    else:
        print("⚠ Skipping: collect_repo not available")


def task_run_ast(**context):
    if parse_multiple_repos:
        parse_multiple_repos()
        print("✓ AST parsing completed.")
    else:
        print("⚠ Skipping: parse_multiple_repos not available")


def task_clean_code(**context):
    if clean_snippet_corpus:
        clean_snippet_corpus()
        print("✓ Code cleaning completed.")
    else:
        print("⚠ Skipping: clean_snippet_corpus not available")


def task_build_snippets(**context):
    if build_snippet_corpus:
        build_snippet_corpus()
        print("✓ Final snippet corpus built.")
    else:
        print("⚠ Skipping: build_snippet_corpus not available")


def task_run_embeddings(**context):
    if run_embedding_pipeline:
        run_embedding_pipeline()
        print("✓ Embedding pipeline completed.")
    else:
        print("⚠ Skipping: run_embedding_pipeline not available")


def task_run_rag(**context):
    if run_rag_test:
        run_rag_test()
        print("✓ RAG retrieval test completed.")
    else:
        print("⚠ Skipping: run_rag_test not available")


# ============================================================
# DAG Definition
# ============================================================

with DAG(
    dag_id="ai_codegen_ingest_dag",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@once",  # 使用 schedule_interval 而不是 schedule
    catchup=False,
    tags=["etl", "rag", "embeddings", "ai-codegen"],
) as dag:

    t1 = PythonOperator(
        task_id="collect_repo",
        python_callable=task_collect_repo,
    )

    t2 = PythonOperator(
        task_id="run_ast",
        python_callable=task_run_ast,
    )

    t3 = PythonOperator(
        task_id="clean_code",
        python_callable=task_clean_code,
    )

    t4 = PythonOperator(
        task_id="build_snippets",
        python_callable=task_build_snippets,
    )

    t5 = PythonOperator(
        task_id="run_embeddings",
        python_callable=task_run_embeddings,
    )

    t6 = PythonOperator(
        task_id="run_rag",
        python_callable=task_run_rag,
    )

    # Task order
    t1 >> t2 >> t3 >> t4 >> t5 >> t6
