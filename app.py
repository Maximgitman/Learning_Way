from flask import Flask

app = Flask(__name__)

from actions import *
from views import *