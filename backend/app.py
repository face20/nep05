# ✅ app.py — Backend Flask ที่เชื่อมต่อ Tuya + Scheduler + REST API

from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import requests, time, os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# 🌐 โหลดข้อมูลจาก ENV
TUYA_ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
TUYA_ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
TUYA_DEVICE_ID = os.getenv("TUYA_DEVICE_ID")
TUYA_UID = os.getenv("TUYA_UID")
TUYA_REGION = os.getenv("TUYA_REGION", "AY")

# 📦 เก็บข้อมูลใช้งาน
plug_data = {
    "energy_today_kwh": 0.0,
    "power_watt": 0,
    "usage_count": 0,
    "last_status": None,
    "history": []
}

# 🔐 สร้าง access token
TOKEN_CACHE = {"token": None, "expire": 0}

def get_token():
    if TOKEN_CACHE['token'] and TOKEN_CACHE['expire'] > time.time():
        return TOKEN_CACHE['token']
    url = f"https://openapi.tuya{TUYA_REGION}.com/v1.0/token?grant_type=1"
    headers = {
        "client_id": TUYA_ACCESS_ID,
        "sign": TUYA_ACCESS_SECRET,
        "sign_method": "HMAC-SHA256"
    }
    r = requests.get(url, headers=headers)
    result = r.json()
    TOKEN_CACHE['token'] = result['result']['access_token']
    TOKEN_CACHE['expire'] = time.time() + 3500
    return TOKEN_CACHE['token']

# 📡 ฟังก์ชันดึงสถานะปลั๊ก

def fetch_plug_data():
    token = get_token()
    url = f"https://openapi.tuya{TUYA_REGION}.com/v1.0/devices/{TUYA_DEVICE_ID}/status"
    headers = {"access_token": token, "client_id": TUYA_ACCESS_ID, "sign_method": "HMAC-SHA256"}
    res = requests.get(url, headers=headers).json()

    watt = 0
    kwh_today = 0
    is_on = False

    for item in res['result']:
        if item['code'] == 'cur_power': watt = float(item['value'])
        if item['code'] == 'cur_current': kwh_today = float(item['value']) / 1000.0
        if item['code'] == 'switch': is_on = item['value']

    if plug_data['last_status'] is False and is_on is True:
        plug_data['usage_count'] += 1

    plug_data['last_status'] = is_on
    plug_data['energy_today_kwh'] = round(kwh_today, 3)
    plug_data['power_watt'] = round(watt, 2)
    plug_data['history'].append({"time": time.strftime("%H:%M"), "watt": watt})
    if len(plug_data['history']) > 50:
        plug_data['history'].pop(0)

# ⏱ Scheduler ทุก 5 นาที
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_plug_data, 'interval', minutes=5)
scheduler.start()

@app.route("/api/data")
def get_data():
    return jsonify(plug_data)

@app.route("/")
def home():
    return {"status": "Tuya Smart Plug Backend is running"}

if __name__ == "__main__":
    fetch_plug_data()
    app.run(host="0.0.0.0", port=5000)
# Backend placeholder for Tuya API integration
