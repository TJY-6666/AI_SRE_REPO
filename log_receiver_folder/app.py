import os
import sys
import uuid
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from google import genai

app = Flask(__name__)
app.config["TRUSTED_HOSTS"] = [
    "localhost",
    "127.0.0.1",
    "log-receiver",
    "log-receiver:5000",
    "log_receiver_container",
    "log_receiver_container:5000",
]

ATTACK_KEYWORDS = [
    "sql injection",
    "multiple failed login",
    "brute force",
    "potential attack",
]

MOCK_MESSAGE = (
    "🚨 [系统防火墙 - 基础拦截模式] 检测到明显的恶意流量注入行为。\n"
    "**当前防御库状态:** 依靠传统安全策略初步拦截成功，已记录黑名单。\n"
    "**行动建议:** 因不确认攻击源真实意图，等待安全工程师授权，点击下方唤醒 Gemini 大模型进行意图溯源分析..."
)

# 用于在内存中缓存最新日志，方便前端实时拉取（为了教学简单，不用数据库）
alerts = []

def is_threat(log_line: str) -> bool:
    text = log_line.lower()
    return any(keyword in text for keyword in ATTACK_KEYWORDS)

def build_prompt(log_line: str) -> str:
    return (
        "You are an SRE security assistant. "
        "Analyze the following log for risk. "
        "Reply in 3 short sections: (1) Threat summary, (2) Why it is risky, "
        "(3) Recommended actions.\n\n"
        f"Log: {log_line}"
    )

def ask_gemini(log_line: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

    if not api_key:
        return (
            "[MOCK MODE] GEMINI API KEY missed. \n"
            "**Threat Summary:** Immediate Attention Required.\n"
            "**Why it is risky:** Could lead to unauthorized system access.\n"
            "**Recommended actions:** Block the source IP and rotate credentials."
        )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=build_prompt(log_line),
        )
        if getattr(response, "text", None):
            return response.text.strip()
        return "Model returned no text response."
    except Exception as exc:
        return f"[GEMINI ERROR] {exc}."

# 接收黑客日志的内网接口
@app.route('/logs', methods=['POST'])
def receive_logs():
    raw = request.get_data(as_text=True).strip()
    data = None
    if raw:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"log": raw}
    if data is None:
        data = request.get_json(force=True, silent=True)
    if not data or 'log' not in data:
        print(
            "Bad /logs payload: "
            f"content_type={request.content_type}, content_length={request.content_length}, raw={raw}",
            flush=True,
        )
        return jsonify({"status": "error", "message": "No log data received"}), 400
        
    log_line = data['log']
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    threat_detected = is_threat(log_line)

    if threat_detected:
        print(f"\n[{now}] THREAT DETECTED: {log_line}", flush=True)
        print("Holding AI analysis until manual trigger.", flush=True)
    else:
        print(f"[{now}] INFO LOG: {log_line}", flush=True)

    # 将日志记录存入全局列表 (保留最新的 50 条)，供前台网站提取
    alert_id = str(uuid.uuid4())
    alert = {
        "id": alert_id,
        "time": now,
        "log": log_line,
        "recommendation": MOCK_MESSAGE if threat_detected else "Normal activity detected. No action required.",
        "analyzed": False,
        "is_threat": threat_detected,
    }
    alerts.insert(0, alert)
    if len(alerts) > 50:
        alerts.pop()

    if threat_detected:
        return jsonify({"status": "threat_handled_mock", "id": alert_id}), 200

    return jsonify({"status": "ok", "id": alert_id}), 200

# 唤醒 AI 的内网接口
@app.route('/api/analyze/<alert_id>', methods=['POST'])
def analyze_alert(alert_id):
    for alert in alerts:
        if alert["id"] == alert_id:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] manual AI trigger for {alert_id}")
            result = ask_gemini(alert["log"])
            alert["recommendation"] = result
            alert["analyzed"] = True
            return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Alert not found"}), 404

# 供前端网站每秒查询最新警报的接口
@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    return jsonify(alerts)


# 视觉化超级酷炫的前端页面 (炫酷的赛博朋克深色风格)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI SRE Watchdog Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --surface: #1e293b;
            --primary: #0ea5e9;
            --danger: #ef4444;
            --text: #f8fafc;
            --text-muted: #94a3b8;
        }
        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100vh;
            box-sizing: border-box;
        }
        h1 {
            font-size: 2.5rem;
            background: linear-gradient(90deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            text-align: center;
        }
        .subtitle {
            color: var(--text-muted);
            margin-bottom: 2rem;
            font-weight: 300;
            font-size: 1.1rem;
        }
        .container {
            display: flex;
            width: 100%;
            max-width: 1400px;
            gap: 2rem;
            flex: 1;
            min-height: 0;
        }
        .left-panel {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            padding-right: 1rem;
        }
        .right-panel {
            flex: 1;
            background-color: var(--surface);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 2rem;
            overflow-y: auto;
            position: relative;
        }
        .alert-card {
            background-color: var(--surface);
            border-left: 4px solid var(--danger);
            border-radius: 12px;
            padding: 1.5rem;
            cursor: pointer;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease, background-color 0.2s;
        }
        .alert-card:hover {
            transform: translateY(-2px);
            background-color: #2a3b52;
            border-left: 4px solid #f87171;
        }
        .alert-card.active {
            border-left: 4px solid var(--primary);
            background-color: #2a3b52;
        }
        .alert-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.8rem;
        }
        .badge {
            background-color: rgba(239, 68, 68, 0.2);
            color: #fca5a5;
            padding: 0.3rem 0.8rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.05em;
        }
        .time {
            color: var(--text-muted);
            font-size: 0.85rem;
            font-family: monospace;
        }
        .log-code {
            background-color: #000;
            padding: 1rem;
            border-radius: 8px;
            font-family: monospace;
            color: #ef4444;
            overflow-x: auto;
            font-size: 0.9rem;
            white-space: pre-wrap;
            word-wrap: break-word;
            border: 1px solid #334155;
        }
        .detail-header {
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .ai-icon {
            color: var(--primary);
            font-weight: 700;
        }
        .recommendation {
            line-height: 1.7;
            color: #e2e8f0;
            font-size: 1.05rem;
        }
        .watermark {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: rgba(255,255,255,0.05);
            font-size: 6rem;
            font-weight: bold;
            pointer-events: none;
        }
        .pulse {
            display: inline-block;
            width: 10px;
            height: 10px;
            background-color: #22c55e;
            border-radius: 50%;
            margin-right: 10px;
            box-shadow: 0 0 10px #22c55e;
            animation: blink 2s infinite;
        }
        @keyframes blink {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
            100% { opacity: 1; transform: scale(1); }
        }
        .ai-button {
            margin-top: 1.2rem;
            background: linear-gradient(135deg, #6366f1, #3b82f6);
            color: white;
            border: none;
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            font-family: 'Outfit', sans-serif;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px -3px rgba(99, 102, 241, 0.5);
            width: 100%;
        }
        .ai-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px -3px rgba(99, 102, 241, 0.6);
        }
        .ai-button:active {
            transform: translateY(0);
        }
        .ai-button:disabled {
            background: #475569;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg); }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #475569; }
    </style>
</head>
<body>
    <h1>AI SRE Watchdog</h1>
    <div class="subtitle">Kubernetes Cloud Security Intelligence | Powered by Gemini</div>
    
    <div class="container">
        <!-- 左侧: 警告列表 -->
        <div class="left-panel" id="alert-list">
        </div>
        
        <!-- 右侧: AI解析面板 -->
        <div class="right-panel" id="ai-panel">
            <div class="watermark">AI SYS</div>
            <div style="text-align: center; color: var(--text-muted); margin-top: 40%;">
                Select a threat on the left.
            </div>
        </div>
    </div>

    <script>
        let currentAlerts = [];
        let selectedAlertIndex = -1;

        async function fetchAlerts() {
            try {
                const response = await fetch('/api/alerts');
                currentAlerts = await response.json();
                renderLeftPanel();
                if (selectedAlertIndex !== -1 && currentAlerts[selectedAlertIndex]) {
                    renderRightPanel(selectedAlertIndex);
                }
            } catch (error) {
                console.error('Error fetching alerts:', error);
            }
        }

        function renderLeftPanel() {
            const listEl = document.getElementById('alert-list');
            if (currentAlerts.length === 0) {
                listEl.innerHTML = `
                    <div style="text-align: center; color: var(--text-muted); padding: 5rem 2rem; border: 2px dashed rgba(255,255,255,0.1); border-radius: 12px; background: var(--surface);">
                        <span class="pulse"></span> System Secure. Listening for logs...
                    </div>
                `;
                return;
            }
            
            listEl.innerHTML = '';
            currentAlerts.forEach((alert, index) => {
                const card = document.createElement('div');
                card.className = 'alert-card';
                if (index === selectedAlertIndex) {
                    card.classList.add('active');
                }
                
                const badgeLabel = alert.is_threat ? '⚠️ THREAT ISOLATED' : 'INFO LOG';
                const badgeColor = alert.is_threat
                    ? 'background-color: rgba(239, 68, 68, 0.2); color: #fca5a5;'
                    : 'background-color: rgba(14, 165, 233, 0.18); color: #7dd3fc;';
                const logColor = alert.is_threat ? '#ef4444' : '#38bdf8';

                card.innerHTML = `
                    <div class="alert-header">
                        <span class="badge" style="${badgeColor}">${badgeLabel}</span>
                        <span class="time">${alert.time}</span>
                    </div>
                    <div class="log-code" style="margin-bottom:0; padding:0.5rem; color:${logColor};">> ${alert.log}</div>
                `;
                card.onclick = () => selectAlert(index);
                listEl.appendChild(card);
            });
        }

        function selectAlert(index) {
            selectedAlertIndex = index;
            renderLeftPanel(); // Update active class
            renderRightPanel(index);
        }

        function renderRightPanel(index) {
            const alert = currentAlerts[index];
            const panel = document.getElementById('ai-panel');
            
            const formattedRec = alert.recommendation
                .replace(/\\n/g, '<br>')
                .replace(/\\*\\*(.*?)\\*\\*/g, '<strong style="color:var(--primary)">$1</strong>')
                .replace(/\\*(.*?)\\*/g, '<em>$1</em>');
            
            let btnHtml = '';
            if (alert.is_threat && !alert.analyzed) {
                btnHtml = `<button class="ai-button" onclick="triggerAI('${alert.id}')">🔮 授权并调用大模型进行深度溯源</button>`;
            }

            const title = alert.is_threat
                ? (alert.analyzed ? 'Gemini Analysis Strategy' : 'Base Firewall System')
                : 'System Activity Overview';
            const icon = alert.is_threat
                ? (alert.analyzed ? '✨' : '🛡️')
                : 'ℹ️';
            const borderColor = alert.is_threat ? 'rgba(239, 68, 68, 0.4)' : 'rgba(14, 165, 233, 0.35)';
            const logColor = alert.is_threat ? '#ef4444' : '#38bdf8';

            panel.innerHTML = `
                <div class="detail-header">
                    <span class="ai-icon">${icon}</span> ${title}
                </div>
                <div class="time" style="margin-bottom: 1rem;">Log Time: ${alert.time}</div>
                <div class="log-code" style="border-color: ${borderColor}; color:${logColor};">> ${alert.log}</div>
                <div class="recommendation" style="margin-top: 1.5rem;">
                    ${formattedRec}
                </div>
                ${btnHtml}
            `;
        }

        async function triggerAI(alertId) {
            const btn = document.querySelector('.ai-button');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = `<span class="pulse" style="background:#fff;box-shadow:none;"></span> Google Gemini 正在深度思考中...`;
            }
            try {
                await fetch(`/api/analyze/${alertId}`, { method: 'POST' });
                fetchAlerts(); 
            } catch(e) {
                console.error(e);
                if(btn) {
                    btn.disabled = false;
                    btn.innerHTML = `❌ 调用失败，点击重试`;
                }
            }
        }

        setInterval(fetchAlerts, 2000); 
        fetchAlerts();
    </script>
</body>
</html>
"""

# 把网站大门敞开，当你在浏览器访问 / 时，返回上面那个极为惊艳的 HTML
@app.route('/', methods=['GET'])
def dashboard():
    return render_template_string(HTML_TEMPLATE)


if __name__ == "__main__":
    print("Service B started - AI Security Web Dashboard", flush=True)
    app.run(host="0.0.0.0", port=5000)
