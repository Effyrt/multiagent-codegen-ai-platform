"""
Multi-Dimensional Quality Scoring System
"""
from typing import Dict
import ast
import re

class QualityScorer:
    """Scores code quality on multiple dimensions"""
    
    def score_code(self, code: str, tests: str, language: str) -> Dict:
        """
        Score code on multiple dimensions
        Returns: dict with overall_score and breakdown
        """
        
        if language == "python":
            return self._score_python(code, tests)
        elif language == "javascript":
            return self._score_javascript(code, tests)
        else:
            return {"overall_score": 7.0, "confidence": 0.5}
    
    def _score_python(self, code: str, tests: str) -> Dict:
        """Score Python code"""
        
        scores = {
            "syntax": 10.0,
            "type_hints": 10.0,
            "documentation": 10.0,
            "error_handling": 10.0,
            "best_practices": 10.0,
            "test_coverage": 10.0
        }
        
        # Syntax (parse with AST)
        try:
            tree = ast.parse(code)
        except SyntaxError:
            scores["syntax"] = 0.0
            return {"overall_score": 0.0, "confidence": 1.0, "breakdown": scores}
        
        # Type hints
        has_type_hints = '->' in code or ': int' in code or ': str' in code
        if not has_type_hints:
            scores["type_hints"] = 5.0
        
        # Documentation
        has_docstring = '"""' in code or "'''" in code
        if not has_docstring:
            scores["documentation"] = 5.0
        
        # Error handling
        has_error_handling = 'try:' in code or 'except' in code or 'raise' in code
        if not has_error_handling:
            scores["error_handling"] = 6.0
        
        # Best practices
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        if not functions:
            scores["best_practices"] = 5.0
        
        # Test coverage
        test_count = tests.count('def test_') + tests.count('assert')
        if test_count < 3:
            scores["test_coverage"] = 5.0
        elif test_count < 5:
            scores["test_coverage"] = 7.5
        
        # Calculate overall
        overall = sum(scores.values()) / len(scores)
        
        # Confidence based on variance
        variance = max(scores.values()) - min(scores.values())
        confidence = 1.0 - (variance / 20.0)  # Lower variance = higher confidence
        
        return {
            "overall_score": round(overall, 1),
            "confidence": round(max(0.3, min(1.0, confidence)), 2),
            "breakdown": scores
        }
    
    def _score_javascript(self, code: str, tests: str) -> Dict:
        """Score JavaScript code"""
        
        scores = {
            "syntax": 10.0,
            "best_practices": 10.0,
            "test_coverage": 10.0
        }
        
        # Basic syntax
        if code.count('{') != code.count('}'):
            scores["syntax"] = 3.0
        
        # Best practices
        if 'function ' not in code and 'const ' not in code:
            scores["best_practices"] = 5.0
        
        # Tests
        test_count = tests.count('test(') + tests.count('expect(')
        if test_count < 3:
            scores["test_coverage"] = 5.0
        
        overall = sum(scores.values()) / len(scores)
        
        return {
            "overall_score": round(overall, 1),
            "confidence": 0.7,
            "breakdown": scores
        }
