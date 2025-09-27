# Automated BMAD Workflow Command

Trigger automated end-to-end development workflow through all BMAD agents.

## Usage
```
/analyst [detailed project description]
```

## What Happens Automatically
When you provide a detailed project description to the analyst, the system will:

1. **🔍 ANALYST**: Analyzes requirements and creates comprehensive documentation
2. **📋 PM**: Creates PRD with scope, timeline, and success metrics
3. **🏗️ ARCHITECT**: Designs system architecture and technical specifications
4. **💻 DEVELOPER**: Implements production-ready code with tests
5. **✅ QA**: Reviews, validates, and creates comprehensive test plans

## Example - Automated Workflow
```
/analyst Create a task management web app with user authentication, CRUD operations for tasks, and a clean responsive UI
```

This will automatically execute all 5 agents in sequence, with each agent building on the previous agent's output.

## Manual Agent Execution
For single agent execution, use individual commands:
- `/pm` - Just the PM agent
- `/architect` - Just the architect agent
- `/developer` - Just the developer agent
- `/qa` - Just the QA agent

## Workflow Management
- `bmad status` - Check current workflow progress
- `bmad save` - Save workflow state
- `bmad reset` - Start fresh workflow

The automated workflow delivers a complete solution from requirements to tested code in one command!
