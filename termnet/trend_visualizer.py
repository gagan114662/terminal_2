"""
TermNet Trend Visualization System
Creates charts and visualizations for trend analysis
"""

import sqlite3
from datetime import datetime, timedelta


class TrendVisualizer:
    """Generate ASCII-based visualizations for trend data"""

    def __init__(self, db_path: str = "termnet_trends.db"):
        self.db_path = db_path

    def create_line_chart(
        self,
        data: list[tuple[str, float]],
        width: int = 60,
        height: int = 20,
        title: str = "",
    ) -> str:
        """Create ASCII line chart"""
        if not data:
            return "No data to display"

        values = [v for _, v in data]
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1

        # Normalize values to chart height
        normalized = [(v - min_val) / range_val * (height - 1) for v in values]

        # Create chart grid
        chart = [[" " for _ in range(width)] for _ in range(height)]

        # Add Y-axis
        for i in range(height):
            chart[i][0] = "│"

        # Add X-axis
        for j in range(width):
            chart[height - 1][j] = "─"

        chart[height - 1][0] = "└"

        # Plot data points
        if len(data) > 1:
            x_step = (width - 5) / (len(data) - 1)
            for i, norm_val in enumerate(normalized):
                x = int(i * x_step) + 2
                y = height - 2 - int(norm_val)
                if 0 <= y < height and 0 <= x < width:
                    chart[y][x] = "●"

                    # Connect points with lines
                    if i > 0:
                        prev_x = int((i - 1) * x_step) + 2
                        prev_y = height - 2 - int(normalized[i - 1])
                        self._draw_line(chart, prev_x, prev_y, x, y)

        # Add labels
        chart_lines = []
        if title:
            chart_lines.append(f"  {title}")
            chart_lines.append("")

        # Add max value label
        chart_lines.append(f"{max_val:>8.2f} ┤" + "".join(chart[0]))

        # Add middle lines
        for i in range(1, height - 1):
            if i == height // 2:
                mid_val = (max_val + min_val) / 2
                chart_lines.append(f"{mid_val:>8.2f} ┤" + "".join(chart[i]))
            else:
                chart_lines.append(f"{'':>8} │" + "".join(chart[i]))

        # Add min value label
        chart_lines.append(f"{min_val:>8.2f} └" + "".join(chart[height - 1][1:]))

        # Add time labels
        if len(data) > 0:
            first_time = datetime.fromisoformat(data[0][0])
            last_time = datetime.fromisoformat(data[-1][0])
            time_label = f"{'':>10}{first_time.strftime('%H:%M')}{'':>{width-20}}{last_time.strftime('%H:%M')}"
            chart_lines.append(time_label)

        return "\n".join(chart_lines)

    def _draw_line(self, chart: list[list[str]], x1: int, y1: int, x2: int, y2: int):
        """Draw a line between two points"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            if 0 <= y1 < len(chart) and 0 <= x1 < len(chart[0]):
                if chart[y1][x1] == " ":
                    if dx > dy:
                        chart[y1][x1] = "─"
                    elif dy > dx:
                        chart[y1][x1] = "│"
                    else:
                        chart[y1][x1] = "/"

            if x1 == x2 and y1 == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def create_bar_chart(
        self, data: dict[str, float], width: int = 50, title: str = ""
    ) -> str:
        """Create horizontal bar chart"""
        if not data:
            return "No data to display"

        max_val = max(data.values()) if data else 1
        chart_lines = []

        if title:
            chart_lines.append(title)
            chart_lines.append("=" * (width + 20))

        for label, value in data.items():
            bar_width = int((value / max_val) * width)
            bar = "█" * bar_width
            chart_lines.append(f"{label:>15} │{bar} {value:.2f}")

        return "\n".join(chart_lines)

    def create_histogram(
        self, values: list[float], bins: int = 10, width: int = 50, title: str = ""
    ) -> str:
        """Create histogram from values"""
        if not values:
            return "No data to display"

        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1
        bin_width = range_val / bins

        # Count values in each bin
        bin_counts = [0] * bins
        for value in values:
            bin_index = min(int((value - min_val) / bin_width), bins - 1)
            bin_counts[bin_index] += 1

        max_count = max(bin_counts) if bin_counts else 1

        chart_lines = []
        if title:
            chart_lines.append(title)
            chart_lines.append("=" * (width + 20))

        for i, count in enumerate(bin_counts):
            bin_start = min_val + i * bin_width
            bin_end = bin_start + bin_width
            bar_width = int((count / max_count) * width)
            bar = "█" * bar_width
            chart_lines.append(f"[{bin_start:>6.2f}-{bin_end:>6.2f}] │{bar} {count}")

        return "\n".join(chart_lines)

    def create_sparkline(self, values: list[float], width: int = 20) -> str:
        """Create a compact sparkline visualization"""
        if not values:
            return ""

        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1

        # Sparkline characters from low to high
        sparks = "▁▂▃▄▅▆▇█"

        # Sample or aggregate values to fit width
        if len(values) > width:
            # Sample evenly
            step = len(values) / width
            sampled = [values[int(i * step)] for i in range(width)]
        else:
            sampled = values

        # Convert to sparkline
        sparkline = ""
        for v in sampled:
            normalized = (v - min_val) / range_val
            spark_index = min(int(normalized * (len(sparks) - 1)), len(sparks) - 1)
            sparkline += sparks[spark_index]

        return sparkline

    def create_dashboard(self, window_hours: int = 24) -> str:
        """Create a comprehensive dashboard"""
        dashboard_lines = [
            "╔" + "═" * 78 + "╗",
            "║" + " TERMNET TREND ANALYSIS DASHBOARD ".center(78) + "║",
            "╠" + "═" * 78 + "╣",
        ]

        with sqlite3.connect(self.db_path) as conn:
            # Get recent metrics summary
            start_time = (datetime.now() - timedelta(hours=window_hours)).isoformat()

            # Command metrics
            cursor = conn.execute(
                """
                SELECT AVG(value), MIN(value), MAX(value), COUNT(*)
                FROM metrics
                WHERE category = 'commands' AND name = 'execution_time'
                AND timestamp >= ?
            """,
                (start_time,),
            )

            avg_time, min_time, max_time, cmd_count = cursor.fetchone()

            if avg_time:
                dashboard_lines.extend(
                    [
                        "║ COMMAND PERFORMANCE" + " " * 58 + "║",
                        f"║   Executions: {cmd_count or 0:>6} | Avg: {avg_time or 0:.2f}s | "
                        f"Min: {min_time or 0:.2f}s | Max: {max_time or 0:.2f}s"
                        + " " * 20
                        + "║",
                    ]
                )

            # Recent trend sparklines
            categories = ["commands", "agent", "validation"]
            dashboard_lines.append("║" + " " * 78 + "║")
            dashboard_lines.append("║ RECENT TRENDS (Sparklines)" + " " * 51 + "║")

            for category in categories:
                cursor = conn.execute(
                    """
                    SELECT value FROM metrics
                    WHERE category = ? AND name LIKE '%time%'
                    AND timestamp >= ?
                    ORDER BY timestamp
                    LIMIT 50
                """,
                    (category, start_time),
                )

                values = [row[0] for row in cursor.fetchall()]
                if values:
                    sparkline = self.create_sparkline(values, 40)
                    dashboard_lines.append(
                        f"║   {category:>12}: {sparkline}"
                        + " " * (78 - 17 - len(sparkline))
                        + "║"
                    )

            # Recent alerts
            cursor = conn.execute(
                """
                SELECT content FROM reports
                WHERE report_type = 'alerts'
                ORDER BY created_at DESC
                LIMIT 1
            """
            )

            result = cursor.fetchone()
            if result:
                alert_lines = result[0].split("\n")
                dashboard_lines.append("║" + " " * 78 + "║")
                dashboard_lines.append("║ RECENT ALERTS" + " " * 64 + "║")
                for line in alert_lines[5:8]:  # Show first 3 alerts
                    if line.strip():
                        truncated = line[:75] if len(line) > 75 else line
                        dashboard_lines.append(
                            "║ " + truncated + " " * (77 - len(truncated)) + "║"
                        )

        dashboard_lines.append("╚" + "═" * 78 + "╝")

        return "\n".join(dashboard_lines)

    def visualize_metric(self, category: str, name: str, window_hours: int = 24) -> str:
        """Visualize a specific metric"""
        start_time = datetime.now() - timedelta(hours=window_hours)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT timestamp, value FROM metrics
                WHERE category = ? AND name = ?
                AND timestamp >= ?
                ORDER BY timestamp
            """,
                (category, name, start_time.isoformat()),
            )

            data = cursor.fetchall()

        if not data:
            return f"No data found for {category}/{name}"

        title = f"{category}/{name} - Last {window_hours} hours"
        chart = self.create_line_chart(data, title=title)

        # Add statistics
        values = [v for _, v in data]
        stats_lines = [
            "",
            "Statistics:",
            f"  Count: {len(values)}",
            f"  Mean:  {sum(values)/len(values):.2f}",
            f"  Min:   {min(values):.2f}",
            f"  Max:   {max(values):.2f}",
        ]

        return chart + "\n" + "\n".join(stats_lines)


def main():
    """Example usage"""
    import random
    import time

    from termnet.trend_analysis import MetricCollector, TrendAnalyzer

    # Generate some sample data
    analyzer = TrendAnalyzer()
    collector = MetricCollector(analyzer)

    print("Generating sample metrics for visualization...")
    for i in range(30):
        collector.collect_command_metrics(
            command=f"test_cmd_{i % 5}",
            execution_time=random.uniform(0.1, 2.0) + (i * 0.05),
            success=random.random() > 0.1,
            output_size=random.randint(100, 1000),
        )

        collector.collect_agent_metrics(
            response_time=random.uniform(0.5, 3.0) + (i * 0.03),
            tokens_used=random.randint(50, 500),
            tool_calls=random.randint(0, 5),
            memory_usage=random.uniform(100, 500) + (i * 2),
        )

        time.sleep(0.05)

    # Create visualizations
    visualizer = TrendVisualizer()

    print("\n" + "=" * 80)
    print(visualizer.create_dashboard())

    print("\n" + "=" * 80)
    print(visualizer.visualize_metric("commands", "execution_time", 1))

    print("\n" + "=" * 80)
    # Create bar chart example
    stats = {
        "Commands": 145,
        "Validations": 298,
        "Agent Calls": 67,
        "Tool Uses": 89,
        "Errors": 12,
    }
    print(visualizer.create_bar_chart(stats, title="Operation Counts"))

    print("\n" + "=" * 80)
    # Create histogram example
    response_times = [random.uniform(0.1, 5.0) for _ in range(100)]
    print(
        visualizer.create_histogram(response_times, title="Response Time Distribution")
    )


if __name__ == "__main__":
    main()
