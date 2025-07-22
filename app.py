from flask import Flask, render_template, request
import threading
from queue import Queue
import requests
import random
import string
import json
import hashlib
from faker import Faker

app = Flask(__name__)

# ---------------------- Helpers ----------------------
def generate_random_string(length):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def get_mail_domains(proxy=None):
    url = "https://api.mail.tm/domains"
    try:
        response = requests.get(url, proxies=proxy, timeout=10)
        if response.status_code == 200:
            return response.json()['hydra:member']
    except:
        return None
    return None

def create_mail_tm_account(proxy=None):
    fake = Faker()
    mail_domains = get_mail_domains(proxy)
    if not mail_domains:
        return None
    domain = random.choice(mail_domains)['domain']
    username = generate_random_string(10)
    password = fake.password()
    data = {
        "address": f"{username}@{domain}",
        "password": password
    }
    try:
        res = requests.post("https://api.mail.tm/accounts", json=data, proxies=proxy, timeout=10)
        if res.status_code == 201:
            return username + '@' + domain, password, fake.first_name(), fake.last_name(), fake.date_of_birth(minimum_age=18, maximum_age=45)
    except:
        return None
    return None

def _call(url, params, proxy=None):
    headers = {
        'User-Agent': '[FBAN/FB4A;FBAV/35.0.0.48.273;FBLC/en_US;FBDV/Nexus 7;]'
    }
    try:
        response = requests.post(url, data=params, headers=headers, proxies=proxy, timeout=10)
        return response.json()
    except:
        return {}

def register_facebook_account(email, password, first_name, last_name, birthday, proxy=None):
    api_key = '882a8490361da98702bf97a021ddc14d'
    secret = '62f8ce9f74b12f84c123cc23437a4a32'
    gender = random.choice(['M', 'F'])
    req = {
        'api_key': api_key,
        'attempt_login': True,
        'birthday': birthday.strftime('%Y-%m-%d'),
        'client_country_code': 'EN',
        'fb_api_caller_class': 'com.facebook.registration.protocol.RegisterAccountMethod',
        'fb_api_req_friendly_name': 'registerAccount',
        'firstname': first_name,
        'format': 'json',
        'gender': gender,
        'lastname': last_name,
        'email': email,
        'locale': 'en_US',
        'method': 'user.register',
        'password': password,
        'reg_instance': generate_random_string(32),
        'return_multiple_errors': True
    }

    sig = ''.join(f'{k}={v}' for k, v in sorted(req.items()))
    req['sig'] = hashlib.md5((sig + secret).encode()).hexdigest()

    result = _call('https://b-api.facebook.com/method/user.register', req, proxy)
    return {
        "email": email,
        "password": password,
        "name": f"{first_name} {last_name}",
        "birthday": str(birthday),
        "gender": gender,
        "result": result
    }

def load_proxies():
    try:
        with open("proxies.txt") as f:
            return [{"http": f"http://{line.strip()}"} for line in f.readlines()]
    except:
        return []

# ---------------------- Flask Routes ----------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        count = int(request.form.get("count"))
        proxies = load_proxies()
        accounts = []
        for _ in range(count):
            proxy = random.choice(proxies) if proxies else None
            data = create_mail_tm_account(proxy)
            if data:
                email, pw, fn, ln, bd = data
                acc = register_facebook_account(email, pw, fn, ln, bd, proxy)
                accounts.append(acc)
        return render_template("index.html", results=accounts)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)