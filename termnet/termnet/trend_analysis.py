"""
TermNet Trend Analysis System
Tracks metrics, analyzes patterns, and provides insights
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import os
import logging
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Individual metric data point"""
    timestamp: str
    category: str
    name: str
    value: float
    metadata: Dict[str, Any]
    tags: List[str]


@dataclass
class Trend:
    """Trend analysis result"""
    category: str
    name: str
    direction: str  # 'increasing', 'decreasing', 'stable'
    slope: float
    correlation: float
    forecast: List[float]
    confidence: float
    anomalies: List[Dict[str, Any]]


class TrendAnalyzer:
    """Main trend analysis engine"""

    def __init__(self, db_path: str = "termnet_trends.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize trend database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    metadata TEXT,
                    tags TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL,
                    direction TEXT,
                    slope REAL,
                    correlation REAL,
                    forecast TEXT,
                    confidence REAL,
                    anomalies TEXT,
                    analyzed_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_category ON metrics(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")

    def record_metric(self, category: str, name: str, value: float,
                     metadata: Optional[Dict] = None, tags: Optional[List[str]] = None):
        """Record a new metric data point"""
        metric = Metric(
            timestamp=datetime.now().isoformat(),
            category=category,
            name=name,
            value=value,
            metadata=metadata or {},
            tags=tags or []
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO metrics (timestamp, category, name, value, metadata, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metric.timestamp,
                metric.category,
                metric.name,
                metric.value,
                json.dumps(metric.metadata),
                json.dumps(metric.tags)
            ))

        logger.info(f"Recorded metric: {category}/{name} = {value}")

    def get_metrics(self, category: str, name: str,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> List[Tuple[str, float]]:
        """Retrieve metrics for analysis"""
        query = """
            SELECT timestamp, value FROM metrics
            WHERE category = ? AND name = ?
        """
        params = [category, name]

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        query += " ORDER BY timestamp"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def analyze_trend(self, category: str, name: str,
                     window_days: int = 7) -> Optional[Trend]:
        """Analyze trend for a specific metric"""
        start_time = datetime.now() - timedelta(days=window_days)
        data = self.get_metrics(category, name, start_time)

        if len(data) < 3:
            logger.warning(f"Insufficient data for trend analysis: {category}/{name}")
            return None

        timestamps = [datetime.fromisoformat(t) for t, _ in data]
        values = [v for _, v in data]

        # Convert timestamps to numeric values for regression
        x = [(t - timestamps[0]).total_seconds() / 3600 for t in timestamps]
        y = values

        # Calculate linear regression using pure Python
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n

        # Calculate correlation
        mean_x = sum_x / n
        mean_y = sum_y / n

        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        denominator_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

        if denominator_x * denominator_y > 0:
            correlation = numerator / (denominator_x * denominator_y)
        else:
            correlation = 0

        # Determine trend direction
        if abs(slope) < 0.01:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'

        # Simple forecast (next 3 points)
        last_x = x[-1]
        forecast_x = [last_x + i * 24 for i in range(1, 4)]  # Next 3 days
        forecast = [slope * fx + intercept for fx in forecast_x]

        # Detect anomalies (values outside 2 standard deviations)
        mean = sum(y) / len(y)
        variance = sum((yi - mean) ** 2 for yi in y) / len(y)
        std = math.sqrt(variance)
        anomalies = []

        for i, value in enumerate(values):
            if abs(value - mean) > 2 * std:
                anomalies.append({
                    'timestamp': timestamps[i].isoformat(),
                    'value': value,
                    'deviation': (value - mean) / std
                })

        # Calculate confidence based on correlation and data points
        confidence = abs(correlation) * min(1.0, len(data) / 10.0)

        trend = Trend(
            category=category,
            name=name,
            direction=direction,
            slope=float(slope),
            correlation=float(correlation),
            forecast=forecast,
            confidence=confidence,
            anomalies=anomalies
        )

        # Store trend analysis
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO trends (category, name, direction, slope, correlation,
                                  forecast, confidence, anomalies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trend.category,
                trend.name,
                trend.direction,
                trend.slope,
                trend.correlation,
                json.dumps(trend.forecast),
                trend.confidence,
                json.dumps(trend.anomalies)
            ))

        return trend

    def analyze_patterns(self, window_days: int = 30) -> Dict[str, Any]:
        """Analyze patterns across all metrics"""
        start_time = datetime.now() - timedelta(days=window_days)

        with sqlite3.connect(self.db_path) as conn:
            # Get all unique category/name combinations
            cursor = conn.execute("""
                SELECT DISTINCT category, name FROM metrics
                WHERE timestamp >= ?
            """, (start_time.isoformat(),))

            metrics = cursor.fetchall()

        patterns = {
            'trending_up': [],
            'trending_down': [],
            'stable': [],
            'volatile': [],
            'anomalous': []
        }

        for category, name in metrics:
            trend = self.analyze_trend(category, name, window_days)
            if trend:
                if trend.direction == 'increasing' and trend.confidence > 0.7:
                    patterns['trending_up'].append({
                        'metric': f"{category}/{name}",
                        'slope': trend.slope,
                        'confidence': trend.confidence
                    })
                elif trend.direction == 'decreasing' and trend.confidence > 0.7:
                    patterns['trending_down'].append({
                        'metric': f"{category}/{name}",
                        'slope': trend.slope,
                        'confidence': trend.confidence
                    })
                elif trend.direction == 'stable':
                    patterns['stable'].append({
                        'metric': f"{category}/{name}",
                        'confidence': trend.confidence
                    })

                if abs(trend.correlation) < 0.3:
                    patterns['volatile'].append({
                        'metric': f"{category}/{name}",
                        'correlation': trend.correlation
                    })

                if len(trend.anomalies) > 0:
                    patterns['anomalous'].append({
                        'metric': f"{category}/{name}",
                        'anomaly_count': len(trend.anomalies),
                        'anomalies': trend.anomalies
                    })

        return patterns

    def generate_report(self, report_type: str = "summary",
                       window_days: int = 7) -> str:
        """Generate trend analysis report"""
        patterns = self.analyze_patterns(window_days)

        report_lines = [
            f"=== Trend Analysis Report ({report_type}) ===",
            f"Analysis Period: Last {window_days} days",
            f"Generated: {datetime.now().isoformat()}",
            "",
        ]

        if report_type == "summary":
            report_lines.extend([
                "SUMMARY",
                "-" * 40,
                f"Metrics Trending Up: {len(patterns['trending_up'])}",
                f"Metrics Trending Down: {len(patterns['trending_down'])}",
                f"Stable Metrics: {len(patterns['stable'])}",
                f"Volatile Metrics: {len(patterns['volatile'])}",
                f"Metrics with Anomalies: {len(patterns['anomalous'])}",
                ""
            ])

        elif report_type == "detailed":
            # Trending up
            if patterns['trending_up']:
                report_lines.extend([
                    "TRENDING UP ↑",
                    "-" * 40
                ])
                for item in sorted(patterns['trending_up'],
                                 key=lambda x: x['slope'], reverse=True)[:5]:
                    report_lines.append(
                        f"  • {item['metric']}: slope={item['slope']:.4f}, "
                        f"confidence={item['confidence']:.2f}"
                    )
                report_lines.append("")

            # Trending down
            if patterns['trending_down']:
                report_lines.extend([
                    "TRENDING DOWN ↓",
                    "-" * 40
                ])
                for item in sorted(patterns['trending_down'],
                                 key=lambda x: x['slope'])[:5]:
                    report_lines.append(
                        f"  • {item['metric']}: slope={item['slope']:.4f}, "
                        f"confidence={item['confidence']:.2f}"
                    )
                report_lines.append("")

            # Anomalies
            if patterns['anomalous']:
                report_lines.extend([
                    "ANOMALIES DETECTED ⚠",
                    "-" * 40
                ])
                for item in sorted(patterns['anomalous'],
                                 key=lambda x: x['anomaly_count'], reverse=True)[:5]:
                    report_lines.append(
                        f"  • {item['metric']}: {item['anomaly_count']} anomalies"
                    )
                    for anomaly in item['anomalies'][:2]:  # Show first 2 anomalies
                        report_lines.append(
                            f"    - {anomaly['timestamp']}: value={anomaly['value']:.2f}, "
                            f"deviation={anomaly['deviation']:.2f}σ"
                        )
                report_lines.append("")

        elif report_type == "alerts":
            alerts = []

            # Critical trends
            for item in patterns['trending_down']:
                if item['confidence'] > 0.8 and item['slope'] < -1.0:
                    alerts.append({
                        'level': 'CRITICAL',
                        'message': f"{item['metric']} showing steep decline",
                        'details': item
                    })

            # Anomaly alerts
            for item in patterns['anomalous']:
                if item['anomaly_count'] > 3:
                    alerts.append({
                        'level': 'WARNING',
                        'message': f"{item['metric']} has multiple anomalies",
                        'details': item
                    })

            # Volatility alerts
            for item in patterns['volatile']:
                if abs(item['correlation']) < 0.1:
                    alerts.append({
                        'level': 'INFO',
                        'message': f"{item['metric']} showing high volatility",
                        'details': item
                    })

            if alerts:
                report_lines.extend([
                    "ALERTS",
                    "-" * 40
                ])
                for alert in sorted(alerts, key=lambda x: x['level']):
                    report_lines.append(
                        f"  [{alert['level']}] {alert['message']}"
                    )
                report_lines.append("")

        report = "\n".join(report_lines)

        # Store report
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO reports (report_type, content, summary)
                VALUES (?, ?, ?)
            """, (
                report_type,
                report,
                json.dumps(patterns)
            ))

        return report

    def get_statistics(self, category: str = None) -> Dict[str, Any]:
        """Get statistical summary"""
        with sqlite3.connect(self.db_path) as conn:
            if category:
                cursor = conn.execute("""
                    SELECT name, COUNT(*) as count, AVG(value) as mean,
                           MIN(value) as min, MAX(value) as max
                    FROM metrics
                    WHERE category = ?
                    GROUP BY name
                """, (category,))
            else:
                cursor = conn.execute("""
                    SELECT category, name, COUNT(*) as count, AVG(value) as mean,
                           MIN(value) as min, MAX(value) as max
                    FROM metrics
                    GROUP BY category, name
                """)

            results = cursor.fetchall()

        stats = {}
        for row in results:
            if category:
                name, count, mean, min_val, max_val = row
                stats[name] = {
                    'count': count,
                    'mean': mean,
                    'min': min_val,
                    'max': max_val,
                    'range': max_val - min_val
                }
            else:
                cat, name, count, mean, min_val, max_val = row
                if cat not in stats:
                    stats[cat] = {}
                stats[cat][name] = {
                    'count': count,
                    'mean': mean,
                    'min': min_val,
                    'max': max_val,
                    'range': max_val - min_val
                }

        return stats

    def collect_request_metrics(self, react_steps: int, tool_accuracy: float, latency_ms: int, request_id: str = None):
        """Collect minimal telemetry metrics for a completed request (opt-in via TERMNET_METRICS=1)"""
        if not os.getenv("TERMNET_METRICS", "0") == "1":
            return

        # Prepare metrics data
        metrics_data = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id or f"req-{datetime.now().strftime('%H%M%S')}",
            "react_steps_per_request": react_steps,
            "tool_selection_accuracy": round(tool_accuracy, 3),
            "reasoning_latency_ms": latency_ms
        }

        # Ensure artifacts directory exists
        os.makedirs("./artifacts/last_run", exist_ok=True)

        # Append to metrics dump file
        metrics_file = "./artifacts/last_run/metrics_dump.json"

        try:
            # Read existing data or start with empty list
            if os.path.exists(metrics_file):
                with open(metrics_file, 'r') as f:
                    all_metrics = json.load(f)
            else:
                all_metrics = []

            # Append new metrics
            all_metrics.append(metrics_data)

            # Keep only last 100 entries to prevent file growth
            if len(all_metrics) > 100:
                all_metrics = all_metrics[-100:]

            # Write back to file
            with open(metrics_file, 'w') as f:
                json.dump(all_metrics, f, indent=2)

            logger.info(f"📊 Telemetry: {react_steps} steps, {tool_accuracy:.1%} accuracy, {latency_ms}ms latency")

        except Exception as e:
            logger.warning(f"Failed to write telemetry metrics: {e}")


class MetricCollector:
    """Collects metrics from TermNet operations"""

    def __init__(self, analyzer: TrendAnalyzer):
        self.analyzer = analyzer

    def collect_command_metrics(self, command: str, execution_time: float,
                               success: bool, output_size: int):
        """Collect metrics from command execution"""
        self.analyzer.record_metric(
            category="commands",
            name="execution_time",
            value=execution_time,
            metadata={
                'command': command,
                'success': success,
                'output_size': output_size
            },
            tags=['performance', 'terminal']
        )

        self.analyzer.record_metric(
            category="commands",
            name="success_rate",
            value=1.0 if success else 0.0,
            metadata={'command': command},
            tags=['reliability']
        )

    def collect_agent_metrics(self, response_time: float, tokens_used: int,
                            tool_calls: int, memory_usage: float):
        """Collect metrics from agent operations"""
        self.analyzer.record_metric(
            category="agent",
            name="response_time",
            value=response_time,
            metadata={
                'tokens': tokens_used,
                'tools': tool_calls
            },
            tags=['performance', 'llm']
        )

        self.analyzer.record_metric(
            category="agent",
            name="memory_usage",
            value=memory_usage,
            tags=['resources']
        )

    def collect_validation_metrics(self, validation_time: float,
                                 rules_checked: int, violations: int):
        """Collect metrics from validation system"""
        self.analyzer.record_metric(
            category="validation",
            name="check_time",
            value=validation_time,
            metadata={
                'rules': rules_checked,
                'violations': violations
            },
            tags=['security', 'performance']
        )

        self.analyzer.record_metric(
            category="validation",
            name="violation_rate",
            value=violations / max(rules_checked, 1),
            tags=['security', 'compliance']
        )


def main():
    """Example usage and testing"""
    analyzer = TrendAnalyzer()
    collector = MetricCollector(analyzer)

    # Simulate some metrics
    import random
    import time

    print("Generating sample metrics...")
    for i in range(20):
        # Command metrics
        collector.collect_command_metrics(
            command=f"test_command_{i % 3}",
            execution_time=random.uniform(0.1, 2.0),
            success=random.random() > 0.2,
            output_size=random.randint(100, 1000)
        )

        # Agent metrics
        collector.collect_agent_metrics(
            response_time=random.uniform(0.5, 3.0),
            tokens_used=random.randint(50, 500),
            tool_calls=random.randint(0, 5),
            memory_usage=random.uniform(100, 500)
        )

        # Validation metrics
        collector.collect_validation_metrics(
            validation_time=random.uniform(0.01, 0.5),
            rules_checked=random.randint(10, 30),
            violations=random.randint(0, 3)
        )

        time.sleep(0.1)  # Small delay to spread timestamps

    print("\nGenerating reports...")
    print("\n" + "=" * 50)
    print(analyzer.generate_report("summary"))
    print("\n" + "=" * 50)
    print(analyzer.generate_report("detailed"))
    print("\n" + "=" * 50)
    print(analyzer.generate_report("alerts"))

    print("\n" + "=" * 50)
    print("Statistics:")
    stats = analyzer.get_statistics()
    for category, metrics in stats.items():
        print(f"\n{category}:")
        for name, values in metrics.items():
            print(f"  {name}: mean={values['mean']:.2f}, "
                  f"range=[{values['min']:.2f}, {values['max']:.2f}]")


if __name__ == "__main__":
    main()