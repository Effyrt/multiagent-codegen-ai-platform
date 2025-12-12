"""
AI Codegen Ingestion DAG - Clean Import Path Version (FIXED)
"""

from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from pathlib import Path
import sys
from etl.bigquery_utils import insert_rows



# ===========================
# Fix Python import path
# ===========================
SRC_PATH = "/opt/airflow/src"

if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)



print("[DAG] Python sys.path updated with:", SRC_PATH)

from rag.retriever import retrieve_similar_code
# ===========================
# Paths
# ===========================
DAGS_DIR = Path(__file__).parent
PROJECT_ROOT = DAGS_DIR.parent
#SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"      
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

#def task_collect_repo_wrapper(**context): 
#    if collect_repo:
#        collect_repo(
#            repo="openai/openai-python",
#            output_dir=str(RAW_DIR)
#        )
#        print("✓ Repo collected →", RAW_DIR)
#    else:
#        print("⚠ collect_repo missing")

def task_collect_repo_wrapper(**context):
    """Collect all three sources locally"""
    collected_paths = {}

    # 1️⃣ GitHub
    try:
        from etl.github_collector_expanded import main as github_main
        print("🚀 Collecting GitHub repo...")
        github_main()
        collected_paths["github"] = "data/raw/github_expanded"
        print("✓ GitHub collection done")
    except Exception as e:
        print("⚠ GitHub collection failed:", e)

    # 2️⃣ StackOverflow
    try:
        from etl.stackoverflow_collector import main as so_main
        print("🚀 Collecting StackOverflow data...")
        so_main()
        collected_paths["stackoverflow"] = "data/tmp/ast_inputs"  
        print("✓ StackOverflow collection done")
    except Exception as e:
        print("⚠ StackOverflow collection failed:", e)

    # 3️⃣ Docs
    try:
        from etl.docs_collector import main as docs_main
        print("🚀 Collecting Documentation snippets...")
        docs_main()
        collected_paths["docs"] = "data/tmp/ast_inputs"  
        print("✓ Docs collection done")
    except Exception as e:
        print("⚠ Docs collection failed:", e)

    return collected_paths  





#def task_run_ast(**context):
#    if parse_multiple_repos:
#        parse_multiple_repos()
#    else:
#        print("⚠ AST parser missing")


def task_run_ast(**context):
    
    repo_path = context["ti"].xcom_pull(task_ids="collect_all_sources")

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


#def task_run_rag(**context):
#    if run_rag_test:
#        output_path = str(DATA_DIR / "rag_outputs" / "rag_from_dag.json")
#
#        result = run_rag_test(
#            query="How to create a dataset?",
#            output_path=output_path
#        )

#        print("✓ RAG executed successfully. Output saved to:", output_path)
#        return result

#    else:
#        print("⚠ RAG test missing")


def task_run_rag(**context):
    if retrieve_similar_code is None:
        print("⚠ Retriever module missing")
        return
    
    print("🚀 Running Code Retriever from DAG...")

    results = retrieve_similar_code(
        query="How to create a dataset?",
        top_k=3,
        language="python",
        framework="fastapi"
    )

    output_path = DATA_DIR / "rag_outputs" / "rag_output.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    import json
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("✓ Retriever finished. Output saved to:", output_path)
    return results



def task_load_bigquery(**context):
    from processing.snippet_builder import get_final_snippets  
    from google.cloud import bigquery

    client = bigquery.Client()

    try:
        all_snippets = get_final_snippets()  
        print(f"🔹 Total snippets to insert: {len(all_snippets)}")
    except Exception as e:
        print("⚠ Failed to get final snippets:", e)
        return


    table_mapping = {
        "dag_metadata": [],
        "snippet_summary": [],
        "token_usage": []
    }

    for snippet in all_snippets:
        table_mapping["dag_metadata"].append({
            "dag_id": snippet.get("dag_id", ""),
            "timestamp": snippet.get("timestamp", "")
        })
        table_mapping["snippet_summary"].append({
            "snippet_id": snippet.get("snippet_id", ""),
            "language": snippet.get("language", ""),
            "framework": snippet.get("framework", ""),
            "complexity": snippet.get("complexity", 0),
            "score": snippet.get("score", 0)
        })
        table_mapping["token_usage"].append({
            "snippet_id": snippet.get("snippet_id", ""),
            "tokens": snippet.get("tokens", 0)
        })


    project = "potent-poet-480804-s4"
    dataset = "codegen_analytics"

    for table_name, rows in table_mapping.items():
        if not rows:
            print(f"⚠ No rows to insert for {table_name}")
            continue

        table_id = f"{project}.{dataset}.{table_name}"
        try:
            errors = client.insert_rows_json(table_id, rows)
            if errors:
                print(f"❌ Insert errors for {table_name}:", errors)
            else:
                print(f"✅ Inserted {len(rows)} rows into BigQuery table: {table_name}")
        except Exception as e:
            print(f"❌ Failed to insert into {table_name}:", e)



# ===========================
# DAG Definition
# ===========================

with DAG(
    dag_id="ai_codegen_ingest_dag",
    start_date=datetime(2025, 1, 1),
    schedule="@once",  
    catchup=False,
    is_paused_upon_creation=False,
    tags=["etl", "rag", "embeddings"],
) as dag:


    t1 = PythonOperator(task_id="collect_all_sources", python_callable=task_collect_repo_wrapper)
    t2 = PythonOperator(task_id="run_ast", python_callable=task_run_ast)
    t3 = PythonOperator(task_id="clean_code", python_callable=task_clean_code)
    t4 = PythonOperator(task_id="build_snippets", python_callable=task_build_snippets)
    t5 = PythonOperator(task_id="run_embeddings", python_callable=task_run_embeddings)
    t6 = PythonOperator(task_id="run_rag", python_callable=task_run_rag)
    t7 = PythonOperator(task_id="load_bigquery", python_callable=task_load_bigquery)

    t1 >> t2 >> t3 >> t4 >> t5 >> t6 >> t7
