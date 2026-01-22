#!/bin/bash
echo "🤖 ЗАПУСК КИБЕР-ТЕРМИТА..."
echo "=========================="

# Проверяем Flask
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Устанавливаем Flask..."
    pip3 install flask
fi

# Запускаем
cd "$(dirname "$0")"
python3 кибертермит.py
