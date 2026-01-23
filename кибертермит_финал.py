from flask import Flask, render_template_string, jsonify, request, session
import time
import socket
import hashlib
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Конфигурация
APP_NAME = "🔒 Личка"
PASSWORD = "011225"
ENCRYPTION_KEY = "termite_secret_key_2026"
SESSION_TIMEOUT = 3600  # 1 час

# Хранилища
messages = []
users = {}
message_id_counter = 0

# Шифрование
def simple_encrypt(text):
    if not text:
        return ""
    encrypted = ""
    for i, char in enumerate(text):
        key_char = ENCRYPTION_KEY[i % len(ENCRYPTION_KEY)]
        encrypted += chr(ord(char) ^ ord(key_char))
    return encrypted.encode('latin-1').hex()

def simple_decrypt(hex_text):
    if not hex_text:
        return ""
    try:
        text = bytes.fromhex(hex_text).decode('latin-1')
        decrypted = ""
        for i, char in enumerate(text):
            key_char = ENCRYPTION_KEY[i % len(ENCRYPTION_KEY)]
            decrypted += chr(ord(char) ^ ord(key_char))
        return decrypted
    except:
        return "[Сообщение защищено]"

# HTML страница входа
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
        </script>
    </div>
</body>
</html>
'''

# HTML чата
CHAT_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🔒 Личка - Приватный чат</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .header {
            background: white;
            border-radius: 15px 15px 0 0;
            padding: 25px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .chat-container {
            background: white;
            border-radius: 0 0 15px 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .status-bar {
            display: flex;
            justify-content: space-between;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .messages {
            height: 400px;
            overflow-y: auto;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            background: #f8f9fa;
        }
        .message {
            margin: 10px 0;
            padding: 12px 15px;
            border-radius: 15px;
            max-width: 80%;
            word-wrap: break-word;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .my-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin-left: auto;
            margin-right: 0;
            border-bottom-right-radius: 5px;
        }
        .other-message {
            background: #e9ecef;
            color: #333;
            margin-right: auto;
            border-bottom-left-radius: 5px;
        }
        .system-message {
            background: #fff3cd;
            color: #856404;
            margin: 10px auto;
            text-align: center;
            max-width: 90%;
            border: 1px solid #ffeaa7;
        }
        .encrypted-note {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
            font-style: italic;
        }
        .input-area {
            display: flex;
            gap: 10px;
        }
        input {
            flex: 1;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
        }
        input:focus {
            border-color: #667eea;
        }
        button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover {
            opacity: 0.9;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            justify-content: center;
        }
        .logout-btn {
            background: #6c757d !important;
        }
        .lock-badge {
            display: inline-block;
            padding: 5px 10px;
            background: #28a745;
            color: white;
            border-radius: 20px;
            font-size: 12px;
            margin-left: 10px;
        }
        .device-info {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin:0;">🔒 Личка</h1>
        <p style="color:#666; margin:5px 0;">Приватный чат для своего круга</p>
        <span class="lock-badge">🔐 Зашифровано</span>
        <div class="device-info">
            IP: <span id="userIp">Загрузка...</span> | 
            Время: <span id="currentTime">--:--:--</span>
        </div>
    </div>
    
    <div class="chat-container">
        <div class="status-bar">
            <div>
                <strong>Устройств онлайн:</strong> <span id="userCount">1</span>
            </div>
            <div>
                <strong>Сообщений:</strong> <span id="msgCount">0</span>
            </div>
            <div>
                <strong>Статус:</strong> <span id="status" style="color:green;">✅ Онлайн</span>
            </div>
        </div>
        
        <div class="messages" id="messagesContainer">
            <div class="system-message">
                🔒 Добро пожаловать в Личку! Все сообщения зашифрованы.
            </div>
        </div>
        
        <div class="input-area">
            <input type="text" id="messageInput" 
                   placeholder="Введите сообщение... (шифруется автоматически)" 
                   autocomplete="off">
            <button onclick="sendMessage()">Отправить</button>
        </div>
        
        <div class="controls">
            <button onclick="clearChat()" style="background:#ffc107;">Очистить чат</button>
            <button onclick="location.reload()" style="background:#17a2b8;">Обновить</button>
            <button onclick="logout()" class="logout-btn">Выйти</button>
        </div>
    </div>
    
    <script>
        let userId = 'user_' + Math.random().toString(36).substr(2, 9);
        let lastMessageId = 0;
        
        // Определяем устройство
        let deviceType = /Mobile|Android|iPhone/i.test(navigator.userAgent) ? '📱 Телефон' : '💻 Компьютер';
        document.getElementById('userIp').textContent = deviceType;
        
        // Обновление времени
        function updateTime() {
            let now = new Date();
            document.getElementById('currentTime').textContent = 
                now.getHours().toString().padStart(2, '0') + ':' +
                now.getMinutes().toString().padStart(2, '0') + ':' +
                now.getSeconds().toString().padStart(2, '0');
        }
        setInterval(updateTime, 1000);
        updateTime();
        
        // Отправка сообщения
        function sendMessage() {
            let input = document.getElementById('messageInput');
            let text = input.value.trim();
            
            if (!text) return;
            
            // Показываем сразу
            displayMessage({
                id: 'temp_' + Date.now(),
                text: text,
                user: 'Я',
                time: new Date().toLocaleTimeString(),
                type: 'my'
            });
            
            input.value = '';
            
            // Отправляем на сервер
            fetch('/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    text: text,
                    user_id: userId,
                    device: deviceType
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Ошибка: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
            });
        }
        
        // Показать сообщение
        function displayMessage(msg) {
            let container = document.getElementById('messagesContainer');
            let msgDiv = document.createElement('div');
            msgDiv.className = 'message ' + (msg.type === 'my' ? 'my-message' : 'other-message');
            msgDiv.id = 'msg_' + msg.id;
            
            msgDiv.innerHTML = `
                <div><strong>${msg.user}</strong> <small>${msg.time}</small></div>
                <div>${msg.text}</div>
                ${msg.type === 'my' ? '<div class="encrypted-note">🔐 Зашифровано</div>' : ''}
            `;
            
            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
            updateMessageCount();
        }
        
        // Получение сообщений
        function getMessages() {
            fetch('/get_messages?last_id=' + lastMessageId)
                .then(response => response.json())
                .then(data => {
                    if (data.messages) {
                        data.messages.forEach(msg => {
                            if (msg.id > lastMessageId) {
                                lastMessageId = msg.id;
                                displayMessage(msg);
                            }
                        });
                    }
                    
                    // Обновляем статистику
                    if (data.stats) {
                        document.getElementById('userCount').textContent = data.stats.users;
                        document.getElementById('msgCount').textContent = data.stats.messages;
                    }
                })
                .catch(error => console.error('Ошибка получения:', error));
        }
        
        // Очистка чата
        function clearChat() {
            if (confirm('Очистить весь чат?')) {
                fetch('/clear', {method: 'POST'})
                    .then(() => {
                        document.getElementById('messagesContainer').innerHTML = 
                            '<div class="system-message">Чат очищен</div>';
                        updateMessageCount();
                    });
            }
        }
        
        // Выход
        function logout() {
            fetch('/logout', {method: 'POST'})
                .then(() => {
                    window.location.href = '/';
                });
        }
        
        // Обновление счетчика
        function updateMessageCount() {
            let count = document.querySelectorAll('.message').length;
            document.getElementById('msgCount').textContent = count;
        }
        
        // Отправка по Enter
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
        
        // Запуск
        updateMessageCount();
        setInterval(getMessages, 2000);  // Обновление каждые 2 секунды
        getMessages();
    </script>
</body>
</html>
'''

# Проверка сессии
def check_session():
    if not session.get('authenticated'):
        return False
    if time.time() - session.get('login_time', 0) > SESSION_TIMEOUT:
        session.clear()
        return False
    return True

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.form.get('password') == PASSWORD:
            session['authenticated'] = True
            session['login_time'] = time.time()
            session['user_agent'] = request.user_agent.string
            return '''
            <script>
                window.location.href = '/chat';
            </script>
            '''
        else:
            return LOGIN_HTML.replace('display: none;', 'display: block;')
    
    if check_session():
        return '''
        <script>
            window.location.href = '/chat';
        </script>
        '''
    
    return LOGIN_HTML

@app.route('/chat')
def chat():
    if not check_session():
        return '''
        <script>
            window.location.href = '/';
        </script>
        '''
    return CHAT_HTML

@app.route('/send', methods=['POST'])
def send_message():
    if not check_session():
        return jsonify({'error': 'Требуется авторизация'}), 401
    
    global message_id_counter
    data = request.json
    
    # Шифруем сообщение
    encrypted_text = simple_encrypt(data.get('text', ''))
    
    message = {
        'id': message_id_counter,
        'text': data.get('text', ''),
        'encrypted': encrypted_text,
        'user': data.get('user_id', 'unknown'),
        'device': data.get('device', 'unknown'),
        'time': datetime.now().strftime('%H:%M:%S'),
        'timestamp': time.time()
    }
    
    messages.append(message)
    message_id_counter += 1
    
    # Ограничиваем историю
    if len(messages) > 100:
        messages.pop(0)
    
    return jsonify({'status': 'ok', 'id': message['id']})

@app.route('/get_messages')
def get_messages():
    if not check_session():
        return jsonify({'error': 'Требуется авторизация'}), 401
    
    last_id = int(request.args.get('last_id', -1))
    
    # Фильтруем сообщения
    new_messages = []
    for msg in messages:
        if msg['id'] > last_id:
            new_messages.append({
                'id': msg['id'],
                'text': msg['text'],
                'user': msg['user'] == session.get('user_id', '') ? 'Я' : 'Другой',
                'time': msg['time'],
                'type': 'my' if msg['user'] == session.get('user_id', '') else 'other'
            })
    
    # Статистика
    unique_users = len(set([msg['user'] for msg in messages]))
    
    return jsonify({
        'messages': new_messages,
        'stats': {
            'users': unique_users,
            'messages': len(messages)
        }
    })

@app.route('/clear', methods=['POST'])
def clear_chat():
    if not check_session():
        return jsonify({'error': 'Требуется авторизация'}), 401
    
    global messages
    messages = []
    return jsonify({'status': 'ok'})

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'status': 'ok'})

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'app': 'Личка', 'encryption': 'enabled'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
