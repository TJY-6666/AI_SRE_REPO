import time
import random
from datetime import datetime
import requests

# Normal log samples
NORMAL_LOGS = [
    "Database query executed",
    "User login successful",
    "API request processed",
    "Cache updated",
    "File uploaded",
    "Configuration reloaded",
    "Health check passed",
    "Connection established",
]

# Attack log samples (contain attack signature keywords)
ATTACK_LOGS = [
    "POTENTIAL ATTACK: SQL Injection attempt detected",
    "POTENTIAL ATTACK: Multiple failed login attempts from 203.0.113.45",
    "POTENTIAL ATTACK: Brute force attack detected on port 22",
    "POTENTIAL ATTACK: SQL Injection in query parameter",
    "POTENTIAL ATTACK: Multiple failed login attempts (15 retries)",
    "POTENTIAL ATTACK: Brute force attempt with common passwords",
]

def generate_log():
    """Generate one log line (current behavior: 20% normal, 80% attack)."""
    if random.random() < 0.2:
        # Normal log path
        message = random.choice(NORMAL_LOGS)
        level = "INFO"
    else:
        # Attack log path
        message = random.choice(ATTACK_LOGS)
        level = "WARN"
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Millisecond precision
    
    # Format log line
    log = f"[{timestamp}] {level}: {message}"
    return log

def main():
    """Main loop: generate logs continuously."""
    print("Service A started - Hacker attack log generator", flush=True)
    print("Sending logs to Service B...", flush=True)
    
    # Read Service B URL, defaulting to localhost for local testing.
    # In Kubernetes, this is provided via SERVICE_B_URL.
    import os
    target_url = os.getenv("SERVICE_B_URL", "http://localhost:5000/logs")
    
    try:
        while True:
            log = generate_log()
            print(f"Generated: {log}", flush=True)
            
            try:
                # Send to Service B as JSON via POST
                response = requests.post(target_url, json={"log": log}, timeout=2)
                
                # If Service B handled a threat log, print the recommendation.
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "threat_handled_mock":
                        print("🔥 [AI ASSISTANT TRIGGERED]")
                        print(data.get("recommendation") + "\n", flush=True)
            except Exception as e:
                print(f"Failed to send to Service B: {e}")
                
            time.sleep(15)  # Generate one log every 15 seconds
    except KeyboardInterrupt:
        print("\nService A stopped", flush=True)

if __name__ == "__main__":
    main()
