from flask import Blueprint, render_template, session
from ..security import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('index.html', username=session.get('username'))
