from flask import Flask, render_template_string, jsonify, request, session
import time
import socket
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Секретный ключ для сессий

# Конфигурация
APP_NAME = "🔒 Личка"
PASSWORD = "011225"  # Пароль для доступа
ENCRYPTION_KEY = "termite_secret_key_2026"  # Ключ для шифрования

# Храним сообщения (в реальном приложении лучше использовать БД)
messages = []
users = {}

# Простое шифрование/дешифрование
def simple_encrypt(text):
    """Простое шифрование для демонстрации"""
    encrypted = ""
    for i, char in enumerate(text):
        key_char = ENCRYPTION_KEY[i % len(ENCRYPTION_KEY)]
        encrypted += chr(ord(char) ^ ord(key_char))
    return encrypted.encode('latin-1').hex()

def simple_decrypt(hex_text):
    """Расшифровка"""
    try:
        text = bytes.fromhex(hex_text).decode('latin-1')
        decrypted = ""
        for i, char in enumerate(text):
            key_char = ENCRYPTION_KEY[i % len(ENCRYPTION_KEY)]
            decrypted += chr(ord(char) ^ ord(key_char))
        return decrypted
    except:
        return "[Зашифрованное сообщение]"

# HTML страница с паролем
LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🔒 Личка - Вход</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            text-align: center;
            width: 350px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        input {
            width: 100%;
            padding: 15px;
            margin: 15px 0;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
            box-sizing: border-box;
        }
        input:focus {
            border-color: #667eea;
            outline: none;
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: opacity 0.3s;
        }
        button:hover {
            opacity: 0.9;
        }
        .error {
            color: #f5576c;
            margin-top: 10px;
            display: none;
        }
        .lock-icon {
            font-size: 50px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <div class="lock-icon">🔒</div>
        <h1>Личка</h1>
        <p class="subtitle">Приватный чат для своего круга</p>
        <form method="post" onsubmit="return validateForm()">
            <input type="password" id="password" name="password" 
                   placeholder="Введите пароль" required autofocus>
            <button type="submit">Войти в чат</button>
        </form>
        <div id="error" class="error">Неверный пароль!</div>
        
        <script>
            function validateForm() {
                var password = document.getElementById("password").value;
                if (password === "") {
                    document.getElementById("error").style.display = "block";
                    return false;
                }
                return true;
            }
            
            // Показать ошибку если есть
            if (window.location.search.includes('error')) {
                document.getElementById("error").style.display = "block";
            }
        </script>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    """Главная страница с проверкой пароля"""
    if request.method == 'POST':
        if request.form.get('password') == PASSWORD:
            session['authenticated'] = True
            session['login_time'] = time.time()
            # Редирект на чат
            return '''
            <script>
                window.location.href = '/chat';
            </script>
            '''
        else:
            return LOGIN_HTML.replace('display: none;', 'display: block;')
    
    # Если уже авторизован
    if session.get('authenticated'):
        return '''
        <script>
            window.location.href = '/chat';
        </script>
        '''
    
    return LOGIN_HTML

@app.route('/chat')
def chat():
    """Страница чата (только для авторизованных)"""
    if not session.get('authenticated'):
        return '''
        <script>
            window.location.href = '/';
        </script>
        '''
    
    # ТУТ БУДЕТ ТВОЙ СТАРЫЙ HTML ИЗ кибертермит_финал.py
    # НО ПОМЕНЯЙ "Кибер-Термит" на "Личка"
    return "Чат загружается... Нужно добавить HTML код сюда."

# Остальные функции пока оставим пустыми
@app.route('/send', methods=['POST'])
def send_message():
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authorized'}), 401
    # Будет позже
    return jsonify({'status': 'ok'})

@app.route('/get_messages')
def get_messages():
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authorized'}), 401
    # Будет позже
    return jsonify({'messages': []})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
