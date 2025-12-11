"""
AI Codegen Ingestion DAG - Clean Import Path Version (FIXED)
"""

from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from pathlib import Path
import sys

# ===========================
# Fix Python import path
# ===========================
SRC_PATH = "/opt/airflow/src"

if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

print("[DAG] Python sys.path updated with:", SRC_PATH)

# ===========================
# Paths
# ===========================
DAGS_DIR = Path(__file__).parent
PROJECT_ROOT = DAGS_DIR.parent
#SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"      # ⭐ FIX #1: 定義 RAW_DIR
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Make modules importable inside container
#sys.path.insert(0, "/opt/airflow/src")
#sys.path.insert(0, str(SRC_DIR))

repo_url = "https://github.com/openai/openai-python.git"
branch = "main"

# ===========================
# Module imports
# ===========================
try:
    from etl.github_collect import collect_repo
except:
    collect_repo = None

try:
    from processing.ast_parser import parse_multiple_repos
except:
    parse_multiple_repos = None

try:
    from processing.code_cleaner import clean_snippet_corpus
except:
    clean_snippet_corpus = None

try:
    from processing.snippet_builder import build_snippet_corpus
except:
    build_snippet_corpus = None

try:
    from embeddings.embed_pipeline import run_embedding_pipeline
except Exception as e:
    print("IMPORT ERROR: Cannot load run_embedding_pipeline:", e)
    raise   

try:
    from rag.rag_pipeline import run_rag_test
except:
    run_rag_test = None


# ===========================
# Wrapper task functions
# ===========================

#def task_collect_repo_wrapper(**context):  # ⭐ FIX #2: 正確 wrapper
#    if collect_repo:
#        collect_repo(
#            repo="openai/openai-python",
#            output_dir=str(RAW_DIR)
#        )
#        print("✓ Repo collected →", RAW_DIR)
#    else:
#        print("⚠ collect_repo missing")

def task_collect_repo_wrapper(**context):
    repo_path = collect_repo(
        owner="openai",
        repo="openai-python",
        branch="main",
        out_dir=str(RAW_DIR)
    )
    print("✓ Repo collected →", repo_path)
    return repo_path   





#def task_run_ast(**context):
#    if parse_multiple_repos:
#        parse_multiple_repos()
#    else:
#        print("⚠ AST parser missing")


def task_run_ast(**context):
    repo_path = context["ti"].xcom_pull(task_ids="collect_repo")

    # ⭐ parse AST
    items = parse_multiple_repos([repo_path])

    # ⭐ save jsonl to processed folder
    from processing.ast_parser import save_jsonl
    OUTPUT_AST_DIR = PROJECT_ROOT / "data" / "processed" / "ast"

    save_jsonl(items, OUTPUT_AST_DIR)

    print("✓ AST parsing completed →", OUTPUT_AST_DIR)



def task_clean_code(**context):
    if clean_snippet_corpus:
        clean_snippet_corpus()
    else:
        print("⚠ Code cleaner missing")


def task_build_snippets(**context):
    if build_snippet_corpus:
        build_snippet_corpus()
    else:
        print("⚠ Snippet builder missing")


def task_run_embeddings(**context):
    if run_embedding_pipeline:
        run_embedding_pipeline()
    else:
        print("⚠ Embedding pipeline missing")


def task_run_rag(**context):
    if run_rag_test:
        run_rag_test()
    else:
        print("⚠ RAG test missing")


# ===========================
# DAG Definition
# ===========================

with DAG(
    dag_id="ai_codegen_ingest_dag",
    start_date=datetime(2025, 1, 1),
    schedule="@once",  # ⭐ FIX #3: 正確寫法
    catchup=False,
    is_paused_upon_creation=False,
    tags=["etl", "rag", "embeddings"],
) as dag:

    t1 = PythonOperator(
        task_id="collect_repo",
        python_callable=task_collect_repo_wrapper,  # ⭐ FIX #4
    )

    t2 = PythonOperator(task_id="run_ast", python_callable=task_run_ast)
    t3 = PythonOperator(task_id="clean_code", python_callable=task_clean_code)
    t4 = PythonOperator(task_id="build_snippets", python_callable=task_build_snippets)
    t5 = PythonOperator(task_id="run_embeddings", python_callable=task_run_embeddings)
    t6 = PythonOperator(task_id="run_rag", python_callable=task_run_rag)

    t1 >> t2 >> t3 >> t4 >> t5 >> t6
