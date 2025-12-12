#!/usr/bin/env python3
"""
Expanded GitHub Data Collector

Collects code snippets from curated GitHub repositories.
Generates tmp .py files for AST parsing.
"""

import sys
from pathlib import Path
SRC_PATH = str(Path(__file__).resolve().parents[1])
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

import os
import json
import logging
from datetime import datetime
import uuid

from parser.ast_adapter import wrap_snippet_as_py  # AST adapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExpandedGitHubCollector:
    def __init__(self, github_token: str = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.output_dir = Path("data/raw/github_expanded")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.snippet_idx = 0  

        self.repositories = self._get_repository_list()

    def _get_repository_list(self):

        return [
            {"owner": "tiangolo", "repo": "fastapi", "language": "python", "framework": "fastapi"},
            {"owner": "tiangolo", "repo": "sqlmodel", "language": "python", "framework": "sqlmodel"},
            {"owner": "encode", "repo": "httpx", "language": "python", "framework": "httpx"},

        ]

    def collect_all(self):
        logger.info("="*60)
        logger.info("EXPANDED GITHUB DATA COLLECTION")
        logger.info("="*60)
        logger.info(f"Target repositories: {len(self.repositories)}")
        logger.info(f"Output directory: {self.output_dir}")

        if not self.github_token:
            logger.warning("⚠️ No GitHub token provided. Using MOCK data collection...")
            self._collect_mock_snippets()
            self._create_mock_report()
            return

        # TODO: Implement actual GitHub API collection
        # This would use PyGitHub or direct API calls

    def _collect_mock_snippets(self):
        """生成 mock snippet 並寫入 tmp .py"""
        for repo in self.repositories[:3]:  
            for i in range(5):  
                code = f"# Example snippet {i} from {repo['repo']}\ndef example_func():\n    pass\n"
                filepath = wrap_snippet_as_py(
                    code=code,
                    source=f"github_{repo['repo']}",
                    idx=self.snippet_idx
                )
                self.snippet_idx += 1
                logger.info(f"Saved tmp snippet: {filepath}, length={len(code)}")

    def _create_mock_report(self):
        report = {
            "collection_plan": {
                "total_repositories": len(self.repositories),
                "target_snippets": 100 
            },
            "repositories": self.repositories,
            "timestamp": datetime.now().isoformat()
        }
        output_file = self.output_dir / "COLLECTION_PLAN.json"
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"📝 Collection plan saved to: {output_file}")

    #  GitHub API
    # def _collect_repo_snippets(self, repo):
    #     pass

def main():
    print("\n" + "="*70)
    print(" " * 15 + "EXPANDED GITHUB DATA COLLECTOR")
    print("="*70)
    collector = ExpandedGitHubCollector()
    collector.collect_all()

if __name__ == "__main__":
    main()
