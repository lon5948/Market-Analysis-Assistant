from flask import Blueprint, render_template
from flask_login import login_required, current_user
import pandas as pd
import os

chat = Blueprint('chat', __name__)

@chat.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html')
