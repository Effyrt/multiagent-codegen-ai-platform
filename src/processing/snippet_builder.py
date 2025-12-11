"""
snippet_builder.py
Builds the final RAG snippet corpus from cleaned snippets.
Ensures schema compliance and exports to final JSONL output.
"""

import json
import uuid
from pathlib import Path
import ast   


# ============================================================
# 🔧 Complexity function
# ============================================================

def compute_cyclomatic_complexity(code: str) -> int:
    """
    Compute cyclomatic complexity using AST.
    Complexity increases with branching statements.
    """
    if not code or not isinstance(code, str):
        return 1

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 1  # return minimal complexity if code is broken

    complexity = 1  # baseline

    for node in ast.walk(tree):
        if isinstance(node, (
            ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler,
            ast.With, ast.And, ast.Or, ast.BoolOp, ast.comprehension
        )):
            complexity += 1

    return complexity


# ============================================================
# Load JSONL helper
# ============================================================

def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


# ============================================================
# Validate snippet (you can adjust rules)
# ============================================================

def validate_snippet(snip):
    if not snip.get("cleaned_code"):
        return False
    if snip.get("type") not in ["class", "function", "method"]:
        return False
    return True


# ============================================================
# Convert cleaned snippet → final schema
# ============================================================

def build_final_snippet(snip):
    code = snip.get("cleaned_code", "")

    return {
        "snippet_id": str(uuid.uuid4()),
        "repo": snip.get("repo"),
        "file_path": snip.get("file_path"),

        "language": snip.get("language"),
        "framework": snip.get("framework"),

        "type": snip.get("type"),
        "func_name": snip.get("func_name"),
        "class_name": snip.get("class_name"),

        "code": code,     # <-- schema requires `code`
        "imports": snip.get("imports", []),

        # 🔧 新增：真正計算 complexity，而不是預設 1.0
        "complexity": float(compute_cyclomatic_complexity(code)),
    }


# ============================================================
# Main builder
# ============================================================

def build_snippet_corpus(
    cleaned_path="data/processed/cleaned/cleaned_snippets.jsonl",
    output_path="data/processed/final_snippets/snippets_final.jsonl"
):

    cleaned_snippets = load_jsonl(cleaned_path)

    print(f"📥 Loaded cleaned snippets: {len(cleaned_snippets)}")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    final_snippets = []

    for snip in cleaned_snippets:
        if not validate_snippet(snip):
            continue

        final_snippets.append(build_final_snippet(snip))

    print(f"✅ Valid final snippets: {len(final_snippets)}")

    # Export to JSONL
    with open(output_path, "w", encoding="utf-8") as f:
        for sn in final_snippets:
            f.write(json.dumps(sn, ensure_ascii=False) + "\n")

    print(f"🎉 Final RAG snippet corpus saved → {output_path}")

    return final_snippets


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    build_snippet_corpus()