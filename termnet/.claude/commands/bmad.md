# BMAD Workflow Commands

Manage your BMAD-METHOD autonomous development workflow.

## Available Commands

### Workflow Management
```bash
bmad status    # Show current workflow status
bmad save      # Save current workflow state
bmad load      # Load previous workflow state
bmad reset     # Reset workflow to start fresh
bmad help      # Show detailed help
```

### Agent Commands
```bash
/analyst [project description]  # Deep requirements analysis
/pm [context]                  # Strategic planning & PRD creation
/architect [requirements]      # System design & architecture
/developer [specifications]   # Code implementation
/qa [validation focus]        # Quality assurance & review
```

## Standard Workflow Process
1. **Start with Analysis**: `/analyst Create a task management web app`
2. **Strategic Planning**: `/pm` (automatically uses analyst output)
3. **Technical Design**: `/architect` (automatically uses PM output)
4. **Implementation**: `/developer` (automatically uses architect output)
5. **Quality Assurance**: `/qa` (validates developer output)

## Workflow Features
- **Context Preservation**: Each agent builds on previous agent outputs
- **State Management**: Save/load workflow states for complex projects
- **Progress Tracking**: Monitor workflow completion status
- **Autonomous Collaboration**: Agents automatically pass context to next agent

## Example Usage
```bash
# Complete autonomous development workflow
/analyst Build a RESTful API for user management with authentication
bmad status
/pm
/architect
/developer
/qa
bmad save
```