from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit
import socket
from datetime import datetime
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'кибер-термит-секрет-ключ'
socketio = SocketIO(app, cors_allowed_origins="*")

# Папка для хранения данных
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# HTML с WebSocket поддержкой
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🤖 Кибер-Термит v2.0 - Синхронизация</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        /* Ваш существующий CSS остаётся */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 24px;
            box-shadow: 0 20px 80px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 1000px;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        .status-bar {
            display: flex;
            justify-content: space-around;
            background: rgba(0,0,0,0.1);
            padding: 15px;
            margin-top: 15px;
            border-radius: 12px;
        }
        .status-item {
            text-align: center;
        }
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .online-dot { background: #4CAF50; }
        .sync-dot { background: #FF9800; }
        .device-dot { background: #2196F3; }
        
        .content {
            padding: 30px;
            display: grid;
            gap: 20px;
            grid-template-columns: 1fr 1fr;
        }
        
        .sync-panel {
            grid-column: span 2;
            background: #f8f9fa;
            border-radius: 16px;
            padding: 25px;
            margin-top: 20px;
        }
        
        .device-list {
            display: flex;
            gap: 15px;
            margin-top: 15px;
        }
        
        .device-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            flex: 1;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .qr-container {
            margin: 20px 0;
            text-align: center;
        }
        
        #qrcode {
            display: inline-block;
            padding: 10px;
            background: white;
            border-radius: 12px;
        }
        
        /* Сообщения синхронизации */
        .sync-message {
            background: #e3f2fd;
            border-left: 4px solid #2196F3;
            padding: 12px;
            margin: 10px 0;
            border-radius: 8px;
            animation: slideIn 0.3s ease;
        }
        
        /* Чат с разделением по устройствам */
        .chat-message {
            margin: 10px;
            padding: 12px;
            border-radius: 12px;
            max-width: 80%;
            position: relative;
        }
        
        .message-from-pc {
            background: #e8f5e9;
            border-left: 4px solid #4CAF50;
            margin-left: auto;
        }
        
        .message-from-phone {
            background: #e3f2fd;
            border-left: 4px solid #2196F3;
            margin-right: auto;
        }
        
        .message-sender {
            font-size: 0.8em;
            color: #666;
            margin-bottom: 5px;
        }
    </style>
    
    <!-- Библиотека для QR кода -->
    <script src="https://cdn.jsdelivr.net/npm/qrcode@1.5.3/build/qrcode.min.js"></script>
    <!-- Socket.IO клиент -->
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Кибер-Термит v2.0</h1>
            <p>Синхронизация между телефоном и компьютером</p>
            
            <div class="status-bar">
                <div class="status-item">
                    <span class="status-dot online-dot"></span>
                    <span id="serverStatus">Сервер: онлайн</span>
                </div>
                <div class="status-item">
                    <span class="status-dot sync-dot"></span>
                    <span id="syncStatus">Синхронизация: ожидание</span>
                </div>
                <div class="status-item">
                    <span class="status-dot device-dot"></span>
                    <span id="deviceCount">Устройств: 1</span>
                </div>
            </div>
        </div>
        
        <div class="content">
            <!-- Левая колонка - компьютер -->
            <div class="device-card">
                <h2>💻 Компьютер (Ubuntu)</h2>
                <div class="device-info">
                    <p><strong>IP:</strong> <span id="pcIp">...</span></p>
                    <p><strong>Статус:</strong> <span id="pcStatus">активен</span></p>
                </div>
                <div class="qr-container">
                    <h3>Для подключения телефона:</h3>
                    <div id="qrcode"></div>
                    <p>Отсканируйте QR-код с телефона</p>
                </div>
            </div>
            
            <!-- Правая колонка - телефон -->
            <div class="device-card">
                <h2>📱 Телефон (Android)</h2>
                <div class="device-info">
                    <p><strong>Статус:</strong> <span id="phoneStatus">не подключен</span></p>
                    <p><strong>Последняя активность:</strong> <span id="phoneLastSeen">никогда</span></p>
                </div>
                <button onclick="connectPhone()" id="connectBtn" style="width:100%; margin-top:15px; padding:15px; background:#4CAF50; color:white; border:none; border-radius:12px; font-size:16px;">
                    📲 Подключить телефон
                </button>
            </div>
            
            <!-- Панель синхронизации -->
            <div class="sync-panel">
                <h2>🔄 Синхронизированный чат</h2>
                <div class="messages" id="syncMessages" style="height:250px; overflow-y:auto; background:white; border-radius:12px; padding:15px; margin:15px 0;">
                    <div class="sync-message">
                        💬 Чат синхронизации запущен. Отправляйте сообщения с любого устройства!
                    </div>
                </div>
                
                <div style="display:flex; gap:10px;">
                    <input type="text" id="syncInput" placeholder="Введите сообщение..." style="flex:1; padding:15px; border:2px solid #ddd; border-radius:25px; font-size:16px;">
                    <button onclick="sendSyncMessage()" style="padding:15px 30px; background:linear-gradient(135deg, #00b09b 0%, #96c93d 100%); color:white; border:none; border-radius:25px; font-size:16px;">
                        Отправить
                    </button>
                </div>
                
                <div style="margin-top:20px; text-align:center;">
                    <button onclick="clearChat()" style="padding:10px 20px; background:#f44336; color:white; border:none; border-radius:25px; margin:0 10px;">
                        Очистить чат
                    </button>
                    <button onclick="testSync()" style="padding:10px 20px; background:#2196F3; color:white; border:none; border-radius:25px; margin:0 10px;">
                        Тест синхронизации
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Подключаемся к WebSocket серверу
        const socket = io();
        let deviceId = 'pc_' + Math.random().toString(36).substr(2, 9);
        let connectedDevices = 1;
        
        // Инициализация
        document.addEventListener('DOMContentLoaded', function() {
            // Определяем тип устройства
            const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
            deviceId = (isMobile ? 'phone_' : 'pc_') + Math.random().toString(36).substr(2, 9);
            
            // Отправляем информацию об устройстве
            socket.emit('device_connect', {
                id: deviceId,
                type: isMobile ? 'phone' : 'pc',
                name: isMobile ? 'Телефон Android' : 'Компьютер Ubuntu',
                userAgent: navigator.userAgent
            });
            
            // Генерируем QR-код для подключения
            if (!isMobile) {
                const url = window.location.href;
                QRCode.toCanvas(document.getElementById('qrcode'), url, {
                    width: 200,
                    height: 200,
                    colorDark: "#000000",
                    colorLight: "#ffffff"
                }, function(error) {
                    if (error) console.error(error);
                });
                document.getElementById('pcIp').textContent = window.location.host;
            }
            
            updateDeviceDisplay(isMobile);
        });
        
        // Обработчики Socket.IO
        socket.on('connect', function() {
            console.log('✅ Подключен к серверу синхронизации');
            document.getElementById('serverStatus').textContent = 'Сервер: онлайн';
        });
        
        socket.on('sync_message', function(data) {
            addSyncMessage(data.message, data.sender, data.deviceType);
        });
        
        socket.on('device_connected', function(data) {
            console.log('📱 Устройство подключено:', data);
            connectedDevices++;
            document.getElementById('deviceCount').textContent = 'Устройств: ' + connectedDevices;
            document.getElementById('syncStatus').textContent = 'Синхронизация: активно';
            
            if (data.type === 'phone') {
                document.getElementById('phoneStatus').textContent = 'подключен';
                document.getElementById('phoneLastSeen').textContent = new Date().toLocaleTimeString();
            }
            
            addSyncMessage(`📱 ${data.name} подключился!`, 'system', 'system');
        });
        
        socket.on('device_disconnected', function(data) {
            connectedDevices--;
            document.getElementById('deviceCount').textContent = 'Устройств: ' + connectedDevices;
            
            if (connectedDevices < 2) {
                document.getElementById('syncStatus').textContent = 'Синхронизация: ожидание';
            }
        });
        
        // Функции интерфейса
        function updateDeviceDisplay(isMobile) {
            if (isMobile) {
                document.getElementById('connectBtn').style.display = 'none';
                document.querySelector('.qr-container').style.display = 'none';
                document.getElementById('phoneStatus').textContent = 'активен';
            }
        }
        
        function addSyncMessage(message, sender, deviceType) {
            const messagesDiv = document.getElementById('syncMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'chat-message ' + 
                (deviceType === 'pc' ? 'message-from-pc' : 
                 deviceType === 'phone' ? 'message-from-phone' : 'sync-message');
            
            messageDiv.innerHTML = `
                <div class="message-sender">
                    ${sender === 'system' ? '🤖 Система' : 
                      deviceType === 'pc' ? '💻 Компьютер' : 
                      deviceType === 'phone' ? '📱 Телефон' : '👤 ' + sender}
                </div>
                <div>${message}</div>
            `;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function sendSyncMessage() {
            const input = document.getElementById('syncInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
            
            // Отправляем сообщение на сервер
            socket.emit('sync_message', {
                message: message,
                sender: deviceId,
                deviceType: isMobile ? 'phone' : 'pc',
                timestamp: new Date().toISOString()
            });
            
            // Показываем локально
            addSyncMessage(message, 'Вы', isMobile ? 'phone' : 'pc');
            
            input.value = '';
        }
        
        function connectPhone() {
            alert('Для подключения телефона:\n1. Убедитесь что телефон в той же WiFi сети\n2. Откройте браузер на телефоне\n3. Введите адрес: ' + window.location.href);
        }
        
        function clearChat() {
            document.getElementById('syncMessages').innerHTML = 
                '<div class="sync-message">💬 Чат очищен</div>';
        }
        
        function testSync() {
            socket.emit('sync_message', {
                message: '🔧 Тестовое сообщение синхронизации',
                sender: 'system',
                deviceType: 'system',
                timestamp: new Date().toISOString()
            });
        }
        
        // Отправка по Enter
        document.getElementById('syncInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendSyncMessage();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'online',
        'version': '2.0',
        'project': 'Кибер-Термит с синхронизацией',
        'connected_devices': len(connected_devices),
        'timestamp': datetime.now().isoformat()
    })

# Храним подключённые устройства
connected_devices = {}

@socketio.on('device_connect')
def handle_device_connect(data):
    device_id = data['id']
    connected_devices[device_id] = {
        'type': data['type'],
        'name': data['name'],
        'connected_at': datetime.now().isoformat(),
        'last_seen': datetime.now().isoformat()
    }
    
    emit('device_connected', {
        'id': device_id,
        'type': data['type'],
        'name': data['name']
    }, broadcast=True)
    
    print(f"📱 Устройство подключено: {data['name']} ({data['type']})")

@socketio.on('sync_message')
def handle_sync_message(data):
    print(f"💬 Сообщение от {data['sender']}: {data['message']}")
    
    # Сохраняем сообщение в файл
    save_message(data)
    
    # Отправляем всем подключённым устройствам
    emit('sync_message', {
        'message': data['message'],
        'sender': data['sender'],
        'deviceType': data['deviceType'],
        'timestamp': data['timestamp']
    }, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    # Находим отключившееся устройство
    for device_id, device_info in list(connected_devices.items()):
        # Простая логика - если долго не было сообщений
        # В реальном приложении нужно отслеживать сессии
        pass

def save_message(data):
    """Сохраняем сообщение в JSON файл"""
    message_file = os.path.join(DATA_DIR, 'messages.json')
    
    messages = []
    if os.path.exists(message_file):
        with open(message_file, 'r', encoding='utf-8') as f:
            try:
                messages = json.load(f)
            except:
                messages = []
    
    messages.append({
        **data,
        'server_received': datetime.now().isoformat()
    })
    
    # Сохраняем только последние 100 сообщений
    if len(messages) > 100:
        messages = messages[-100:]
    
    with open(message_file, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    print("🤖 Запуск Кибер-Термита v2.0 с синхронизацией...")
    print("🌐 Сервер будет доступен по:")
    print("   • http://localhost:8081")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        print(f"   • http://{ip}:8081 (для телефона)")
        print(f"   • QR-код для подключения телефона будет на странице")
    except:
        print("   • Не удалось определить внешний IP")
    
    print("\n⚡ Для остановки: Ctrl+C")
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=8081, debug=True, allow_unsafe_werkzeug=True)
