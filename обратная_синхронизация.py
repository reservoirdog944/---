from flask import Flask, render_template_string
from flask_socketio import SocketIO
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Храним последние сообщения для телефона
phone_messages = []
phone_lock = threading.Lock()

HTML_COMPUTER = '''
<!DOCTYPE html>
<html>
<body style="padding:20px;">
    <h2>💻 КОМПЬЮТЕР (ОТПРАВЛЯЕТ)</h2>
    <div id="status">Статус телефона: <span id="phoneStatus">❓ Не подключен</span></div>
    <input id="msg" placeholder="Сообщение для телефона">
    <button onclick="sendToPhone()">📤 → Телефону</button>
    <div id="log" style="margin-top:20px; border:1px solid #ccc; padding:10px; height:200px; overflow:auto;"></div>
    
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const socket = io();
        
        function log(text) {
            const div = document.getElementById('log');
            div.innerHTML += '<div>' + new Date().toLocaleTimeString() + ': ' + text + '</div>';
            div.scrollTop = 9999;
        }
        
        socket.on('connect', () => {
            log('✅ Подключен к серверу');
        });
        
        socket.on('phone_status', (status) => {
            document.getElementById('phoneStatus').textContent = status;
            document.getElementById('phoneStatus').style.color = status === 'online' ? 'green' : 'red';
        });
        
        socket.on('message_to_phone_ack', (data) => {
            log('📨 Сервер подтвердил отправку телефону: ' + data.text);
        });
        
        function sendToPhone() {
            const text = document.getElementById('msg').value || 'Тест с компьютера';
            socket.emit('message_to_phone', {text: text});
            log('📤 Отправляю телефону: ' + text);
            document.getElementById('msg').value = '';
        }
        
        log('Компьютер готов к отправке');
    </script>
</body>
</html>
'''

HTML_PHONE = '''
<!DOCTYPE html>
<html>
<body style="padding:20px;">
    <h2>📱 ТЕЛЕФОН (ПОЛУЧАЕТ)</h2>
    <div id="status">Статус: <span style="color:green;">✅ Онлайн</span></div>
    <button onclick="checkMessages()">🔄 Проверить сообщения</button>
    <div id="messages" style="margin-top:20px; border:1px solid #ccc; padding:10px; height:300px; overflow:auto;">
        <div>Ожидаю сообщения с компьютера...</div>
    </div>
    
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const socket = io();
        let lastCheck = 0;
        
        function addMessage(text) {
            const div = document.getElementById('messages');
            div.innerHTML += '<div style="background:#e8f5e9; padding:10px; margin:5px; border-radius:5px;">' + 
                '💻 Компьютер: ' + text + 
                '<div style="font-size:12px; color:#666;">' + new Date().toLocaleTimeString() + '</div>' +
                '</div>';
            div.scrollTop = 9999;
        }
        
        socket.on('connect', () => {
            console.log('📱 Телефон подключен к серверу');
            // Регистрируемся как телефон
            socket.emit('register_as_phone');
        });
        
        // Получаем сообщения ПРЯМО от сервера
        socket.on('message_from_computer', (data) => {
            console.log('📩 Получено сообщение с компьютера:', data);
            addMessage(data.text);
        });
        
        function checkMessages() {
            socket.emit('get_messages', {since: lastCheck});
        }
        
        // Автопроверка каждые 3 секунды
        setInterval(checkMessages, 3000);
        
        // Симулируем подключение телефона
        socket.emit('phone_online');
    </script>
</body>
</html>
'''

@app.route('/')
def computer():
    return render_template_string(HTML_COMPUTER)

@app.route('/phone')
def phone():
    return render_template_string(HTML_PHONE)

# Храним состояние телефона
phone_online = False
phone_sid = None

@socketio.on('connect')
def handle_connect():
    print(f"📡 Подключение: {request.sid}")

@socketio.on('register_as_phone')
def handle_phone_register():
    global phone_online, phone_sid
    phone_online = True
    phone_sid = request.sid
    print(f"📱 Телефон зарегистрирован: {request.sid}")
    
    # Оповещаем компьютер
    socketio.emit('phone_status', 'online')

@socketio.on('phone_online')
def handle_phone_online():
    global phone_online
    phone_online = True
    print("📱 Телефон в сети")

@socketio.on('message_to_phone')
def handle_message_to_phone(data):
    print(f"💬 Сообщение для телефона: {data['text']}")
    
    # Сохраняем для телефона
    with phone_lock:
        phone_messages.append({
            'text': data['text'],
            'time': time.time()
        })
    
    # Подтверждаем компьютеру
    socketio.emit('message_to_phone_ack', data)
    
    # НЕМЕДЛЕННО отправляем телефону, если он онлайн
    if phone_online and phone_sid:
        print(f"🚀 Отправляю телефону {phone_sid}: {data['text']}")
        socketio.emit('message_from_computer', data, room=phone_sid)

@socketio.on('get_messages')
def handle_get_messages(data):
    since = data.get('since', 0)
    with phone_lock:
        new_messages = [m for m in phone_messages if m['time'] > since]
    
    if new_messages:
        for msg in new_messages:
            socketio.emit('message_from_computer', {'text': msg['text']})

if __name__ == '__main__':
    print("="*60)
    print("📱 ОБРАТНАЯ СИНХРОНИЗАЦИЯ (телефон получает)")
    print("="*60)
    print("💻 КОМПЬЮТЕР (отправляет): http://localhost:9111")
    print("📱 ТЕЛЕФОН (получает):    http://192.168.0.144:9111/phone")
    print("="*60)
    print("ИНСТРУКЦИЯ:")
    print("1. На телефоне откройте /phone")
    print("2. На компьютере откройте /")
    print("3. С компьютера отправьте сообщение")
    print("4. На телефоне должно появиться сообщение")
    print("="*60)
    
    socketio.run(app, host='0.0.0.0', port=9111, debug=True)
