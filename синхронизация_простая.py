from flask import Flask, render_template_string, jsonify
from flask_socketio import SocketIO, emit
import socket
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'кибертермит2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Храним подключенные устройства
connected_devices = {}

# Простой HTML интерфейс
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🤖 Кибер-Термит - Синхронизация</title>
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
        .container {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .status {
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            background: #f5f5f5;
        }
        .online { border-left: 5px solid #4CAF50; }
        .offline { border-left: 5px solid #f44336; }
        .messages {
            height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 15px;
            margin: 15px 0;
            border-radius: 10px;
        }
        .message {
            margin: 10px 0;
            padding: 10px;
            border-radius: 10px;
            max-width: 80%;
        }
        .from-pc { background: #e3f2fd; margin-left: auto; }
        .from-phone { background: #e8f5e9; }
        .input-area {
            display: flex;
            gap: 10px;
        }
        input {
            flex: 1;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
        }
        button {
            padding: 12px 25px;
            background: #FF5722;
            color: white;
            border: none;
            border-radius: 25px;
            font-weight: bold;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Кибер-Термит - Синхронизация</h1>
        
        <div class="status" id="connectionStatus">
            <h3>🔌 Статус подключения</h3>
            <p>Сервер: <span id="serverStatus">подключение...</span></p>
            <p>Устройств: <span id="devicesCount">1</span></p>
            <p>Ваше устройство: <span id="deviceType">определение...</span></p>
            <p>IP для телефона: <span id="serverIP">192.168.0.144:8081</span></p>
        </div>
        
        <div>
            <h3>💬 Общий чат (синхронизированный)</h3>
            <div class="messages" id="chatMessages">
                <div class="message" style="background:#fff3e0;">
                    Чат синхронизации запущен. Сообщения будут видны на всех устройствах!
                </div>
            </div>
            
            <div class="input-area">
                <input type="text" id="messageInput" placeholder="Введите сообщение..." autocomplete="off">
                <button onclick="sendMessage()">Отправить</button>
            </div>
            
            <div style="margin-top: 20px; text-align: center;">
                <button onclick="testConnection()" style="background:#2196F3;">Тест соединения</button>
                <button onclick="clearChat()" style="background:#f44336;">Очистить чат</button>
            </div>
        </div>
    </div>

    <!-- Socket.IO клиент -->
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    
    <script>
        // Определяем тип устройства
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        const deviceType = isMobile ? 'phone' : 'pc';
        const deviceName = isMobile ? 'Телефон Android' : 'Компьютер Ubuntu';
        
        // Подключаемся к серверу
        const socket = io();
        
        // Обновляем интерфейс
        document.getElementById('deviceType').textContent = deviceName;
        
        // События Socket.IO
        socket.on('connect', function() {
            console.log('✅ Подключились к серверу WebSocket');
            document.getElementById('serverStatus').textContent = 'онлайн';
            document.getElementById('connectionStatus').className = 'status online';
            
            // Регистрируем устройство
            socket.emit('register_device', {
                type: deviceType,
                name: deviceName
            });
        });
        
        socket.on('disconnect', function() {
            console.log('❌ Отключились от сервера');
            document.getElementById('serverStatus').textContent = 'оффлайн';
            document.getElementById('connectionStatus').className = 'status offline';
        });
        
        socket.on('device_connected', function(data) {
            console.log('📱 Новое устройство:', data);
            const count = parseInt(document.getElementById('devicesCount').textContent) + 1;
            document.getElementById('devicesCount').textContent = count;
            
            addMessage(`📱 ${data.name} подключился!`, 'system');
        });
        
        socket.on('chat_message', function(data) {
            console.log('💬 Новое сообщение:', data);
            addMessage(data.message, data.deviceType);
        });
        
        socket.on('devices_count', function(count) {
            document.getElementById('devicesCount').textContent = count;
        });
        
        // Функции интерфейса
        function addMessage(text, senderType) {
            const messagesDiv = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            
            messageDiv.className = 'message ' + 
                (senderType === 'pc' ? 'from-pc' : 
                 senderType === 'phone' ? 'from-phone' : '');
            
            messageDiv.innerHTML = `
                <strong>${senderType === 'pc' ? '💻 Компьютер' : 
                          senderType === 'phone' ? '📱 Телефон' : '🤖 Система'}:</strong>
                <br>${text}
                <div style="font-size:12px; color:#666; margin-top:5px;">
                    ${new Date().toLocaleTimeString()}
                </div>
            `;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const text = input.value.trim();
            
            if (!text) return;
            
            // Отправляем на сервер
            socket.emit('chat_message', {
                message: text,
                deviceType: deviceType
            });
            
            // Показываем локально
            addMessage(text, deviceType);
            
            input.value = '';
            input.focus();
        }
        
        function testConnection() {
            socket.emit('chat_message', {
                message: '🔧 Тестовое сообщение синхронизации',
                deviceType: 'system'
            });
        }
        
        function clearChat() {
            document.getElementById('chatMessages').innerHTML = 
                '<div class="message" style="background:#fff3e0;">Чат очищен</div>';
        }
        
        // Отправка по Enter
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
        
        // Автофокус
        document.getElementById('messageInput').focus();
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/status')
def get_status():
    return jsonify({
        'status': 'online',
        'devices_count': len(connected_devices),
        'devices': list(connected_devices.values())
    })

@socketio.on('connect')
def handle_connect():
    print(f"📡 Новое подключение: {request.sid}")

@socketio.on('register_device')
def handle_register_device(data):
    device_id = request.sid
    connected_devices[device_id] = {
        'id': device_id,
        'type': data['type'],
        'name': data['name'],
        'connected_at': time.time()
    }
    
    print(f"✅ Устройство зарегистрировано: {data['name']} ({data['type']})")
    
    # Отправляем всем обновлённое количество устройств
    emit('devices_count', len(connected_devices), broadcast=True)
    
    # Оповещаем всех о новом устройстве
    emit('device_connected', {
        'name': data['name'],
        'type': data['type']
    }, broadcast=True, include_self=False)

@socketio.on('chat_message')
def handle_chat_message(data):
    print(f"💬 Сообщение от {data.get('deviceType', 'unknown')}: {data['message']}")
    
    # Пересылаем всем подключенным клиентам
    emit('chat_message', {
        'message': data['message'],
        'deviceType': data.get('deviceType', 'unknown'),
        'timestamp': time.time()
    }, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    device_id = request.sid
    if device_id in connected_devices:
        device_info = connected_devices.pop(device_id)
        print(f"❌ Устройство отключилось: {device_info['name']}")
        
        # Обновляем счетчик устройств
        emit('devices_count', len(connected_devices), broadcast=True)

def get_server_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return 'localhost'

if __name__ == '__main__':
    server_ip = get_server_ip()
    port = 8081
    
    print("=" * 50)
    print("🤖 КИБЕР-ТЕРМИТ - РЕАЛЬНАЯ СИНХРОНИЗАЦИЯ")
    print("=" * 50)
    print(f"🌐 Сервер запущен на:")
    print(f"   • http://localhost:{port}")
    print(f"   • http://{server_ip}:{port} (для телефона)")
    print("\n📱 Инструкция для подключения телефона:")
    print(f"   1. Убедитесь, что телефон в той же WiFi сети")
    print(f"   2. На телефоне откройте браузер")
    print(f"   3. Введите адрес: http://{server_ip}:{port}")
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
