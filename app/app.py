from flask import Flask, render_template
import prometheus_client
from prometheus_client import Counter, generate_latest

app = Flask(__name__)

REQUEST_COUNT = Counter('app_requests_total', 'Total des requêtes reçues')

@app.route('/')
def home():
    REQUEST_COUNT.inc()
    return render_template("index.html")

@app.route('/metrics')
def metrics():
    return generate_latest(REQUEST_COUNT), 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
