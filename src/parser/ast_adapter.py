import uuid
from pathlib import Path

TMP_AST_DIR = Path("data/tmp/ast_inputs")
TMP_AST_DIR.mkdir(parents=True, exist_ok=True)


def wrap_snippet_as_py(code: str, source: str, idx: int) -> Path:
    """
    Wrap arbitrary code snippet into a minimal valid Python file
    so that ast.parse() can consume it.
    """
    file_id = f"{source}_{idx}_{uuid.uuid4().hex[:6]}"
    file_path = TMP_AST_DIR / f"{file_id}.py"

    wrapped_code = f'''"""
Source: {source}
"""

{code}
'''

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(wrapped_code)

    return file_path
