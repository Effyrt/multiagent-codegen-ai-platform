"""
code_cleaner.py
Cleans AST-extracted code snippets and extracts imports.
Supports batch cleaning of JSONL corpus and exporting results.
"""

import ast
import re
import json
from pathlib import Path


# ============================================================
# Extract import statements
# ============================================================

def extract_imports(code: str):
    """
    Extract import statements using AST.
    """
    imports = []
    try:
        tree = ast.parse(code)
    except Exception:
        return []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"from {module} import {alias.name}")

    return imports


# ============================================================
# Clean code (remove comments + blank lines)
# ============================================================

def clean_code(code: str):
    """
    Remove comments, excessive blank lines, strip whitespace.
    """
    code = re.sub(r"#.*", "", code)
    code = code.replace("\r\n", "\n")

    cleaned_lines = []
    prev_blank = False
    for line in code.split("\n"):
        stripped = line.strip()
        if stripped == "":
            if prev_blank:
                continue
            prev_blank = True
            cleaned_lines.append("")
        else:
            prev_blank = False
            cleaned_lines.append(line.rstrip())

    cleaned = "\n".join(cleaned_lines).strip()
    return cleaned


# ============================================================
# Batch Clean AST Snippet Corpus
# ============================================================

def clean_snippet_corpus(
    input_path="data/processed/ast/snippets_ast.jsonl",
    output_path="data/processed/cleaned/cleaned_snippets.jsonl"
):
    """
    Read AST snippets → clean code → extract imports → export cleaned corpus.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"❌ AST snippet file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cleaned_items = []

    print(f"\n📥 Loading AST snippets from: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"🔍 Total snippets loaded: {len(lines)}")

    for idx, line in enumerate(lines):
        obj = json.loads(line)

        raw_code = obj.get("code", "")

        cleaned = clean_code(raw_code)
        imports = extract_imports(cleaned)

        # Store results inside snippet object
        obj["cleaned_code"] = cleaned
        obj["imports"] = imports

        cleaned_items.append(obj)

        if idx % 500 == 0:
            print(f"  → Processed {idx} snippets...")

    # Export cleaned corpus
    with open(output_path, "w", encoding="utf-8") as f:
        for item in cleaned_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\n✅ Cleaned snippets saved → {output_path}")
    print(f"🧹 Total cleaned snippets: {len(cleaned_items)}")

    return cleaned_items



# ============================================================
# Wrapper for Unified DAG Compatibility
# ============================================================

def clean_all_snippets():
    """
    Unified DAG expects this function name clean_snippet_corpus().
    """
    print("[Wrapper] clean_all_snippets() → calling clean_snippet_corpus()")
    return clean_snippet_corpus()


# ============================================================
# CLI TESTING BLOCK
# ============================================================

if __name__ == "__main__":
    print("\n🔧 Running batch cleaning on AST output...\n")

    clean_snippet_corpus()

    print("\n🎉 Cleaning pipeline completed successfully!\n")
