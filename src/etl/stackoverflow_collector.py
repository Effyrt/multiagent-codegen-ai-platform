#!/usr/bin/env python3
"""
Stack Overflow Data Collector

Collects code snippets from Stack Overflow questions and answers.

Target: 2K-5K Q&A pairs with code
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StackOverflowCollector:
    """
    Stack Overflow data collector
    
    Uses Stack Exchange API to collect high-quality Q&A pairs
    with code snippets.
    """
    
    def __init__(self):
        self.api_base = "https://api.stackexchange.com/2.3"
        self.output_dir = Path("data/raw/stackoverflow")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Target tags
        self.tags = [
            # Python frameworks
            "fastapi",
            "flask",
            "django",
            "python",
            "python-3.x",
            
            # JavaScript frameworks
            "express",
            "nestjs",
            "node.js",
            "javascript",
            
            # Related topics
            "rest-api",
            "api",
            "authentication",
            "database",
        ]
    
    def collect_questions(self, tag: str, max_questions: int = 200):
        """
        Collect questions for a specific tag
        
        Args:
            tag: Stack Overflow tag
            max_questions: Maximum questions to collect per tag
        """
        
        logger.info(f"Collecting Stack Overflow questions for tag: {tag}")
        
        # Stack Exchange API endpoint
        url = f"{self.api_base}/questions"
        
        params = {
            "order": "desc",
            "sort": "votes",  # Get highest voted questions
            "tagged": tag,
            "site": "stackoverflow",
            "filter": "withbody",  # Include question body
            "pagesize": 100,  # Max per page
            "page": 1
        }
        
        all_questions = []
        pages_to_fetch = (max_questions // 100) + 1
        
        for page in range(1, pages_to_fetch + 1):
            params["page"] = page
            
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                questions = data.get("items", [])
                
                if not questions:
                    break
                
                all_questions.extend(questions)
                logger.info(f"  Fetched page {page}: {len(questions)} questions")
                
                # Respect rate limits
                if "backoff" in data:
                    backoff = data["backoff"]
                    logger.warning(f"  Rate limit backoff: waiting {backoff}s")
                    time.sleep(backoff)
                else:
                    time.sleep(0.5)  # Be nice to the API
                
                # Check quota
                if "quota_remaining" in data:
                    quota = data["quota_remaining"]
                    logger.info(f"  API quota remaining: {quota}")
                    if quota < 100:
                        logger.warning("  Low API quota!")
                        break
                
            except Exception as e:
                logger.error(f"  Error fetching page {page}: {e}")
                break
        
        logger.info(f"✅ Collected {len(all_questions)} questions for tag '{tag}'")
        
        # Save raw data
        output_file = self.output_dir / f"questions_{tag}.json"
        with open(output_file, 'w') as f:
            json.dump(all_questions, f, indent=2)
        
        return all_questions
    
    def extract_code_snippets(self, html_body: str) -> List[str]:
        """
        Extract code blocks from HTML body
        
        Args:
            html_body: HTML content from question/answer
            
        Returns:
            List of code snippets
        """
        soup = BeautifulSoup(html_body, 'html.parser')
        code_blocks = soup.find_all('code')
        
        snippets = []
        for block in code_blocks:
            code = block.get_text().strip()
            # Filter out very short snippets (likely inline code)
            if len(code) > 50:
                snippets.append(code)
        
        return snippets
    
    def collect_all(self, questions_per_tag: int = 200):
        """
        Collect questions from all tags
        
        Args:
            questions_per_tag: Maximum questions per tag
        """
        
        logger.info("=" * 60)
        logger.info("STACK OVERFLOW DATA COLLECTION")
        logger.info("=" * 60)
        logger.info(f"Tags: {len(self.tags)}")
        logger.info(f"Questions per tag: {questions_per_tag}")
        logger.info(f"Target total: {len(self.tags) * questions_per_tag}")
        logger.info("")
        
        total_questions = 0
        total_snippets = 0
        
        for tag in self.tags:
            try:
                questions = self.collect_questions(tag, questions_per_tag)
                total_questions += len(questions)
                
                # Extract code snippets
                for q in questions:
                    snippets = self.extract_code_snippets(q.get("body", ""))
                    total_snippets += len(snippets)
                
                logger.info(f"  Total snippets from '{tag}': {total_snippets}")
                
            except Exception as e:
                logger.error(f"❌ Error collecting tag '{tag}': {e}")
        
        # Create summary report
        report = {
            "collection_summary": {
                "total_tags": len(self.tags),
                "total_questions": total_questions,
                "total_code_snippets": total_snippets,
                "average_snippets_per_question": total_snippets / max(total_questions, 1),
                "timestamp": datetime.now().isoformat()
            },
            "tags": self.tags,
            "per_tag_target": questions_per_tag
        }
        
        report_file = self.output_dir / "collection_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("COLLECTION COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"✅ Total questions: {total_questions}")
        logger.info(f"✅ Total code snippets: {total_snippets}")
        logger.info(f"✅ Report saved to: {report_file}")
        logger.info("=" * 60)


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print(" " * 15 + "STACK OVERFLOW DATA COLLECTOR")
    print("=" * 70)
    print("\n⚠️  Note: Stack Exchange API has rate limits:")
    print("   - 300 requests/day without API key")
    print("   - 10,000 requests/day with API key")
    print("\n   Get API key at: https://stackapps.com/apps/oauth/register")
    print("\n" + "=" * 70)
    
    collector = StackOverflowCollector()
    
    # Start with smaller batch for testing
    print("\nStarting collection (100 questions per tag for testing)...")
    collector.collect_all(questions_per_tag=100)


if __name__ == "__main__":
    main()
