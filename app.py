
import os
import time
import threading
import random
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# قاموس لتخزين نتائج العمليات ومتابعتها
automation_reports = {}

# واجهة مستخدم HTML مدمجة في الكود
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم الأتمتة التلقائية</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; text-align: center; color: #333; }
        .container { max-width: 500px; background: white; margin: 30px auto; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h2 { color: #007bff; margin-bottom: 20px; }
        input, button { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #ccc; box-sizing: border-box; font-size: 16px; }
        button { background-color: #007bff; color: white; border: none; cursor: pointer; font-weight: bold; transition: 0.3s; }
        button:hover { background-color: #0056b3; }
        .result-box { margin-top: 20px; padding: 15px; border-radius: 6px; background: #e9ecef; display: none; text-align: right; }
        .status-badge { display: inline-block; padding: 5px 10px; border-radius: 4px; color: white; font-weight: bold; font-size: 14px; }
        .running { background-color: #ffc107; color: #212529; }
        .completed { background-color: #28a745; }
    </style>
</head>
<body>
<div class="container">
    <h2>🤖 لوحة تحكم الأتمتة الذكية</h2>
    <p>أدخل الرابط والعدد المطلوب لبدء العملية كزائر مجهول وبأمان</p>
    <input type="url" id="fbLink" placeholder="أدخل رابط فيسبوك هنا..." required>
    <input type="number" id="reqCount" placeholder="العدد المطلوب (الحد الأقصى 50)" min="1" max="50" value="10">
    <button id="startBtn" onclick="startAutomation()">🚀 ابدأ التشغيل التلقائي</button>
    <div id="resultBox" class="result-box">
        <h3>📊 حالة العملية الحالية:</h3>
        <p><strong>المعرف:</strong> <span id="taskId">-</span></p>
        <p><strong>الحالة:</strong> <span id="taskStatus" class="status-badge">-</span></p>
        <p><strong>التقدم:</strong> <span id="taskProgress">0/0</span></p>
        <p><strong>الطلبات الناجحة ✅:</strong> <span id="taskSuccess">0</span></p>
        <p><strong>الطلبات الفاشلة ❌:</strong> <span id="taskFailed">0</span></p>
    </div>
</div>
<script>
    let intervalId = null;
    async function startAutomation() {
        const link = document.getElementById('fbLink').value;
        const count = document.getElementById('reqCount').value;
        const startBtn = document.getElementById('startBtn');
        if(!link) { alert('الرجاء إدخال الرابط أولاً!'); return; }
        startBtn.disabled = true;
        startBtn.innerText = '⏳ جاري بدء العملية...';
        try {
            const response = await fetch('/api/reports', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ link: link, count: parseInt(count) })
            });
            const result = await response.json();
            if(result.success) {
                document.getElementById('resultBox').style.display = 'block';
                document.getElementById('taskId').innerText = result.task_id;
                if(intervalId) clearInterval(intervalId);
                intervalId = setInterval(() => checkStatus(result.task_id), 1500);
            } else {
                alert('خطأ: ' + result.message);
                startBtn.disabled = false;
                startBtn.innerText = '🚀 ابدأ التشغيل التلقائي';
            }
        } catch (error) {
            alert('حدث خطأ أثناء الاتصال بالسيرفر');
            startBtn.disabled = false;
            startBtn.innerText = '🚀 ابدأ التشغيل التلقائي';
        }
    }
    async function checkStatus(taskId) {
        try {
            const response = await fetch(`/api/status/${taskId}`);
            const result = await response.json();
            if(result.success) {
                const data = result.data;
                document.getElementById('taskStatus').innerText = data.status;
                document.getElementById('taskStatus').className = 'status-badge ' + (data.status === 'Completed' ? 'completed' : 'running');
                document.getElementById('taskProgress').innerText = data.progress;
                document.getElementById('taskSuccess').innerText = data.success;
                document.getElementById('taskFailed').innerText = data.failed;
                if(data.status === 'Completed') {
                    clearInterval(intervalId);
                    const startBtn = document.getElementById('startBtn');
                    startBtn.disabled = false;
                    startBtn.innerText = '🚀 ابدأ التشغيل التلقائي';
                    alert('🎉 اكتملت العملية التلقائية بنجاح!');
                }
            }
        } catch (error) {
            console.error('Error checking status:', error);
        }
    }
</script>
</body>
</html>
"""

def fetch_free_proxies():
    proxies = []
    try:
        url = "https://proxyscrape.com"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            raw_proxies = response.text.strip().split("\r\n")
            proxies = [f"http://{p}" for p in raw_proxies if ":" in p][:40]
    except Exception as e:
        print(f"Error fetching proxies: {e}")
    return proxies

def run_automation_in_background(task_id, link, count):
    global automation_reports
    proxy_list = fetch_free_proxies()
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})
    successful_attempts = 0
    failed_attempts = 0
    for i in range(count):
        proxies = None
        if proxy_list:
            proxy = random.choice(proxy_list)
            proxies = {"http": proxy, "https": proxy}
        try:
            response = session.get(link, proxies=proxies, timeout=5)
            if response.status_code == 200:
                successful_attempts += 1
            else:
                failed_attempts += 1
            time.sleep(0.2)
        except Exception:
            failed_attempts += 1
            if proxy_list and proxy in proxy_list:
                proxy_list.remove(proxy)
            time.sleep(0.3)
        automation_reports[task_id] = {
            "status": "Running",
            "target": link,
            "total_requested": count,
            "progress": f"{successful_attempts + failed_attempts}/{count}",
            "success": successful_attempts,
            "failed": failed_attempts
        }
    automation_reports[task_id]["status"] = "Completed"

@app.get("/")
def home():
    return render_template_string(HTML_INTERFACE)

@app.post("/api/reports")
def receive_report():
    data = request.get_json(silent=True) or {}
    link = data.get("link", "").strip()
    try:
        count = int(data.get("count", 10))
    except ValueError:
        return jsonify({"success": False, "message": "Count must be a valid number"}), 400
    if count > 50:
        count = 50
        
    # 🔥 التعديل السحري والمرن هنا: دعم جميع صيغ روابط فيسبوك لمشاركة الجوال
    if "facebook.com" not in link.lower():
        return jsonify({"success": False, "message": "Invalid Facebook link"}), 400

    task_id = str(int(time.time()))
    automation_reports[task_id] = {
        "status": "Starting",
        "target": link,
        "total_requested": count,
        "progress": f"0/{count}",
        "success": 0,
        "failed": 0
    }
    thread = threading.Thread(target=run_automation_in_background, args=(task_id, link, count))
    thread.start()
    return jsonify({"success": True, "task_id": task_id})

@app.get("/api/status/<task_id>")
def get_status(task_id):
    report = automation_reports.get(task_id)
    if not report:
        return jsonify({"success": False, "message": "Task not found"}), 404
    return jsonify({"success": True, "data": report})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
