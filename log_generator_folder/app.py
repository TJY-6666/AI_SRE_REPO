import time
import random
from datetime import datetime
import requests

# 正常日志列表
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

# 攻击日志列表（包含攻击特征关键词）
ATTACK_LOGS = [
    "POTENTIAL ATTACK: SQL Injection attempt detected",
    "POTENTIAL ATTACK: Multiple failed login attempts from 203.0.113.45",
    "POTENTIAL ATTACK: Brute force attack detected on port 22",
    "POTENTIAL ATTACK: SQL Injection in query parameter",
    "POTENTIAL ATTACK: Multiple failed login attempts (15 retries)",
    "POTENTIAL ATTACK: Brute force attempt with common passwords",
]

def generate_log():
    """生成一条日志（80%正常，20%攻击）"""
    if random.random() < 0:
        # 80% 正常日志
        message = random.choice(NORMAL_LOGS)
        level = "INFO"
    else:
        # 20% 攻击日志
        message = random.choice(ATTACK_LOGS)
        level = "WARN"
    
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # 毫秒级
    
    # 格式化日志
    log = f"[{timestamp}] {level}: {message}"
    return log

def main():
    """主函数：无限循环生成日志"""
    print("Service A started - Hacker attack log generator", flush=True)
    print("Sending logs to Service B...", flush=True)
    
    # 获取 Service B 的地址，本地测试默认为 localhost:5000
    # 在 k8s 中，我们会通过环境变量 SERVICE_B_URL 改变它的值
    import os
    target_url = os.getenv("SERVICE_B_URL", "http://localhost:5000/logs")
    
    try:
        while True:
            log = generate_log()
            print(f"Generated: {log}", flush=True)
            
            try:
                # 包装成 JSON 发送 POST 请求给 Service B
                response = requests.post(target_url, json={"log": log}, timeout=2)
                
                # 如果是攻击日志并且 Service B 处理了，我们抓取它的回复
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "threat_handled_mock":
                        print("🔥 [AI ASSISTANT TRIGGERED]")
                        print(data.get("recommendation") + "\n", flush=True)
            except Exception as e:
                print(f"Failed to send to Service B: {e}")
                
            time.sleep(15)  # 每15秒生成一条日志
    except KeyboardInterrupt:
        print("\nService A stopped", flush=True)

if __name__ == "__main__":
    main()
