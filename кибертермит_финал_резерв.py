from flask import Flask, render_template_string, jsonify, request
import time
import socket

app = Flask(__name__)

# Храним сообщения
messages = []
users = {}

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🤖 Кибер-Термит - РАБОЧАЯ версия</title>
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
        .device-badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            margin-left: 10px;
        }
        .phone-badge { background: #2196F3; color: white; }
        .pc-badge { background: #4CAF50; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin:0;">🤖 Кибер-Термит</h1>
        <p style="color:#666; margin:5px 0;">РАБОЧАЯ версия с синхронизацией</p>
        <div class="device-badge" id="deviceBadge">💻 Компьютер</div>
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
        
        <div class="messages" id="messages">
            <div class="system-message">
                🤖 Кибер-Термит запущен! Синхронизация активна!
            </div>
        </div>
        
        <div class="input-area">
            <input type="text" id="inputField" placeholder="Введите сообщение..." autocomplete="off">
            <button onclick="sendMessage()">📤 Отправить</button>
        </div>
        
        <div class="controls">
            <button onclick="clearChat()" style="background:#f44336;">🗑️ Очистить</button>
            <button onclick="testSync()" style="background:#2196F3;">🔗 Тест синхронизации</button>
            <button onclick="sendHello()" style="background:#4CAF50;">👋 Приветствие</button>
        </div>
    </div>

    <script>
        // Идентификатор пользователя
        let myId = 'user_' + Math.random().toString(36).substr(2, 9);
        let lastMessageId = 0;
        let isPolling = false;
        
        // Определяем устройство
        const isMobile = /Android|iPhone|iPad/i.test(navigator.userAgent);
        const deviceType = isMobile ? 'phone' : 'computer';
        const deviceName = isMobile ? '📱 Телефон' : '💻 Компьютер';
        
        // Обновляем интерфейс
        document.getElementById('deviceBadge').textContent = deviceName;
        document.getElementById('deviceBadge').className = 'device-badge ' + (isMobile ? 'phone-badge' : 'pc-badge');
        if (isMobile) {
            document.title = '📱 ' + document.title;
        } else {
            document.title = '💻 ' + document.title;
        }
        
        function addMessage(text, senderType, senderName = '') {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            
            let className = 'message ';
            let displayName = '';
            
            switch(senderType) {
                case 'me':
                    className += 'my-message';
                    displayName = '👤 Вы';
                    break;
                case 'other':
                    className += 'other-message';
                    displayName = senderName || '📱 Другой';
                    break;
                case 'system':
                    className += 'system-message';
                    displayName = '🤖 Система';
                    break;
            }
            
            messageDiv.className = className;
            messageDiv.innerHTML = `
                <strong>${displayName}:</strong><br>
                ${text}
                <div style="font-size:12px; opacity:0.7; margin-top:5px;">
                    ${new Date().toLocaleTimeString()}
                </div>
            `;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            // Обновляем счетчик
            if (senderType !== 'system') {
                document.getElementById('msgCount').textContent = 
                    parseInt(document.getElementById('msgCount').textContent) + 1;
            }
        }
        
        function sendMessage() {
            const input = document.getElementById('inputField');
            const text = input.value.trim();
            
            if (!text) {
                addMessage('Введите сообщение!', 'system');
                return;
            }
            
            // Отправляем на сервер
            fetch('/send', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    text: text,
                    id: myId,
                    device: deviceType,
                    name: deviceName
                })
            }).then(r => r.json()).then(data => {
                if (data.success) {
                    addMessage(text, 'me');
                    input.value = '';
                    input.focus();
                }
            });
        }
        
        function pollMessages() {
            if (isPolling) return;
            isPolling = true;
            
            fetch('/poll?since=' + lastMessageId + '&id=' + myId)
                .then(r => r.json())
                .then(data => {
                    isPolling = false;
                    
                    // Обновляем счетчик пользователей
                    if (data.user_count !== undefined) {
                        document.getElementById('userCount').textContent = data.user_count;
                    }
                    
                    // Обрабатываем новые сообщения
                    if (data.messages && data.messages.length > 0) {
                        data.messages.forEach(msg => {
                            if (msg.id !== myId) {
                                addMessage(
                                    msg.text, 
                                    'other', 
                                    msg.device === 'phone' ? '📱 Телефон' : '💻 Компьютер'
                                );
                                lastMessageId = Math.max(lastMessageId, msg.mid);
                            }
                        });
                    }
                    
                    // Следующий опрос через 500ms
                    setTimeout(pollMessages, 500);
                })
                .catch(error => {
                    isPolling = false;
                    document.getElementById('status').textContent = '❌ Ошибка соединения';
                    document.getElementById('status').style.color = 'red';
                    
                    // Повтор через 2 секунды
                    setTimeout(pollMessages, 2000);
                });
        }
        
        function clearChat() {
            if (confirm('Очистить чат на всех устройствах?')) {
                fetch('/clear').then(() => {
                    document.getElementById('messages').innerHTML = 
                        '<div class="system-message">🗑️ Чат очищен</div>';
                    document.getElementById('msgCount').textContent = '0';
                });
            }
        }
        
        function testSync() {
            const testText = `🔗 Тест синхронизации от ${deviceName} в ${new Date().toLocaleTimeString()}`;
            document.getElementById('inputField').value = testText;
            sendMessage();
        }
        
        function sendHello() {
            document.getElementById('inputField').value = `👋 Привет от ${deviceName}! Кибер-Термит работает!`;
            sendMessage();
        }
        
        // Инициализация
        document.addEventListener('DOMContentLoaded', function() {
            // Регистрируем пользователя
            fetch('/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    id: myId,
                    device: deviceType,
                    name: deviceName
                })
            });
            
            // Отправка по Enter
            document.getElementById('inputField').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });
            
            // Автофокус
            document.getElementById('inputField').focus();
            
            // Запускаем опрос сообщений
            pollMessages();
            
            // Приветственное сообщение
            addMessage(`Добро пожаловать! Вы подключены как ${deviceName}.`, 'system');
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/register', methods=['POST'])
def register_user():
    data = request.json
    users[data['id']] = {
        'device': data['device'],
        'name': data['name'],
        'last_seen': time.time()
    }
    
    # Удаляем неактивных пользователей (больше 30 секунд)
    current_time = time.time()
    inactive_users = []
    for user_id, user_info in users.items():
        if current_time - user_info['last_seen'] > 30:
            inactive_users.append(user_id)
    
    for user_id in inactive_users:
        users.pop(user_id, None)
    
    print(f"📱 Новый пользователь: {data['name']} ({data['device']})")
    print(f"👥 Всего пользователей: {len(users)}")
    
    return jsonify({
        'success': True,
        'user_count': len(users)
    })

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    
    # Обновляем время активности пользователя
    if data['id'] in users:
        users[data['id']]['last_seen'] = time.time()
    
    # Сохраняем сообщение
    messages.append({
        'mid': len(messages) + 1,
        'text': data['text'],
        'id': data['id'],
        'device': data['device'],
        'name': data.get('name', ''),
        'time': time.time()
    })
    
    # Ограничиваем историю
    if len(messages) > 100:
        messages.pop(0)
    
    print(f"💬 Сообщение от {data['name']} ({data['device']}): {data['text']}")
    
    return jsonify({
        'success': True,
        'mid': len(messages),
        'user_count': len(users)
    })

@app.route('/poll')
def poll_messages():
    since = int(request.args.get('since', 0))
    client_id = request.args.get('id', '')
    
    # Обновляем время активности
    if client_id in users:
        users[client_id]['last_seen'] = time.time()
    
    # Ищем новые сообщения
    new_messages = []
    for msg in messages:
        if msg['mid'] > since and msg['id'] != client_id:
            new_messages.append({
                'mid': msg['mid'],
                'text': msg['text'],
                'id': msg['id'],
                'device': msg['device'],
                'name': msg['name']
            })
    
    # Удаляем неактивных пользователей
    current_time = time.time()
    inactive_users = []
    for user_id, user_info in users.items():
        if current_time - user_info['last_seen'] > 30:
            inactive_users.append(user_id)
    
    for user_id in inactive_users:
        users.pop(user_id, None)
    
    return jsonify({
        'messages': new_messages,
        'user_count': len(users),
        'total_messages': len(messages)
    })

@app.route('/clear')
def clear_chat():
    global messages
    messages = []
    print("🗑️ Чат очищен")
    return jsonify({'success': True})

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.0', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return 'localhost'

if __name__ == '__main__':
    ip = get_ip()
    
    print("="*60)
    print("🤖 КИБЕР-ТЕРМИТ - РАБОЧАЯ ВЕРСИЯ")
    print("="*60)
    print("✅ СИНХРОНИЗАЦИЯ РАБОТАЕТ!")
    print("="*60)
    print("🌐 Адреса:")
    print(f"💻 Компьютер: http://localhost:8080")
    print(f"📱 Телефон:   http://{ip}:8080")
    print("="*60)
    print("🎯 Функционал:")
    print("• 💬 Синхронизированный чат между устройствами")
    print("• 📱 Автоопределение устройств (телефон/компьютер)")
    print("• 👥 Отображение количества онлайн-пользователей")
    print("• 🔗 Тестирование синхронизации")
    print("• 🗑️ Очистка чата")
    print("="*60)
    print("🚀 Проект 'Руки (ты) + Мозг (DeepSeek) = Кибер-Термит!'")
    print("="*60)
    
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
