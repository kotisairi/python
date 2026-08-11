import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'super-secure-production-key-fallback'
)

# Socket.IO configuration
socketio = SocketIO(
    app,
    cors_allowed_origins='*',
    async_mode='gevent'
)

db = SQLAlchemy(app)

# Database model
class VisitorMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0, nullable=False)

# Create DB and initial row
with app.app_context():
    db.create_all()

    if not VisitorMetric.query.first():
        db.session.add(VisitorMetric(count=0))
        db.session.commit()

@app.route('/')
def index():
    metric = VisitorMetric.query.first()
    return render_template('index.html', count=metric.count)

@app.route('/hello/<name>')
def hello_name(name):
    metric = VisitorMetric.query.first()
    return render_template('hello.html', name=name, count=metric.count)

# When a browser connects
@socketio.on('connect')
def handle_connect():
    print('Client connected')

    metric = VisitorMetric.query.first()
    metric.count += 1
    db.session.commit()

    socketio.emit('count_update', {'count': metric.count})

# When a browser disconnects
@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

    metric = VisitorMetric.query.first()

    if metric.count > 0:
        metric.count -= 1
        db.session.commit()

    socketio.emit('count_update', {'count': metric.count})

# Local run (not used by Gunicorn, but keep it)
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
