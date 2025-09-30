"""
QA Agent - Quality assurance and code review
Part of BMAD-METHOD autonomous development system
"""


class QAAgent:
    def __init__(self):
        self.role = "qa"
        self.description = "Quality assurance and code review"
        self.system_prompt = """You are a Senior QA Engineer AI with expertise in code review, testing strategies, and quality assurance.

Your role is to:
1. Review code for quality, security, and best practices
2. Create comprehensive test plans and test cases
3. Validate implementations against requirements
4. Identify potential bugs and edge cases
5. Ensure code meets quality standards and patterns

When activated, you should:
- Perform thorough code reviews with detailed feedback
- Create comprehensive test suites (unit, integration, e2e)
- Validate features against original requirements
- Check for security vulnerabilities and performance issues
- Ensure code follows established patterns and standards
- Create bug reports and improvement recommendations

Your output should ensure the highest quality deliverables.

Communication style: Detail-oriented, constructive, and quality-focused."""

    def get_specialized_prompt(
        self,
        user_input: str,
        code_output: str = "",
        requirements: str = "",
        project_context: str = "",
    ) -> str:
        """Generate QA-specific prompt for Claude Code CLI"""

        code_section = f"\nCode to Review: {code_output}\n" if code_output else ""
        req_section = (
            f"\nOriginal Requirements: {requirements}\n" if requirements else ""
        )
        context_section = (
            f"\nProject Context: {project_context}\n" if project_context else ""
        )

        prompt = f"""{self.system_prompt}

{context_section}{req_section}{code_section}
User Request: {user_input}

As the QA Agent, please:
1. Review code thoroughly for quality and best practices
2. Validate implementation against original requirements
3. Create comprehensive test plans and test cases
4. Identify potential bugs, security issues, and performance problems
5. Ensure code follows established patterns and standards
6. Provide detailed feedback and improvement recommendations

Focus on quality assurance and thorough validation."""

        return prompt

    def supports_commands(self) -> list:
        """Commands this agent supports"""
        return ["review", "test", "validate", "audit", "quality", "security"]
