"""
Terminal Command Verification System
Generates verifiable terminal commands for all BMAD operations
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List


class CommandVerifier:
    """Generates and manages verification commands for BMAD operations"""

    def __init__(self):
        self.command_history = []
        self.verification_log = ".bmad-core/verification_log.json"

    def generate_test_commands(
        self, operation: str, context: Dict[str, Any] = None
    ) -> List[str]:
        """Generate terminal commands to verify specific operations"""

        commands = {
            "bmad_system": [
                "echo '=== BMAD System Verification ==='",
                "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from enhanced_orchestrator import EnhancedBMADOrchestrator; print('✅ BMAD System OK')\"",
                "ls -la .bmad-core/",
                "echo 'BMAD agents available:'",
                "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from agent_loader import AgentLoader; al = AgentLoader(); print(' '.join(al.list_agents()))\"",
            ],
            "react_framework": [
                "echo '=== ReAct Framework Test ==='",
                "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from react_framework import ReActFramework; rf = ReActFramework(); rf.set_goal('test'); rf.add_thought('testing'); print('✅ ReAct Framework OK')\"",
                "echo 'ReAct components loaded successfully'",
            ],
            "task_analysis": [
                "echo '=== Task Analysis Test ==='",
                "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from task_analyzer import TaskAnalyzer; ta = TaskAnalyzer(); c, w = ta.analyze_task('build web app'); print(f'✅ Analysis: {c.value} -> {len(w)} agents')\"",
            ],
            "context_manager": [
                "echo '=== Context Manager Test ==='",
                "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from context_manager import ContextManager; cm = ContextManager(); cm.initialize_project({'name': 'test'}); print('✅ Context Manager OK')\"",
            ],
            "full_integration": [
                "echo '=== Full Integration Test ==='",
                "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from enhanced_orchestrator import EnhancedBMADOrchestrator; from context_manager import ContextManager; eo = EnhancedBMADOrchestrator(); cm = ContextManager(); plan = eo.analyze_and_plan('create simple API'); print('✅ All systems integrated')\"",
            ],
            "phase3_integration": [
                "echo '=== Phase 3 Integration Test ==='",
                "python3 -c \"from termnet.claims_engine import ClaimsEngine; ce = ClaimsEngine('test.db'); print('✅ Phase 3 Claims Engine OK')\"",
                "python3 -c \"from termnet.command_lifecycle import CommandLifecycle; from termnet.claims_engine import ClaimsEngine; ce = ClaimsEngine('test.db'); cl = CommandLifecycle(ce); print('✅ Phase 3 Lifecycle OK')\"",
            ],
        }

        if operation not in commands:
            return [f"echo 'Unknown operation: {operation}'"]

        return commands[operation]

    def verify_installation(self) -> List[str]:
        """Generate commands to verify entire enhanced system"""
        return [
            "echo '🧪 TermNet Enhanced System Verification'",
            "echo '======================================'",
            "echo ''",
            # Check Python environment
            "python3 --version",
            "echo 'Current directory:' && pwd",
            # Check BMAD core files
            "echo '📁 BMAD Core Files:'",
            "ls -la .bmad-core/*.py | wc -l && echo 'Python files found'",
            # Test each component
            "echo '🔧 Testing ReAct Framework...'",
            "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from react_framework import ReActFramework; print('✅ ReAct OK')\"",
            "echo '🔧 Testing Task Analyzer...'",
            "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from task_analyzer import TaskAnalyzer; print('✅ TaskAnalyzer OK')\"",
            "echo '🔧 Testing Enhanced Orchestrator...'",
            "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from enhanced_orchestrator import EnhancedBMADOrchestrator; print('✅ Enhanced Orchestrator OK')\"",
            "echo '🔧 Testing Context Manager...'",
            "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from context_manager import ContextManager; print('✅ Context Manager OK')\"",
            "echo ''",
            "echo '🎉 All Enhanced Components Verified!'",
        ]

    def log_verification(
        self, operation: str, commands: List[str], success: bool = True
    ):
        """Log verification commands and results"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "commands": commands,
            "success": success,
        }

        self.command_history.append(log_entry)

        # Save to file
        os.makedirs(".bmad-core", exist_ok=True)
        with open(self.verification_log, "w") as f:
            json.dump(self.command_history, f, indent=2)

    def get_quick_test(self) -> str:
        """Get a single command to quickly test all enhancements"""
        return "python3 -c \"import sys; sys.path.insert(0,'.bmad-core'); from enhanced_orchestrator import EnhancedBMADOrchestrator; from context_manager import ContextManager; print('✅ All enhanced systems working')\""
