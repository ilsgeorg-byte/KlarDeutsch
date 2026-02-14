from flask import Flask

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return "Hello from Flask on Vercel!"

# Vercel требует, чтобы объект приложения назывался 'app'
