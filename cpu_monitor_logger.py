#!/usr/bin/env python3
import datetime
import signal
import sys
import time

import psutil


def signal_handler(sig, frame):
    print("\n\nMonitoring stopped by user")
    sys.exit(0)


def monitor_cpu(duration=30, interval=2):
    signal.signal(signal.SIGINT, signal_handler)

    log_file = "cpu_monitor.log"
    start_time = time.time()

    print(f"Starting CPU monitoring for {duration} seconds...")
    print(f"Logging to: {log_file}")
    print("Press Ctrl+C to stop\n")

    with open(log_file, "w") as f:
        f.write(f"CPU Monitoring Log - Started at {datetime.datetime.now()}\n")
        f.write("=" * 60 + "\n")
        f.write(f"{'Timestamp':<20} {'CPU %':<10} {'Per Core'}\n")
        f.write("-" * 60 + "\n")

        while time.time() - start_time < duration:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=0, percpu=True)

            log_entry = f"{timestamp:<20} {cpu_percent:<10.1f} {cpu_per_core}"

            print(
                f"[{timestamp}] CPU: {cpu_percent:.1f}% | Per core: {[f'{c:.1f}%' for c in cpu_per_core]}"
            )

            f.write(log_entry + "\n")
            f.flush()

            time.sleep(interval - 1)

        f.write("-" * 60 + "\n")
        f.write(f"Monitoring completed at {datetime.datetime.now()}\n")

        cpu_info = {
            "CPU Count (Logical)": psutil.cpu_count(logical=True),
            "CPU Count (Physical)": psutil.cpu_count(logical=False),
            "CPU Frequency": (
                f"{psutil.cpu_freq().current:.2f} MHz" if psutil.cpu_freq() else "N/A"
            ),
        }

        f.write("\nSystem Information:\n")
        for key, value in cpu_info.items():
            f.write(f"  {key}: {value}\n")

    print(f"\nMonitoring complete! Results saved to {log_file}")
    return log_file


if __name__ == "__main__":
    monitor_cpu(duration=30, interval=2)
