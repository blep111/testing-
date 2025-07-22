from flask import Flask, render_template, request
import threading
from queue import Queue
import requests
import random
import string
from faker import Faker
import hashlib

app = Flask(__name__)
fake = Faker()

def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_mail_domains(proxy=None):
    url = "https://api.mail.tm/domains"
    try:
        response = requests.get(url, proxies=proxy)
        if response.status_code == 200:
            return response.json()['hydra:member']
        else:
            return None
    except:
        return None

def create_mail_tm_account(proxy=None):
    mail_domains = get_mail_domains(proxy)
    if mail_domains:
        domain = random.choice(mail_domains)['domain']
        username = generate_random_string(10)
        password = fake.password()
        birthday = fake.date_of_birth(minimum_age=18, maximum_age=45)
        first_name = fake.first_name()
        last_name = fake.last_name()
        url = "https://api.mail.tm/accounts"
        headers = {"Content-Type": "application/json"}
        data = {"address": f"{username}@{domain}", "password": password}
        try:
            response = requests.post(url, headers=headers, json=data, proxies=proxy)
            if response.status_code == 201:
                return f"{username}@{domain}", password, first_name, last_name, birthday
        except:
            return None, None, None, None, None
    return None, None, None, None, None

def register_facebook_account(email, password, first_name, last_name, birthday, proxy=None):
    api_key = '882a8490361da98702bf97a021ddc14d'
    secret = '62f8ce9f74b12f84c123cc23437a4a32'
    gender = random.choice(['M', 'F'])
    req = {
        'api_key': api_key, 'attempt_login': True, 'birthday': birthday.strftime('%Y-%m-%d'),
        'client_country_code': 'EN', 'fb_api_caller_class': 'com.facebook.registration.protocol.RegisterAccountMethod',
        'fb_api_req_friendly_name': 'registerAccount', 'firstname': first_name, 'format': 'json',
        'gender': gender, 'lastname': last_name, 'email': email, 'locale': 'en_US',
        'method': 'user.register', 'password': password, 'reg_instance': generate_random_string(32),
        'return_multiple_errors': True
    }
    sorted_req = sorted(req.items(), key=lambda x: x[0])
    sig = ''.join(f'{k}={v}' for k, v in sorted_req)
    ensig = hashlib.md5((sig + secret).encode()).hexdigest()
    req['sig'] = ensig
    headers = {
        'User-Agent': '[FBAN/FB4A;FBAV/35.0.0.48.273;FBDM/{density=1.3,width=800,height=1205};FBLC/en_US;FBCR/;FBPN/com.facebook.katana;FBDV/Nexus 7;FBSV/4.1.1;FBBK/0;]'
    }
    response = requests.post('https://b-api.facebook.com/method/user.register', data=req, headers=headers, proxies=proxy)
    reg = response.json()
    return reg.get('new_user_id'), reg.get('session_info', {}).get('access_token')

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    if request.method == "POST":
        amount = int(request.form.get("amount", 1))
        proxy_list = open("proxies.txt").read().splitlines()
        for _ in range(amount):
            proxy = random.choice(proxy_list).strip()
            proxy_dict = {"http": f"http://{proxy}"}
            email, password, fname, lname, birthday = create_mail_tm_account(proxy_dict)
            if email:
                user_id, token = register_facebook_account(email, password, fname, lname, birthday, proxy_dict)
                message += f"Generated: {email} | ID: {user_id} | Token: {token}<br>"
            else:
                message += "Failed to generate account.<br>"
    return render_template("index.html", message=message)

