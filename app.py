from flask import Flask, render_template, request, jsonify import threading from queue import Queue import requests import random import string from faker import Faker

app = Flask(name) fake = Faker()

Check if a proxy is working

def test_proxy(proxy, q, valid): try: res = requests.get('https://api.mail.tm', proxies={"http": proxy}, timeout=5) if res.status_code == 200: valid.append(proxy) except: pass q.task_done()

Load and test proxies in threads

def get_working_proxies(proxies): q = Queue() valid_proxies = [] for proxy in proxies: q.put(proxy) for _ in range(10): t = threading.Thread(target=worker, args=(q, valid_proxies)) t.daemon = True t.start() q.join() return valid_proxies

def worker(q, valid): while not q.empty(): proxy = q.get() test_proxy(proxy, q, valid)

Get domains from mail.tm

def get_mail_domains(): try: r = requests.get("https://api.mail.tm/domains") return [d['domain'] for d in r.json().get('hydra:member', [])] except: return []

Create temp mail account

def create_mail_account(): domains = get_mail_domains() if not domains: return None domain = random.choice(domains) username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) password = fake.password() email = f"{username}@{domain}" data = {"address": email, "password": password} try: r = requests.post("https://api.mail.tm/accounts", json=data) if r.status_code == 201: return {"email": email, "password": password} except: pass return None

@app.route("/") def index(): return render_template("index.html")

@app.route("/check_proxies", methods=["POST"]) def check_proxies(): proxy_list = request.json.get("proxies", []) working = get_working_proxies(proxy_list) return jsonify({"working": working})

@app.route("/generate_email", methods=["GET"]) def generate_email(): result = create_mail_account() return jsonify(result or {"error": "failed"})

if name == "main": app.run(host="0.0.0.0", port=10000)  # Required for Render

