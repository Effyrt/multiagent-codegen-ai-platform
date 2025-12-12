"""
Code Validation Tools

Tools for validating code syntax, security, and quality.
"""

import ast
import logging
from typing import Dict, Any, List

from .base_tool import BaseTool, ToolParameter

logger = logging.getLogger(__name__)


class CodeValidationTool(BaseTool):
    """
    Validate code syntax and structure
    
    Checks if code has valid syntax and no obvious structural errors.
    """
    
    name = "validate_code_syntax"
    description = "Check if code has valid syntax and structure"
    parameters = [
        ToolParameter(
            name="code",
            type="string",
            description="Code to validate",
            required=True
        ),
        ToolParameter(
            name="language",
            type="string",
            description="Programming language (python, javascript)",
            required=True,
            enum=["python", "javascript"]
        )
    ]
    
    async def execute(self, code: str, language: str) -> Dict[str, Any]:
        """
        Validate code syntax
        
        Args:
            code: Code to validate
            language: Programming language
            
        Returns:
            Validation result with errors if any
        """
        
        self.logger.info(f"Validating {language} code ({len(code)} chars)")
        
        errors = []
        warnings = []
        is_valid = False
        
        try:
            if language == "python":
                # Parse Python code using AST
                try:
                    ast.parse(code)
                    is_valid = True
                    self.logger.info("✅ Python code syntax is valid")
                except SyntaxError as e:
                    errors.append({
                        "type": "SyntaxError",
                        "message": str(e),
                        "line": e.lineno,
                        "offset": e.offset
                    })
                    self.logger.warning(f"❌ Python syntax error: {e}")
                
                # Additional checks
                if "eval(" in code or "exec(" in code:
                    warnings.append("Code contains eval() or exec() which can be dangerous")
                
                if "import os" in code and ("os.system" in code or "os.popen" in code):
                    warnings.append("Code uses potentially unsafe os module functions")
            
            elif language == "javascript":
                # For JavaScript, we'd use a parser like esprima
                # For now, do basic checks
                
                # Check for common syntax patterns
                open_braces = code.count("{")
                close_braces = code.count("}")
                open_parens = code.count("(")
                close_parens = code.count(")")
                open_brackets = code.count("[")
                close_brackets = code.count("]")
                
                if open_braces != close_braces:
                    errors.append({
                        "type": "SyntaxError",
                        "message": f"Mismatched braces: {open_braces} open, {close_braces} close"
                    })
                
                if open_parens != close_parens:
                    errors.append({
                        "type": "SyntaxError",
                        "message": f"Mismatched parentheses: {open_parens} open, {close_parens} close"
                    })
                
                if open_brackets != close_brackets:
                    errors.append({
                        "type": "SyntaxError",
                        "message": f"Mismatched brackets: {open_brackets} open, {close_brackets} close"
                    })
                
                is_valid = len(errors) == 0
                
                if is_valid:
                    self.logger.info("✅ JavaScript code structure looks valid")
                else:
                    self.logger.warning(f"❌ JavaScript validation found {len(errors)} errors")
                
                # Warnings
                if "eval(" in code:
                    warnings.append("Code contains eval() which can be dangerous")
            
            else:
                errors.append({
                    "type": "ValidationError",
                    "message": f"Unsupported language: {language}"
                })
            
            return {
                "valid": is_valid,
                "language": language,
                "errors": errors,
                "warnings": warnings,
                "error_count": len(errors),
                "warning_count": len(warnings)
            }
            
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return {
                "valid": False,
                "language": language,
                "errors": [{
                    "type": "ValidationError",
                    "message": str(e)
                }],
                "warnings": [],
                "error_count": 1,
                "warning_count": 0
            }


class SecurityScanTool(BaseTool):
    """
    Scan code for security vulnerabilities
    
    Checks for common security issues and dangerous patterns.
    """
    
    name = "scan_security_issues"
    description = "Scan code for common security vulnerabilities and dangerous patterns"
    parameters = [
        ToolParameter(
            name="code",
            type="string",
            description="Code to scan",
            required=True
        ),
        ToolParameter(
            name="language",
            type="string",
            description="Programming language",
            required=False,
            enum=["python", "javascript"]
        )
    ]
    
    async def execute(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Scan code for security issues
        
        Args:
            code: Code to scan
            language: Programming language
            
        Returns:
            Security scan results
        """
        
        self.logger.info(f"Scanning {language} code for security issues")
        
        issues = []
        
        # Common dangerous patterns
        dangerous_patterns = {
            "python": [
                ("eval(", "HIGH", "eval() can execute arbitrary code"),
                ("exec(", "HIGH", "exec() can execute arbitrary code"),
                ("__import__(", "MEDIUM", "Dynamic imports can be dangerous"),
                ("os.system(", "HIGH", "Shell command execution"),
                ("subprocess.call(", "MEDIUM", "Shell command execution"),
                ("pickle.loads(", "HIGH", "Pickle deserialization can be unsafe"),
                ("input(", "LOW", "User input should be validated"),
                ("open(", "LOW", "File operations should be validated"),
            ],
            "javascript": [
                ("eval(", "HIGH", "eval() can execute arbitrary code"),
                ("Function(", "HIGH", "Dynamic function creation can be dangerous"),
                ("innerHTML", "MEDIUM", "Can lead to XSS vulnerabilities"),
                ("document.write", "MEDIUM", "Can lead to XSS vulnerabilities"),
                ("localStorage", "LOW", "Sensitive data in localStorage can be accessed"),
                ("exec(", "HIGH", "Command execution"),
            ]
        }
        
        patterns = dangerous_patterns.get(language, [])
        
        for pattern, severity, description in patterns:
            if pattern in code:
                issues.append({
                    "pattern": pattern,
                    "severity": severity,
                    "description": description,
                    "line": code.split(pattern)[0].count("\n") + 1
                })
        
        # SQL Injection patterns (language-agnostic)
        if any(word in code.lower() for word in ["select ", "insert ", "update ", "delete "]):
            if "%" in code or "f\"" in code or "${" in code:
                issues.append({
                    "pattern": "SQL Query with string formatting",
                    "severity": "HIGH",
                    "description": "Potential SQL injection vulnerability - use parameterized queries",
                    "line": 0
                })
        
        # Hardcoded secrets patterns
        secret_patterns = [
            "password", "api_key", "secret", "token", "credentials"
        ]
        for pattern in secret_patterns:
            if f'{pattern} = "' in code.lower() or f"{pattern} = '" in code.lower():
                issues.append({
                    "pattern": f"Hardcoded {pattern}",
                    "severity": "HIGH",
                    "description": f"Potential hardcoded secret: {pattern}",
                    "line": 0
                })
        
        # Count by severity
        severity_counts = {
            "HIGH": len([i for i in issues if i["severity"] == "HIGH"]),
            "MEDIUM": len([i for i in issues if i["severity"] == "MEDIUM"]),
            "LOW": len([i for i in issues if i["severity"] == "LOW"])
        }
        
        result = {
            "clean": len(issues) == 0,
            "issues_found": len(issues),
            "issues": issues,
            "severity_counts": severity_counts,
            "risk_level": self._calculate_risk_level(severity_counts)
        }
        
        if len(issues) == 0:
            self.logger.info("✅ No security issues found")
        else:
            self.logger.warning(f"⚠️  Found {len(issues)} security issues")
        
        return result
    
    def _calculate_risk_level(self, severity_counts: Dict[str, int]) -> str:
        """Calculate overall risk level"""
        if severity_counts["HIGH"] > 0:
            return "HIGH"
        elif severity_counts["MEDIUM"] > 1:
            return "MEDIUM"
        elif severity_counts["MEDIUM"] == 1 or severity_counts["LOW"] > 2:
            return "LOW"
        else:
            return "MINIMAL"
