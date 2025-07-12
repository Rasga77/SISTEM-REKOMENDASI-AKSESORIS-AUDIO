from flask import Flask, redirect, session, url_for
from auth import auth_bp
from admin import admin_bp
from user import user_bp

from flask import render_template

app = Flask(__name__)
app.secret_key = 'rahasia_super_aman'

# Register Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp) 
app.register_blueprint(user_bp)

@app.route('/')
def home():
    if 'user' in session:
        # Redirect ke dashboard sesuai role
        return redirect(url_for(f"{session['user']['role']}.index"))
    # Kalau belum login, arahkan ke halaman login
    return redirect(url_for('auth.login'))


# Root URL
@app.route('/')
def root():
    if 'user' in session:
        role = session['user']['role']
        if role == 'admin':
            return redirect(url_for('admin.index'))
        else:
            return f"Hai pengguna {session['user']['email']}, halaman user belum dibuat."
    return redirect(url_for('auth.login'))

# Jalankan Aplikasi
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
