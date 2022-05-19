from flask import Blueprint, request, render_template, flash, redirect

bp = Blueprint('auth-login', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        # TODO: check if login and password is ok
        # TODO: generate JWT token and store it in the cookie
        error = 'Invalid credentials'

        if error is None:
            return redirect('__PUT_FRONT_URL_HERE__')

        flash(error)

    return render_template('auth/login.html')
