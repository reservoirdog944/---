from flask import Flask, render_template_string, jsonify, request, session
import time
import socket
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ... (весь остальной код из моего предыдущего сообщения)
