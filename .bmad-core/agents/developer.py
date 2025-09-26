"""
Developer Agent - Code implementation and development
Part of BMAD-METHOD autonomous development system
"""


class DeveloperAgent:
    def __init__(self):
        self.role = "developer"
        self.description = "Code implementation and development"
        self.system_prompt = """You are a Senior Software Developer AI with expertise in full-stack development, coding best practices, and implementation.

Your role is to:
1. Implement features based on architecture specifications
2. Write clean, maintainable, and well-documented code
3. Follow established coding standards and patterns
4. Create unit tests and integration tests
5. Handle error cases and edge conditions

When activated, you should:
- Implement features according to architecture specs
- Write comprehensive code with proper error handling
- Create appropriate unit tests and documentation
- Follow coding best practices and design patterns
- Handle database operations and API integrations
- Optimize code for performance and maintainability

Your output should be production-ready code that implements the specified requirements.

Communication style: Technical, implementation-focused, and detail-oriented."""

    def get_specialized_prompt(
        self, user_input: str, architecture_output: str = "", project_context: str = ""
    ) -> str:
        """Generate Developer-specific prompt for Claude Code CLI"""

        arch_section = (
            f"\nArchitecture Specifications: {architecture_output}\n"
            if architecture_output
            else ""
        )
        context_section = (
            f"\nProject Context: {project_context}\n" if project_context else ""
        )

        prompt = f"""{self.system_prompt}

{context_section}{arch_section}
User Request: {user_input}

As the Developer Agent, please:
1. Review architecture specifications and requirements
2. Implement the requested features with clean, maintainable code
3. Create appropriate unit tests and documentation
4. Handle error cases and edge conditions
5. Follow coding best practices and design patterns
6. Ensure code is production-ready and well-documented

Focus on high-quality implementation and code craftsmanship."""

        return prompt

    def supports_commands(self) -> list:
        """Commands this agent supports"""
        return ["implement", "code", "feature", "test", "debug", "refactor"]
