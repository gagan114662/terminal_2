"""
BMAD Validation Agent - Automated quality assurance and code validation
Performs comprehensive validation without user intervention
"""

from typing import Any, Dict, List


class ValidatorAgent:
    def __init__(self):
        self.role = "validator"
        self.name = "ValidationAgent"
        self.description = "Automated validation and quality assurance agent"
        self.validation_rules = []

    def supports_command(self, command: str) -> bool:
        """Check if this agent supports the given command"""
        validation_commands = ["/validator", "/validate", "/quality", "/check"]
        return any(cmd in command.lower() for cmd in validation_commands)

    def get_specialized_prompt(
        self,
        request: str,
        code_output: str = "",
        requirements: str = "",
        context: str = "",
    ) -> str:
        """Generate specialized validation prompt for autonomous operation"""

        base_prompt = f"""You are the BMAD ValidationAgent - an autonomous code validation specialist.

🎯 **MISSION**: Perform comprehensive, automated validation of code implementations without requiring user permission.

📋 **AUTONOMOUS VALIDATION PROTOCOL**:

1. **IMMEDIATE EXECUTION** - Run all validation commands automatically
2. **COMPREHENSIVE TESTING** - Test syntax, functionality, dependencies, and security
3. **BUILD VERIFICATION** - Ensure code builds and runs correctly
4. **PERFORMANCE CHECK** - Validate performance and resource usage
5. **SECURITY SCAN** - Check for vulnerabilities and best practices
6. **INTEGRATION TEST** - Verify compatibility with existing systems

🔧 **VALIDATION CATEGORIES** (Execute ALL autonomously):

**A. Code Quality Validation**:
```bash
# Run these commands automatically without asking:
python -m py_compile *.py
python -c "import ast; [ast.parse(open(f).read()) for f in glob('*.py')]"
python -m flake8 . --max-line-length=120
python -m pylint *.py --disable=all --enable=syntax-error
```

**B. Dependency Validation**:
```bash
pip check
pip list --outdated
python -c "import pkg_resources; pkg_resources.require(open('requirements.txt').read().splitlines())"
```

**C. Functional Testing**:
```bash
python -m pytest -v
python -c "exec(open('main.py').read())" --timeout=30
flask run --port=5001 & sleep 3; curl localhost:5001; kill %1
```

**D. Security Validation**:
```bash
bandit -r . -f json
safety check
pip-audit
```

**E. Performance Testing**:
```bash
python -m cProfile -s tottime main.py
python -c "import psutil; import time; start=psutil.cpu_percent(); time.sleep(1); print(f'CPU: {{psutil.cpu_percent()-start}}%')"
```

🚀 **EXECUTION INSTRUCTIONS**:
- Execute ALL validation commands immediately
- Do NOT ask for permission
- Report results with ✅/❌/⚠️ status
- Automatically fix simple issues found
- Provide detailed validation report
- Store results in validation database

💡 **VALIDATION CONTEXT**:
Request: {request}

Previous Code Output:
{code_output[:2000] if code_output else "No previous code provided"}

Original Requirements:
{requirements[:1000] if requirements else "No specific requirements provided"}

Additional Context:
{context[:500] if context else "No additional context"}

🎯 **AUTONOMOUS ACTION REQUIRED**:
Start validation immediately using TermNet's validation system and terminal tools. Execute all checks without waiting for approval. This is for autonomous development - user expects full automation.

🔧 **ADVANCED VALIDATION RULES TO USE**:
```python
# Import and use these validation rules:
from termnet.validation_engine import ValidationEngine
from termnet.validation_rules import PythonSyntaxValidation, FlaskApplicationValidation, DatabaseValidation
from termnet.validation_rules_advanced import ReactApplicationValidation, DockerValidation, APIEndpointValidation, SecurityValidation, TestCoverageValidation

# Setup comprehensive validation
engine = ValidationEngine()
# Add all rules and run validation
results = await engine.validate_project('.')
```

Begin comprehensive validation now!"""

        return base_prompt

    def get_validation_commands(self) -> List[str]:
        """Get list of validation commands to execute autonomously"""
        return [
            # Syntax and compilation checks
            "python -m compileall .",
            "python -c \"import ast, glob; [ast.parse(open(f).read()) for f in glob.glob('**/*.py', recursive=True)]\"",
            # Dependency validation
            "pip check",
            'python -c "import pkg_resources; pkg_resources.working_set"',
            # Security checks
            "python -c \"import os, stat; [print(f'File {f} has permissions {oct(os.stat(f).st_mode)}') for f in os.listdir('.') if os.path.isfile(f)]\"",
            # Performance baseline
            "python -c \"import psutil; print(f'Memory: {psutil.virtual_memory().percent}% CPU: {psutil.cpu_percent(interval=1)}%')\"",
            # Application startup test
            "python -c \"import sys, importlib; [importlib.import_module(m.replace('.py', '')) for m in sys.argv[1:] if m.endswith('.py')]\"",
        ]

    def create_validation_report(self, results: Dict[str, Any]) -> str:
        """Create comprehensive validation report"""
        report = "📋 **AUTONOMOUS VALIDATION REPORT**\n\n"

        if results.get("overall_status") == "PASSED":
            report += "🎉 **VALIDATION STATUS: PASSED** ✅\n\n"
        else:
            report += "⚠️ **VALIDATION STATUS: ISSUES FOUND**\n\n"

        report += "**Summary Statistics:**\n"
        report += f"- Total Rules: {results.get('total_rules', 0)}\n"
        report += f"- Passed: {results.get('passed', 0)} ✅\n"
        report += f"- Failed: {results.get('failed', 0)} ❌\n"
        report += f"- Errors: {results.get('errors', 0)} 🚫\n"
        report += f"- Execution Time: {results.get('execution_time', 0):.2f}s\n\n"

        if results.get("results"):
            report += "**Detailed Results:**\n"
            for result in results["results"]:
                status_emoji = {"PASSED": "✅", "FAILED": "❌", "ERROR": "🚫"}.get(
                    result.status.name, "❓"
                )
                report += f"{status_emoji} **{result.rule_name}**: {result.message}\n"
                if result.details:
                    report += f"   Details: {result.details}\n"
                report += "\n"

        report += (
            "🤖 **AUTONOMOUS VALIDATION COMPLETE** - No user intervention required!\n"
        )

        return report

    def should_validate_automatically(self, context: Dict[str, Any]) -> bool:
        """Determine if automatic validation should run"""
        # Always validate autonomously - this is the point of BMAD
        return True

    def get_auto_fix_suggestions(self, failed_results: List) -> List[str]:
        """Generate automatic fix suggestions"""
        fixes = []

        for result in failed_results:
            if "syntax" in result.rule_name.lower():
                fixes.append("python -m autopep8 --in-place --recursive .")
            elif "requirements" in result.rule_name.lower():
                fixes.append("pip install -r requirements.txt")
            elif "flask" in result.rule_name.lower():
                fixes.append("pip install flask")
            elif "database" in result.rule_name.lower():
                fixes.append('python -c "from app import db; db.create_all()"')

        return fixes
