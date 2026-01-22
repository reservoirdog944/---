from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
import socket

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

HTML = '''
<!DOCTYPE html>
<html>
<body>
    <h1>🔄 ТЕСТ СИНХРОНИЗАЦИИ (ИСПРАВЛЕННЫЙ)</h1>
    <p>Статус: <span id="status">Загрузка...</span></p>
    <button onclick="send()">Отправить тест</button>
    <div id="messages"></div>
    
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const socket = io();
        
        socket.on('connect', () => {
            document.getElementById('status').textContent = '✅ Подключён!';
            document.getElementById('status').style.color = 'green';
            console.log('WebSocket подключён!');
        });
        
        socket.on('disconnect', () => {
            document.getElementById('status').textContent = '❌ Отключён';
            document.getElementById('status').style.color = 'red';
        });
        
        socket.on('test_message', (data) => {
            console.log('Получено сообщение:', data);
            document.getElementById('messages').innerHTML += 
                '<p style="background:#e8f5e9; padding:10px; margin:5px;">' + data + '</p>';
        });
        
        function send() {
            const msg = 'Тест от ' + new Date().toLocaleTimeString();
            console.log('Отправляю:', msg);
            socket.emit('test', msg);
            
            // Показываем локально
            document.getElementById('messages').innerHTML += 
                '<p style="background:#e3f2fd; padding:10px; margin:5px;">Вы: ' + msg + '</p>';
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
    
    # Исправленный вызов emit - без параметра broadcast
    # Вместо этого используем room='*' или to=None для broadcast
    emit('test_message', f"🔁 Переслано: {data}", broadcast=True)
    # ИЛИ так (старый стиль): socketio.emit('test_message', f"🔁 Переслано: {data}", namespace='/')

if __name__ == '__main__':
    print("🚀 Запускаем ИСПРАВЛЕННЫЙ тест синхронизации...")
    print("📱 Откройте на двух устройствах: http://localhost:9090")
    socketio.run(app, host='0.0.0.0', port=9090, debug=True, allow_unsafe_werkzeug=True)
