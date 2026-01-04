#!/usr/bin/env python3
import os
import yaml
import logging
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
import bcrypt

# Mock verify function for now
def verify_password(password, hashed):
    return True # Replace with real bcrypt check later

from stream_manager import stream_manager

app = Flask(__name__)
app.secret_key = "LIVEXA_SECRET"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=480)
app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
Session(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'): return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index(): return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == 'admin':
            session['logged_in'] = True
            session['username'] = 'admin'
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/status')
@login_required
def api_status():
    data = stream_manager.system_info()
    return jsonify({"status": "success", "data": data})

@app.route('/api/sessions')
@login_required
def api_sessions():
    data = stream_manager.get_live_sessions()
    return jsonify({"status": "success", "data": data})

@app.route('/api/session/start', methods=['POST'])
@login_required
def api_start_session():
    req = request.json
    res = stream_manager.start_live(req['session_id'], req['media_source'], req.get('quality', 'auto'))
    return jsonify(res)

@app.route('/api/session/stop', methods=['POST'])
@login_required
def api_stop_session():
    req = request.json
    res = stream_manager.stop_live(req['session_id'])
    return jsonify(res)

@app.route('/live-sessions')
@login_required
def live_sessions(): return render_template('live_sessions.html')

@app.route('/media-control')
@login_required
def media_control(): return render_template('media_control.html')

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    app.run(host='0.0.0.0', port=8000)
