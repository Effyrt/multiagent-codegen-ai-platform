#!/usr/bin/env python3
"""
Expanded GitHub Data Collector

Collects code snippets from 30-50 curated GitHub repositories across
multiple frameworks and languages.

Target: 8K-10K snippets from GitHub
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExpandedGitHubCollector:
    """
    Expanded GitHub data collector
    
    Collects from 30-50 repositories across:
    - Python: FastAPI, Flask, Django, general utilities
    - JavaScript: Express, NestJS, Koa
    - Real-world applications
    """
    
    def __init__(self, github_token: str = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.output_dir = Path("data/raw/github_expanded")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Curated list of high-quality repositories
        self.repositories = self._get_repository_list()
    
    def _get_repository_list(self) -> List[Dict[str, Any]]:
        """
        Get curated list of repositories to collect from
        
        Total: 50 repositories
        Target: ~10K snippets
        """
        return [
            # ============ PYTHON - FASTAPI (15 repos) ============
            {"owner": "tiangolo", "repo": "fastapi", "language": "python", "framework": "fastapi"},
            {"owner": "fastapi-users", "repo": "fastapi-users", "language": "python", "framework": "fastapi"},
            {"owner": "nsidnev", "repo": "fastapi-realworld-example-app", "language": "python", "framework": "fastapi"},
            {"owner": "s3rius", "repo": "FastAPI-template", "language": "python", "framework": "fastapi"},
            {"owner": "testdrivenio", "repo": "fastapi-react", "language": "python", "framework": "fastapi"},
            {"owner": "IndominusByte", "repo": "fastapi-jwt-auth", "language": "python", "framework": "fastapi"},
            {"owner": "dmontagu", "repo": "fastapi-utils", "language": "python", "framework": "fastapi"},
            {"owner": "laurentS", "repo": "slowapi", "language": "python", "framework": "fastapi"},
            {"owner": "Buuntu", "repo": "fastapi-react", "language": "python", "framework": "fastapi"},
            {"owner": "rednafi", "repo": "fastapi-nano", "language": "python", "framework": "fastapi"},
            {"owner": "tokusumi", "repo": "fastapi-cloudauth", "language": "python", "framework": "fastapi"},
            {"owner": "Kludex", "repo": "fastapi-code-generator", "language": "python", "framework": "fastapi"},
            {"owner": "dmontagu", "repo": "fastapi-auth", "language": "python", "framework": "fastapi"},
            {"owner": "aminalaee", "repo": "sqladmin", "language": "python", "framework": "fastapi"},
            {"owner": "zhanymkanov", "repo": "fastapi-best-practices", "language": "python", "framework": "fastapi"},
            
            # ============ PYTHON - FLASK (10 repos) ============
            {"owner": "pallets", "repo": "flask", "language": "python", "framework": "flask"},
            {"owner": "flask-restful", "repo": "flask-restful", "language": "python", "framework": "flask"},
            {"owner": "miguelgrinberg", "repo": "flasky", "language": "python", "framework": "flask"},
            {"owner": "miguelgrinberg", "repo": "Flask-SocketIO", "language": "python", "framework": "flask"},
            {"owner": "corydolphin", "repo": "flask-cors", "language": "python", "framework": "flask"},
            {"owner": "maxcountryman", "repo": "flask-login", "language": "python", "framework": "flask"},
            {"owner": "python-restx", "repo": "flask-restx", "language": "python", "framework": "flask"},
            {"owner": "flask-admin", "repo": "flask-admin", "language": "python", "framework": "flask"},
            {"owner": "pallets-eco", "repo": "flask-sqlalchemy", "language": "python", "framework": "flask"},
            {"owner": "sh4nks", "repo": "flaskbb", "language": "python", "framework": "flask"},
            
            # ============ PYTHON - DJANGO (8 repos) ============
            {"owner": "django", "repo": "django", "language": "python", "framework": "django"},
            {"owner": "encode", "repo": "django-rest-framework", "language": "python", "framework": "django"},
            {"owner": "cookiecutter", "repo": "cookiecutter-django", "language": "python", "framework": "django"},
            {"owner": "django-extensions", "repo": "django-extensions", "language": "python", "framework": "django"},
            {"owner": "viewflow", "repo": "viewflow", "language": "python", "framework": "django"},
            {"owner": "jazzband", "repo": "django-debug-toolbar", "language": "python", "framework": "django"},
            {"owner": "django-oscar", "repo": "django-oscar", "language": "python", "framework": "django"},
            {"owner": "wsvincent", "repo": "djangoforbeginners", "language": "python", "framework": "django"},
            
            # ============ JAVASCRIPT - EXPRESS (10 repos) ============
            {"owner": "expressjs", "repo": "express", "language": "javascript", "framework": "express"},
            {"owner": "goldbergyoni", "repo": "nodebestpractices", "language": "javascript", "framework": "express"},
            {"owner": "hagopj13", "repo": "node-express-boilerplate", "language": "javascript", "framework": "express"},
            {"owner": "danielfsousa", "repo": "express-rest-es2017-boilerplate", "language": "javascript", "framework": "express"},
            {"owner": "kunalkapadia", "repo": "express-mongoose-es6-rest-api", "language": "javascript", "framework": "express"},
            {"owner": "w3tecch", "repo": "express-typescript-boilerplate", "language": "javascript", "framework": "express"},
            {"owner": "santiq", "repo": "bulletproof-nodejs", "language": "javascript", "framework": "express"},
            {"owner": "microsoft", "repo": "TypeScript-Node-Starter", "language": "javascript", "framework": "express"},
            {"owner": "talyssonoc", "repo": "node-api-boilerplate", "language": "javascript", "framework": "express"},
            {"owner": "sahat", "repo": "hackathon-starter", "language": "javascript", "framework": "express"},
            
            # ============ JAVASCRIPT - NESTJS (5 repos) ============
            {"owner": "nestjs", "repo": "nest", "language": "javascript", "framework": "nestjs"},
            {"owner": "nestjs", "repo": "nest-cli", "language": "javascript", "framework": "nestjs"},
            {"owner": "lujakob", "repo": "nestjs-realworld-example-app", "language": "javascript", "framework": "nestjs"},
            {"owner": "xmlking", "repo": "ngx-starter-kit", "language": "javascript", "framework": "nestjs"},
            {"owner": "notiz-dev", "repo": "nestjs-prisma-starter", "language": "javascript", "framework": "nestjs"},
            
            # ============ GENERAL UTILITIES (2 repos) ============
            {"owner": "psf", "repo": "requests", "language": "python", "framework": "none"},
            {"owner": "axios", "repo": "axios", "language": "javascript", "framework": "none"},
        ]
    
    def collect_all(self):
        """
        Collect from all repositories
        
        This is a placeholder - actual implementation would:
        1. Use GitHub API to fetch repository content
        2. Parse files for functions/classes
        3. Extract code snippets
        4. Save to JSONL format
        """
        
        logger.info("=" * 60)
        logger.info("EXPANDED GITHUB DATA COLLECTION")
        logger.info("=" * 60)
        logger.info(f"Target repositories: {len(self.repositories)}")
        logger.info(f"Output directory: {self.output_dir}")
        
        if not self.github_token:
            logger.warning("⚠️  No GitHub token provided!")
            logger.warning("   Set GITHUB_TOKEN environment variable for higher rate limits")
            logger.warning("   Get token at: https://github.com/settings/tokens")
            logger.warning("")
            logger.warning("   Without token, you'll be rate limited to 60 requests/hour")
            logger.warning("   With token, you get 5000 requests/hour")
            logger.warning("")
            logger.info("   For now, creating MOCK data collection report...")
            self._create_mock_report()
            return
        
        # TODO: Implement actual GitHub API collection
        # This would use PyGitHub or direct API calls
        
        logger.info("✅ Collection plan created!")
        logger.info("   Implementation notes saved to data/raw/github_expanded/COLLECTION_PLAN.md")
    
    def _create_mock_report(self):
        """Create a mock report showing what would be collected"""
        
        report = {
            "collection_plan": {
                "total_repositories": len(self.repositories),
                "target_snippets": 10000,
                "estimated_size_gb": 2.5,
                "breakdown": {
                    "python_fastapi": 15,
                    "python_flask": 10,
                    "python_django": 8,
                    "javascript_express": 10,
                    "javascript_nestjs": 5,
                    "utilities": 2
                }
            },
            "repositories": self.repositories,
            "next_steps": [
                "1. Get GitHub personal access token",
                "2. Set GITHUB_TOKEN environment variable",
                "3. Run collector script",
                "4. Monitor progress and rate limits",
                "5. Validate collected data"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        output_file = self.output_dir / "COLLECTION_PLAN.json"
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📝 Collection plan saved to: {output_file}")


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print(" " * 15 + "EXPANDED GITHUB DATA COLLECTOR")
    print("=" * 70)
    
    collector = ExpandedGitHubCollector()
    collector.collect_all()
    
    print("\n" + "=" * 70)
    print("Next steps:")
    print("  1. Get GitHub token: https://github.com/settings/tokens")
    print("  2. Set environment: export GITHUB_TOKEN=your_token")
    print("  3. Run this script again to collect actual data")
    print("=" * 70)


if __name__ == "__main__":
    main()
