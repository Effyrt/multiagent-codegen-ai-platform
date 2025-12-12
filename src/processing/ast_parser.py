"""
ast_parser.py
Parses multiple repositories and extracts functions/classes/methods
into a unified structure for snippet_builder. Outputs JSONL files for snippet_builder.
"""

import ast
import os
import json
from pathlib import Path


# ============================================================
# Detect language
# ============================================================

def detect_language(file_path: str):
    if file_path.endswith(".py"):
        return "python"
    return "unknown"


# ============================================================
# Detect framework
# ============================================================

def detect_framework(repo_name: str, source_code: str):
    repo_name = repo_name.lower()
    src = source_code.lower()

    if "fastapi" in repo_name or "fastapi" in src:
        return "fastapi"
    if "flask" in repo_name or "from flask" in src:
        return "flask"
    if "django" in repo_name or "django" in src:
        return "django"
    if "transformers" in repo_name or "from transformers" in src:
        return "transformers"
    if "pandas" in repo_name or "import pandas" in src:
        return "pandas"
    if "requests" in repo_name or "import requests" in src:
        return "requests"
    if "cpython" in repo_name:
        return "python-core"

    return "unknown"


# ============================================================
# Compute AST Complexity (Real Version)
# ============================================================

class ComplexityVisitor(ast.NodeVisitor):
    """
    Real AST-based complexity:
    - Each decision node (If, For, While, Try, BoolOp) increases score
    - Nested structures increase score more
    - Simple functions/classes get low score
    """
    def __init__(self):
        self.score = 1   # base complexity

    def generic_visit(self, node):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            self.score += 1

        if isinstance(node, ast.BoolOp):
            # a and b or c → more conditions = higher complexity
            self.score += len(node.values)

        super().generic_visit(node)


def compute_complexity(node):
    """Return a float complexity score for snippet."""
    visitor = ComplexityVisitor()
    visitor.visit(node)
    return float(visitor.score)


# ============================================================
# Extract AST items (function, class, methods)
# ============================================================

def parse_file(repo_name: str, file_path: str):
    """
    Parse a Python file and extract:
    - top-level functions
    - classes
    - methods inside classes
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except Exception as e:
        print(f"⚠️ AST parse failed for {file_path}: {e}")
        return []

    results = []
    language = detect_language(file_path)
    framework = detect_framework(repo_name, source)

    for node in ast.walk(tree):

        # ---------- Function ----------
        if isinstance(node, ast.FunctionDef):
            code = ast.get_source_segment(source, node)
            results.append({
                "repo": repo_name,
                "file_path": file_path,
                "type": "function",
                "func_name": node.name,
                "class_name": None,
                "code": code,
                "language": language,
                "framework": framework,
                "complexity": compute_complexity(node),
            })

        # ---------- Class ----------
        if isinstance(node, ast.ClassDef):
            class_code = ast.get_source_segment(source, node)

            # Save the class itself
            results.append({
                "repo": repo_name,
                "file_path": file_path,
                "type": "class",
                "func_name": None,
                "class_name": node.name,
                "code": class_code,
                "language": language,
                "framework": framework,
                "complexity": compute_complexity(node),
            })

            # Extract class methods
            for body_item in node.body:
                if isinstance(body_item, ast.FunctionDef):
                    method_code = ast.get_source_segment(source, body_item)
                    results.append({
                        "repo": repo_name,
                        "file_path": file_path,
                        "type": "method",
                        "func_name": body_item.name,
                        "class_name": node.name,
                        "code": method_code,
                        "language": language,
                        "framework": framework,
                        "complexity": compute_complexity(body_item),
                    })

    return results


# ============================================================
# Parse whole repository
# ============================================================

def parse_repo(repo_path: str):
    repo_name = os.path.basename(repo_path)
    items = []

    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                items.extend(parse_file(repo_name, full_path))

    return items


def parse_multiple_repos(repo_paths: list):
    all_items = []
    for repo in repo_paths:
        print(f"📦 Parsing repo: {repo}")
        all_items.extend(parse_repo(repo))
    return all_items



def parse_tmp_ast_inputs(tmp_dir="data/tmp/ast_inputs"):
    """
    Parse all .py snippet files generated from StackOverflow/Docs
    """
    items = []
    for py_file in Path(tmp_dir).glob("*.py"):
        items.extend(parse_file("external_snippet", str(py_file)))
    return items




# ============================================================
# Save to JSONL
# ============================================================

def save_jsonl(items, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "snippets_ast.jsonl"

    with open(output_path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ Saved {len(items)} AST snippets → {output_path}")


# ============================================================
# CLI Test
# ============================================================

if __name__ == "__main__":
    items = []

    #  StackOverflow + Docs snippet
    items.extend(parse_tmp_ast_inputs("data/tmp/ast_inputs"))

    print(f"🔍 Total parsed snippets: {len(items)}")
    save_jsonl(items, "data/processed/ast")
    print("🎉 AST parsing completed!")

