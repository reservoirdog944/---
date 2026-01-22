from flask import Flask, render_template_string, jsonify
import socket
from datetime import datetime

app = Flask(__name__)

# Минимальный HTML с красивым дизайном
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🤖 Кибер-Термит v1.0</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
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
            max-width: 900px;
            overflow: hidden;
            animation: fadeIn 0.5s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .header {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        .tagline {
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 20px;
        }
        .content {
            padding: 40px;
            display: grid;
            gap: 30px;
            grid-template-columns: 1fr 1fr;
        }
        @media (max-width: 768px) {
            .content { grid-template-columns: 1fr; }
        }
        .card {
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
        }
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status-item {
            display: flex;
            align-items: center;
            padding: 15px;
            margin: 10px 0;
            background: #f8f9fa;
            border-radius: 12px;
            transition: transform 0.2s;
        }
        .status-item:hover {
            transform: translateX(5px);
        }
        .status-icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 15px;
            font-size: 1.2em;
        }
        .online { background: #4CAF50; color: white; }
        .offline { background: #f44336; color: white; }
        .warning { background: #FF9800; color: white; }
        .chat-box {
            grid-column: span 2;
            background: #f8f9fa;
            border-radius: 16px;
            padding: 30px;
        }
        @media (max-width: 768px) {
            .chat-box { grid-column: span 1; }
        }
        .messages {
            height: 300px;
            overflow-y: auto;
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border: 2px solid #e9ecef;
        }
        .message {
            margin: 10px 0;
            padding: 15px;
            border-radius: 12px;
            max-width: 80%;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-10px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin-left: auto;
            margin-right: 0;
        }
        .bot-message {
            background: #e9ecef;
            color: #333;
        }
        .input-group {
            display: flex;
            gap: 10px;
        }
        input {
            flex: 1;
            padding: 18px 25px;
            border: 2px solid #ddd;
            border-radius: 50px;
            font-size: 16px;
            outline: none;
            transition: all 0.3s;
        }
        input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        }
        button {
            padding: 18px 35px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .footer {
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            color: #666;
            border-top: 1px solid #e9ecef;
        }
        .ip-address {
            background: #e3f2fd;
            padding: 10px 20px;
            border-radius: 50px;
            font-family: monospace;
            margin: 10px 0;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Кибер-Термит</h1>
            <div class="tagline">Ваш AI ассистент с синхронизацией между устройствами</div>
            <div class="ip-address" id="ipDisplay">IP: загрузка...</div>
        </div>
        
        <div class="content">
            <div class="card">
                <h2>📡 Статус системы</h2>
                <div class="status-item">
                    <div class="status-icon online">✅</div>
                    <div>
                        <strong>Сервер Ubuntu</strong><br>
                        <small>Версия 1.0.0</small>
                    </div>
                </div>
                <div class="status-item">
                    <div class="status-icon warning">📱</div>
                    <div>
                        <strong>Телефон Android</strong><br>
                        <small id="phoneStatus">Настройте подключение</small>
                    </div>
                </div>
                <div class="status-item">
                    <div class="status-icon offline">🔄</div>
                    <div>
                        <strong>Синхронизация</strong><br>
                        <small id="syncStatus">Отключена</small>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>⚡ Быстрые действия</h2>
                <button style="width:100%; margin-bottom:15px;" onclick="testAPI()">Тест API</button>
                <button style="width:100%; margin-bottom:15px;" onclick="showIP()">Показать IP</button>
                <button style="width:100%;" onclick="setupSync()">Настроить синхронизацию</button>
            </div>
            
            <div class="chat-box">
                <h2>💬 Чат с Кибер-Термитом</h2>
                <div class="messages" id="messages">
                    <div class="message bot-message">Привет! Я Кибер-Термит. Готов к работе!</div>
                </div>
                <div class="input-group">
                    <input type="text" id="userInput" placeholder="Введите сообщение..." autocomplete="off">
                    <button onclick="sendMessage()">Отправить</button>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Кибер-Термит v1.0 | Создано на Ubuntu | Время: <span id="currentTime"></span></p>
        </div>
    </div>

    <script>
        // Обновляем время
        function updateTime() {
            document.getElementById('currentTime').textContent = 
                new Date().toLocaleTimeString('ru-RU');
        }
        setInterval(updateTime, 1000);
        updateTime();
        
        // Получаем IP адрес
        fetch('/api/ip').then(r => r.json()).then(data => {
            document.getElementById('ipDisplay').textContent = `IP: ${data.ip}:${data.port}`;
            document.getElementById('phoneStatus').textContent = 
                `Доступен по: ${data.ip}:${data.port}`;
        });
        
        // Функции чата
        function addMessage(text, isUser) {
            const messages = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = isUser ? 'message user-message' : 'message bot-message';
            messageDiv.textContent = text;
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function sendMessage() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if (!text) return;
            
            addMessage(text, true);
            input.value = '';
            
            // Эмуляция ответа AI
            setTimeout(() => {
                const responses = [
                    "Привет! Я Кибер-Термит, ваш личный AI ассистент!",
                    "Отличный вопрос! Я пока учусь, но скоро стану умнее!",
                    "Мы создаём проект вместе с DeepSeek!",
                    "Синхронизация с телефоном будет настроена позже!",
                    "Работаю на Ubuntu - лучшей ОС для разработки!"
                ];
                const response = responses[Math.floor(Math.random() * responses.length)];
                addMessage(response, false);
            }, 500);
        }
        
        // Вспомогательные функции
        function testAPI() {
            fetch('/api/status').then(r => r.json()).then(data => {
                alert(`✅ API работает!\nВерсия: ${data.version}\nСтатус: ${data.status}`);
            });
        }
        
        function showIP() {
            fetch('/api/ip').then(r => r.json()).then(data => {
                alert(`IP адрес сервера: ${data.ip}:${data.port}\nОткройте этот адрес на телефоне!`);
            });
        }
        
        function setupSync() {
            alert('Синхронизация будет настроена позже. Сейчас работаем над базовой версией!');
        }
        
        // Отправка по Enter
        document.getElementById('userInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
        
        // Автофокус на поле ввода
        document.getElementById('userInput').focus();
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
        'version': '1.0.0',
        'project': 'Кибер-Термит',
        'timestamp': datetime.now().isoformat(),
        'message': 'Сервер работает отлично!'
    })

@app.route('/api/ip')
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
    except:
        ip = 'localhost'
    return jsonify({'ip': ip, 'port': 8080})  # Изменили порт на 8080

@app.route('/api/chat', methods=['POST'])
def chat():
    # Заглушка для AI - потом добавим настоящую логику
    return jsonify({
        'response': 'Я Кибер-Термит! Работаю над улучшением интеллекта!',
        'status': 'success'
    })

if __name__ == '__main__':
    print("🤖 Запуск Кибер-Термита v1.0 на порту 8080...")
    print("🌐 Сервер будет доступен по:")
    print("   • http://localhost:8080")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        print(f"   • http://{ip}:8080 (для телефона)")
    except:
        print("   • Не удалось определить внешний IP")
    
    print("\n⚡ Для остановки: Ctrl+C")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8080, debug=True)  # Изменили порт на 8080
