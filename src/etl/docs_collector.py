#!/usr/bin/env python3
"""
Official Documentation Collector

Scrapes code examples from official framework documentation.

Target: 1K-2K examples from official docs
"""

import os
import json
import time
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocsCollector:
    """
    Official documentation collector
    
    Scrapes code examples from:
    - FastAPI docs
    - Flask docs
    - Django docs
    - Express.js docs
    """
    
    def __init__(self):
        self.output_dir = Path("data/raw/documentation")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Documentation sources
        self.sources = {
            "fastapi": {
                "base_url": "https://fastapi.tiangolo.com",
                "pages": [
                    "/tutorial/first-steps/",
                    "/tutorial/path-params/",
                    "/tutorial/query-params/",
                    "/tutorial/body/",
                    "/tutorial/security/",
                    "/tutorial/dependencies/",
                    "/tutorial/sql-databases/",
                    "/tutorial/bigger-applications/",
                    "/advanced/security/",
                    "/advanced/custom-response/",
                ],
                "language": "python",
                "framework": "fastapi"
            },
            "flask": {
                "base_url": "https://flask.palletsprojects.com/en/latest",
                "pages": [
                    "/quickstart/",
                    "/tutorial/",
                    "/patterns/appfactories/",
                    "/patterns/sqlalchemy/",
                    "/patterns/fileuploads/",
                ],
                "language": "python",
                "framework": "flask"
            },
            "django": {
                "base_url": "https://docs.djangoproject.com/en/stable",
                "pages": [
                    "/intro/tutorial01/",
                    "/intro/tutorial02/",
                    "/topics/auth/",
                    "/topics/db/models/",
                    "/topics/http/views/",
                ],
                "language": "python",
                "framework": "django"
            },
            "express": {
                "base_url": "https://expressjs.com",
                "pages": [
                    "/en/starter/hello-world.html",
                    "/en/starter/basic-routing.html",
                    "/en/guide/routing.html",
                    "/en/guide/using-middleware.html",
                    "/en/guide/error-handling.html",
                ],
                "language": "javascript",
                "framework": "express"
            }
        }
    
    def scrape_page(self, url: str) -> List[str]:
        """
        Scrape code examples from a documentation page
        
        Args:
            url: URL to scrape
            
        Returns:
            List of code snippets
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find code blocks (common patterns in documentation)
            code_blocks = []
            
            # Method 1: <pre><code> blocks
            for pre in soup.find_all('pre'):
                code = pre.find('code')
                if code:
                    text = code.get_text().strip()
                    if len(text) > 50:  # Filter short snippets
                        code_blocks.append(text)
            
            # Method 2: Direct <code> blocks with class
            for code in soup.find_all('code', class_=re.compile(r'language-|highlight')):
                text = code.get_text().strip()
                if len(text) > 50:
                    code_blocks.append(text)
            
            # Method 3: Markdown-style code blocks
            for div in soup.find_all('div', class_=re.compile(r'code|highlight|example')):
                text = div.get_text().strip()
                if len(text) > 50 and len(text) < 2000:
                    code_blocks.append(text)
            
            logger.info(f"  Found {len(code_blocks)} code blocks")
            return code_blocks
            
        except Exception as e:
            logger.error(f"  Error scraping {url}: {e}")
            return []
    
    def collect_framework(self, framework: str):
        """
        Collect documentation for a specific framework
        
        Args:
            framework: Framework name (fastapi, flask, etc.)
        """
        if framework not in self.sources:
            logger.error(f"Unknown framework: {framework}")
            return []
        
        source = self.sources[framework]
        logger.info(f"Collecting {framework} documentation...")
        logger.info(f"  Base URL: {source['base_url']}")
        logger.info(f"  Pages: {len(source['pages'])}")
        
        all_snippets = []
        
        for page in source['pages']:
            url = source['base_url'] + page
            logger.info(f"  Scraping: {page}")
            
            snippets = self.scrape_page(url)
            
            # Add metadata to each snippet
            for snippet in snippets:
                all_snippets.append({
                    "code": snippet,
                    "language": source["language"],
                    "framework": source["framework"],
                    "source": f"docs:{framework}",
                    "url": url,
                    "page": page,
                    "timestamp": datetime.now().isoformat()
                })
            
            time.sleep(1)  # Be respectful to servers
        
        # Save to file
        output_file = self.output_dir / f"{framework}_docs.jsonl"
        with open(output_file, 'w') as f:
            for snippet in all_snippets:
                f.write(json.dumps(snippet) + '\n')
        
        logger.info(f"✅ Collected {len(all_snippets)} snippets from {framework} docs")
        return all_snippets
    
    def collect_all(self):
        """Collect from all documentation sources"""
        
        logger.info("=" * 60)
        logger.info("OFFICIAL DOCUMENTATION COLLECTION")
        logger.info("=" * 60)
        logger.info(f"Frameworks: {list(self.sources.keys())}")
        logger.info("")
        
        total_snippets = 0
        results = {}
        
        for framework in self.sources.keys():
            try:
                snippets = self.collect_framework(framework)
                results[framework] = len(snippets)
                total_snippets += len(snippets)
            except Exception as e:
                logger.error(f"❌ Error collecting {framework}: {e}")
                results[framework] = 0
        
        # Create summary report
        report = {
            "collection_summary": {
                "total_frameworks": len(self.sources),
                "total_snippets": total_snippets,
                "average_snippets_per_framework": total_snippets / len(self.sources),
                "timestamp": datetime.now().isoformat()
            },
            "per_framework": results,
            "sources": {
                name: {
                    "base_url": info["base_url"],
                    "pages_count": len(info["pages"])
                }
                for name, info in self.sources.items()
            }
        }
        
        report_file = self.output_dir / "collection_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("COLLECTION COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"✅ Total snippets: {total_snippets}")
        logger.info(f"✅ Report saved to: {report_file}")
        
        for framework, count in results.items():
            logger.info(f"   {framework}: {count} snippets")
        
        logger.info("=" * 60)


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print(" " * 15 + "DOCUMENTATION COLLECTOR")
    print("=" * 70)
    
    collector = DocsCollector()
    collector.collect_all()


if __name__ == "__main__":
    main()
