"""
Real-time Validation Monitor for TermNet
Monitors project changes and triggers validation automatically
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from termnet.validation_engine import ValidationEngine
from termnet.validation_rules import (
    ApplicationStartupValidation,
    DatabaseValidation,
    FlaskApplicationValidation,
    PythonSyntaxValidation,
    RequirementsValidation,
)
from termnet.validation_rules_advanced import (
    APIEndpointValidation,
    DockerValidation,
    ReactApplicationValidation,
    SecurityValidation,
    TestCoverageValidation,
)


class ValidationFileHandler(FileSystemEventHandler):
    """Handles file system events for automatic validation"""

    def __init__(self, monitor):
        self.monitor = monitor
        self.last_validation = {}

    def should_trigger_validation(self, file_path: str) -> bool:
        """Determine if file change should trigger validation"""
        path = Path(file_path)

        # Skip temporary files and directories
        if any(part.startswith(".") for part in path.parts):
            return False

        # Only validate important file types
        important_extensions = {
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".json",
            ".yml",
            ".yaml",
            ".dockerfile",
            ".md",
            ".txt",
            ".cfg",
            ".ini",
            ".toml",
        }

        return path.suffix.lower() in important_extensions

    def on_modified(self, event):
        if not event.is_directory and self.should_trigger_validation(event.src_path):
            # Debounce - don't validate same file too frequently
            now = time.time()
            if event.src_path in self.last_validation:
                if now - self.last_validation[event.src_path] < 5:  # 5 second debounce
                    return

            self.last_validation[event.src_path] = now
            asyncio.create_task(self.monitor.trigger_validation(event.src_path))

    def on_created(self, event):
        if not event.is_directory and self.should_trigger_validation(event.src_path):
            asyncio.create_task(self.monitor.trigger_validation(event.src_path))


class ValidationMonitor:
    """Real-time validation monitoring system"""

    def __init__(self, project_path: str = ".", monitor_db: str = "termnet_monitor.db"):
        self.project_path = Path(project_path).resolve()
        self.validation_engine = ValidationEngine(monitor_db)
        self.observer = None
        self.is_monitoring = False
        self.validation_queue = asyncio.Queue()
        self.stats = {
            "validations_triggered": 0,
            "files_monitored": 0,
            "last_validation": None,
            "monitoring_since": None,
        }

        self._setup_validation_rules()

    def _setup_validation_rules(self):
        """Setup all validation rules"""
        # Core rules
        self.validation_engine.add_rule(PythonSyntaxValidation())
        self.validation_engine.add_rule(RequirementsValidation())
        self.validation_engine.add_rule(ApplicationStartupValidation())
        self.validation_engine.add_rule(FlaskApplicationValidation())
        self.validation_engine.add_rule(DatabaseValidation())

        # Advanced rules
        self.validation_engine.add_rule(ReactApplicationValidation())
        self.validation_engine.add_rule(DockerValidation())
        self.validation_engine.add_rule(APIEndpointValidation())
        self.validation_engine.add_rule(SecurityValidation())
        self.validation_engine.add_rule(TestCoverageValidation())

        print(f"🔍 Monitoring with {len(self.validation_engine.rules)} validation rules")

    def start_monitoring(self):
        """Start file system monitoring"""
        if self.is_monitoring:
            print("⚠️ Monitoring already active")
            return

        print(f"👁️ Starting validation monitoring for: {self.project_path}")

        self.observer = Observer()
        event_handler = ValidationFileHandler(self)
        self.observer.schedule(event_handler, str(self.project_path), recursive=True)
        self.observer.start()

        self.is_monitoring = True
        self.stats["monitoring_since"] = datetime.now().isoformat()

        print("✅ Real-time validation monitoring started")

    def stop_monitoring(self):
        """Stop file system monitoring"""
        if not self.is_monitoring:
            return

        if self.observer:
            self.observer.stop()
            self.observer.join()

        self.is_monitoring = False
        print("🛑 Validation monitoring stopped")

    async def trigger_validation(self, changed_file: str):
        """Trigger validation based on file change"""
        try:
            print(f"🔄 File changed: {Path(changed_file).name} - triggering validation")

            # Add to validation queue
            await self.validation_queue.put(
                {
                    "file": changed_file,
                    "timestamp": datetime.now().isoformat(),
                    "type": "file_change",
                }
            )

            # Run validation
            results = await self.validation_engine.validate_project(
                str(self.project_path),
                {
                    "trigger": "file_change",
                    "changed_file": changed_file,
                    "monitoring_mode": True,
                },
            )

            self.stats["validations_triggered"] += 1
            self.stats["last_validation"] = datetime.now().isoformat()

            # Show validation summary
            self._display_validation_summary(results, changed_file)

        except Exception as e:
            print(f"❌ Validation error: {e}")

    def _display_validation_summary(self, results: Dict[str, Any], trigger_file: str):
        """Display concise validation summary"""
        status = results.get("overall_status", "UNKNOWN")
        passed = results.get("passed", 0)
        failed = results.get("failed", 0)
        errors = results.get("errors", 0)

        status_emoji = {"PASSED": "✅", "FAILED": "❌", "ERROR": "🚫"}.get(status, "❓")

        print(
            f"{status_emoji} Validation: {status} | {passed}✅ {failed}❌ {errors}🚫 | Trigger: {Path(trigger_file).name}"
        )

        # Show critical issues only
        if failed > 0 or errors > 0:
            critical_issues = [
                r
                for r in results.get("results", [])
                if r.status.name in ["FAILED", "ERROR"]
                and r.severity.name == "CRITICAL"
            ]
            for issue in critical_issues[:2]:  # Show max 2 critical issues
                print(f"  ⚠️ {issue.rule_name}: {issue.message}")

    async def manual_validation(self) -> Dict[str, Any]:
        """Trigger manual validation"""
        print("🔍 Running manual validation...")

        results = await self.validation_engine.validate_project(
            str(self.project_path),
            {
                "trigger": "manual",
                "monitoring_mode": True,
                "timestamp": datetime.now().isoformat(),
            },
        )

        self.stats["validations_triggered"] += 1
        self.stats["last_validation"] = datetime.now().isoformat()

        return results

    def score_agent_completion(
        self, request_id: str, final_answer: str, evidence_snippets: List[str]
    ):
        """Hook to score agent run completion with semantic evaluation"""
        try:
            from termnet.claims_engine import SemanticChecker

            checker = SemanticChecker()
            score = checker.score_answer(final_answer, evidence_snippets)
            checker.save_semantic_score(request_id, score)

            print(
                f"📊 Semantic Score [Request {request_id}]: {score['final']}/100 "
                f"(G:{score['grounding']:.2f} C:{score['consistency']:.2f} S:{score['style']:.2f})"
            )

            return score

        except Exception as e:
            print(f"⚠️ Semantic scoring failed for {request_id}: {e}")
            return None

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get current monitoring statistics"""
        monitored_files = 0
        if self.project_path.exists():
            monitored_files = len(
                [
                    f
                    for f in self.project_path.rglob("*")
                    if f.is_file() and not any(part.startswith(".") for part in f.parts)
                ]
            )

        return {
            **self.stats,
            "is_monitoring": self.is_monitoring,
            "monitored_files": monitored_files,
            "project_path": str(self.project_path),
            "validation_rules": len(self.validation_engine.rules),
        }

    def get_recent_validations(self, limit: int = 10) -> List[Dict]:
        """Get recent validation history"""
        return self.validation_engine.get_validation_history(limit=limit)

    async def health_check(self) -> Dict[str, Any]:
        """Perform system health check"""
        health = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_active": self.is_monitoring,
            "validation_engine": self.validation_engine is not None,
            "rules_loaded": len(self.validation_engine.rules),
            "project_accessible": self.project_path.exists(),
            "queue_size": self.validation_queue.qsize(),
        }

        # Test validation engine
        try:
            test_result = await self.validation_engine.validate_command_output(
                "echo 'health check'", ["health check"], str(self.project_path)
            )
            health["engine_functional"] = test_result.status.name == "PASSED"
        except Exception as e:
            health["engine_functional"] = False
            health["engine_error"] = str(e)

        return health

    def export_monitoring_report(
        self, filename: str = "validation_monitoring_report.json"
    ):
        """Export monitoring report"""
        report = {
            "report_generated": datetime.now().isoformat(),
            "monitoring_stats": self.get_monitoring_stats(),
            "recent_validations": self.get_recent_validations(20),
            "validation_rules": [
                {
                    "name": rule.name,
                    "description": rule.description,
                    "severity": rule.severity.value,
                }
                for rule in self.validation_engine.rules
            ],
        }

        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"📊 Monitoring report exported to: {filename}")
        return filename


# Standalone monitoring functions
async def start_monitoring_daemon(project_path: str = "."):
    """Start monitoring as a daemon process"""
    monitor = ValidationMonitor(project_path)
    monitor.start_monitoring()

    print("🤖 Validation monitoring daemon started")
    print("Press Ctrl+C to stop...")

    try:
        # Keep monitoring running
        while True:
            await asyncio.sleep(10)

            # Periodic health check
            health = await monitor.health_check()
            if not health.get("engine_functional", False):
                print("⚠️ Validation engine health check failed")

    except KeyboardInterrupt:
        print("\n🛑 Stopping monitoring daemon...")
        monitor.stop_monitoring()


if __name__ == "__main__":
    import sys

    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    asyncio.run(start_monitoring_daemon(project_path))
