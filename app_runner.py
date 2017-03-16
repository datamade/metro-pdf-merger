from flask import Flask
from app import *

app = Flask(__name__)
app.config.from_object('config')

queue_daemon(app)