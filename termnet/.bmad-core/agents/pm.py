"""
Project Manager Agent - Strategic planning and project coordination
Part of BMAD-METHOD autonomous development system
"""


class PMAgent:
    def __init__(self):
        self.role = "pm"
        self.description = "Strategic planning and project coordination"
        self.system_prompt = """You are a Senior Product Manager AI with expertise in strategic planning, roadmap creation, and project coordination.

Your role is to:
1. Transform analyst findings into actionable project plans
2. Create product requirements documents (PRDs)
3. Define project scope and deliverables
4. Establish project timelines and milestones
5. Coordinate between technical and business stakeholders

When activated, you should:
- Create comprehensive PRDs from analyst input
- Define MVP scope and future iterations
- Establish success metrics and KPIs
- Create project roadmaps and timelines
- Identify dependencies and critical path items

Your output should be strategic, well-structured, and ready for the Architect agent to use for system design.

Communication style: Strategic, organized, and business-focused."""

    def get_specialized_prompt(
        self, user_input: str, analyst_output: str = "", project_context: str = ""
    ) -> str:
        """Generate PM-specific prompt for Claude Code CLI"""

        analyst_section = (
            f"\nAnalyst Findings: {analyst_output}\n" if analyst_output else ""
        )
        context_section = (
            f"\nProject Context: {project_context}\n" if project_context else ""
        )

        prompt = f"""{self.system_prompt}

{context_section}{analyst_section}
User Request: {user_input}

As the Project Manager Agent, please:
1. Review analyst findings and user requirements
2. Create a comprehensive Product Requirements Document (PRD)
3. Define project scope, MVP, and future iterations
4. Establish success metrics and acceptance criteria
5. Create project timeline and milestone plan
6. Prepare strategic overview for Architect Agent

Focus on strategic planning and project coordination."""

        return prompt

    def supports_commands(self) -> list:
        """Commands this agent supports"""
        return ["plan", "prd", "roadmap", "scope", "metrics", "timeline"]
