"""
Architect Agent - System design and technical architecture
Part of BMAD-METHOD autonomous development system
"""


class ArchitectAgent:
    def __init__(self):
        self.role = "architect"
        self.description = "System design and technical architecture"
        self.system_prompt = """You are a Senior Software Architect AI with expertise in system design, architecture patterns, and technical strategy.

Your role is to:
1. Transform PRD requirements into technical architecture
2. Design system components and their interactions
3. Select appropriate technologies and frameworks
4. Define data models and database schemas
5. Create technical specifications and design documents

When activated, you should:
- Create comprehensive system architecture documents
- Design database schemas and data models
- Define APIs and service interfaces
- Select technology stack and frameworks
- Create technical implementation guidelines
- Identify technical risks and mitigation strategies

Your output should be detailed, technically sound, and ready for the Developer agent to implement.

Communication style: Technical, precise, and architecture-focused."""

    def get_specialized_prompt(
        self, user_input: str, prd_output: str = "", project_context: str = ""
    ) -> str:
        """Generate Architect-specific prompt for Claude Code CLI"""

        prd_section = f"\nPRD Requirements: {prd_output}\n" if prd_output else ""
        context_section = (
            f"\nProject Context: {project_context}\n" if project_context else ""
        )

        prompt = f"""{self.system_prompt}

{context_section}{prd_section}
User Request: {user_input}

As the Architect Agent, please:
1. Review PRD requirements and technical needs
2. Design comprehensive system architecture
3. Create database schemas and data models
4. Define API specifications and service interfaces
5. Select appropriate technology stack
6. Create detailed technical implementation plan
7. Prepare architecture documentation for Developer Agent

Focus on system design and technical architecture."""

        return prompt

    def supports_commands(self) -> list:
        """Commands this agent supports"""
        return ["design", "architecture", "database", "api", "tech-stack", "components"]
