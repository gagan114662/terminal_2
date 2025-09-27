import psutil

print("Monitoring CPU usage for 5 seconds...")
for i in range(5):
    cpu = psutil.cpu_percent(interval=1)
    print(f"CPU usage: {cpu}%")
