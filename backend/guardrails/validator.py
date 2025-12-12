"""
Production-Grade Code Validation & Security Scanning
"""
import ast
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Result of code validation"""
    is_valid: bool
    score: float  # 0-10
    issues: List[str]
    warnings: List[str]
    security_flags: List[str]
    
class CodeValidator:
    """Multi-layer code validation system"""
    
    def __init__(self):
        self.security_patterns = {
            'sql_injection': [
                r'execute\s*\(',
                r'executemany\s*\(',
                r'\.format\s*\(',  # String formatting in SQL
                r'%s.*SELECT',
            ],
            'command_injection': [
                r'os\.system',
                r'subprocess\.call',
                r'subprocess\.run',
                r'eval\s*\(',
                r'exec\s*\(',
            ],
            'path_traversal': [
                r'\.\./\.\.',
                r'\.\.\\\\',
            ]
        }
    
    def validate_python(self, code: str) -> ValidationResult:
        """Comprehensive Python validation"""
        
        issues = []
        warnings = []
        security_flags = []
        score = 10.0
        
        # 1. Syntax validation (AST parsing)
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error: {str(e)}")
            score -= 5.0
            return ValidationResult(False, max(0, score), issues, warnings, security_flags)
        
        # 2. Security scanning
        for vuln_type, patterns in self.security_patterns.items():
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    security_flags.append(f"Potential {vuln_type}: {pattern}")
                    score -= 2.0
        
        # 3. Best practices checks
        if 'def ' not in code:
            warnings.append("No function definitions found")
            score -= 0.5
        
        if '"""' not in code and "'''" not in code:
            warnings.append("Missing docstrings")
            score -= 1.0
        
        if 'try:' not in code and 'except' not in code:
            warnings.append("No error handling detected")
            score -= 1.0
        
        if ':' in code and '->' not in code:
            warnings.append("Missing type hints")
            score -= 0.5
        
        # 4. Complexity check
        lines = len([l for l in code.split('\n') if l.strip()])
        if lines > 200:
            warnings.append(f"High complexity: {lines} lines")
            score -= 0.5
        
        # 5. Security critical - fail if found
        if security_flags:
            issues.append("Security vulnerabilities detected - requires review")
            score = min(score, 6.0)  # Cap at 6.0 if security issues
        
        is_valid = score >= 7.0 and len(security_flags) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            score=max(0, min(10, score)),
            issues=issues,
            warnings=warnings,
            security_flags=security_flags
        )
    
    def validate_javascript(self, code: str) -> ValidationResult:
        """Basic JavaScript validation"""
        
        issues = []
        warnings = []
        security_flags = []
        score = 10.0
        
        # Basic syntax checks
        if code.count('{') != code.count('}'):
            issues.append("Mismatched braces")
            score -= 3.0
        
        if code.count('(') != code.count(')'):
            issues.append("Mismatched parentheses")
            score -= 3.0
        
        # XSS patterns
        xss_patterns = [r'innerHTML\s*=', r'eval\s*\(', r'document\.write']
        for pattern in xss_patterns:
            if re.search(pattern, code):
                security_flags.append(f"Potential XSS: {pattern}")
                score -= 2.0
        
        # Best practices
        if 'function ' not in code and 'const ' not in code and 'let ' not in code:
            warnings.append("No function or variable declarations")
            score -= 1.0
        
        is_valid = score >= 7.0 and len(security_flags) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            score=max(0, min(10, score)),
            issues=issues,
            warnings=warnings,
            security_flags=security_flags
        )
