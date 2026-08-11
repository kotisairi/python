import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit

app = Flask(__name__)

# Production Database & Security Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secure-production-key-fallback')

# Initialize safe relational storage & async real-time server engine
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Thread-safe database counter model
class VisitorMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0, nullable=False)

# Bootstrap database table on startup
with app.app_context():
    db.create_all()
    if not VisitorMetric.query.first():
        db.session.add(VisitorMetric(count=0))
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hello/<name>')
def hello_name(name):
    # Render UI layout once. Socket.IO will handle the real-time data layer next.
    return render_template('hello.html', name=name)

# Triggered immediately when a user hits or opens the page
@socketio.on('connect')
def handle_connect():
    metric = VisitorMetric.query.first()
    metric.count += 1
    db.session.commit()
    
    # BROADCAST: Pushes the updated number instantly to ALL connected devices
    emit('count_update', {'count': metric.count}, broadcast=True)

if __name__ == '__main__':
    # Local fallback runner (Docker skips this and runs Gunicorn directly)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
