from flask import Flask, render_template_string
from flask_socketio import SocketIO
import socket

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

HTML = '''
<!DOCTYPE html>
<html>
<body>
    <h1>🔄 ТЕСТ СИНХРОНИЗАЦИИ</h1>
    <p>Статус: <span id="status">Загрузка...</span></p>
    <button onclick="send()">Отправить тест</button>
    <div id="messages"></div>
    
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const socket = io();
        
        socket.on('connect', () => {
            document.getElementById('status').textContent = '✅ Подключён!';
            document.getElementById('status').style.color = 'green';
        });
        
        socket.on('disconnect', () => {
            document.getElementById('status').textContent = '❌ Отключён';
            document.getElementById('status').style.color = 'red';
        });
        
        socket.on('test', (data) => {
            document.getElementById('messages').innerHTML += 
                '<p>' + data + '</p>';
        });
        
        function send() {
            socket.emit('test', 'Тест от ' + new Date().toLocaleTimeString());
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@socketio.on('test')
def handle_test(data):
    print(f"📨 Получено: {data}")
    socketio.emit('test', f"🔁 Переслано: {data}", broadcast=True)

if __name__ == '__main__':
    print("🚀 Запускаем ПРОСТОЙ тест синхронизации...")
    print("📱 Откройте на двух устройствах: http://localhost:9090")
    socketio.run(app, host='0.0.0.0', port=9090, debug=True)
