from flask import Flask, request, jsonify, render_template, flash, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from kafka import KafkaProducer, KafkaConsumer
from pymongo import MongoClient
from bson import ObjectId
import redis
import json
import os
import threading
import time
import importlib.util
import pandas as pd
import plotly.express as px
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')  # Required for flash messages

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Add this line

# Database setup
mongo_client = MongoClient(os.environ.get('MONGO_URI', 'mongodb://mongodb:27017/'))
db = mongo_client.quant_platform
redis_client = redis.Redis.from_url(os.environ.get('REDIS_URL', 'redis://redis:6379/0'))

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']

@login_manager.user_loader
def load_user(user_id):
    user_data = db.users.find_one({'_id': user_id})
    return User(user_data) if user_data else None

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200
# 策略管理
@app.route('/strategy', methods=['POST'])
@login_required
def create_strategy():
    data = request.json
    strategy = {
        'name': data['name'],
        'description': data['description'],
        'code': data['code'],
        'user_id': current_user.id,
        'created_at': time.time(),
        'parameters': data.get('parameters', {}),
        'status': 'inactive'
    }
    result = db.strategies.insert_one(strategy)
    return jsonify({'strategy_id': str(result.inserted_id)})

@app.route('/strategy/<strategy_id>', methods=['GET'])
@login_required
def get_strategy(strategy_id):
    strategy = db.strategies.find_one({'_id': strategy_id, 'user_id': current_user.id})
    return jsonify(strategy)

@app.route('/strategy/<strategy_id>/backtest', methods=['POST'])
@login_required
def run_backtest(strategy_id):
    strategy = db.strategies.find_one({'_id': strategy_id, 'user_id': current_user.id})
    if not strategy:
        return jsonify({'error': 'Strategy not found'}), 404
    
    # 加载策略代码
    spec = importlib.util.spec_from_file_location(
        "strategy", f"/app/strategies/{strategy_id}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # 运行回测
    results = module.run_backtest(
        start_date=request.json['start_date'],
        end_date=request.json['end_date'],
        parameters=strategy['parameters']
    )
    
    # 存储回测结果
    backtest_result = {
        'strategy_id': strategy_id,
        'timestamp': time.time(),
        'results': results,
        'parameters': strategy['parameters']
    }
    db.backtest_results.insert_one(backtest_result)
    
    return jsonify(results)

@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch user's strategies from database
    strategies = list(db.strategies.find({'user_id': current_user.id}))
    
    # You can add more context data here
    return render_template('dashboard.html', 
                         strategies=strategies,
                         username=current_user.username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Please provide both username and password')
                return render_template('login.html')
            
            user = db.users.find_one({'username': username})
            if user and user['password'] == password:  # In production, use password hashing
                user_obj = User(user)
                login_user(user_obj)
                return redirect(url_for('dashboard'))
            
            flash('Invalid username or password')
        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred during login')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/create-new-strategy', methods=['GET', 'POST'])
@login_required
def create_new_strategy():
    if request.method == 'POST':
        strategy = {
            'name': request.form['name'],
            'description': request.form['description'],
            'user_id': current_user.id,
            'created_at': datetime.now(),
            'code': request.form['code'],
            'status': 'inactive'
        }
        db.strategies.insert_one(strategy)
        flash('Strategy created successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('create_strategy.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
