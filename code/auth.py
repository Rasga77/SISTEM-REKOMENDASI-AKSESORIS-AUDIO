from flask import Blueprint, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson import ObjectId
from functools import wraps

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Koneksi ke MongoDB
mongo_client = MongoClient('mongodb://localhost:27017')
db = mongo_client['ecommerce_audio']
pengguna_collection = db['pengguna']

# ================================
# Middleware: login_required
# ================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# ================================
# Middleware: admin_required
# ================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['user']['role'] != 'admin':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# ================================
# Login Route
# ================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = pengguna_collection.find_one({'email': email, 'password': password})
        if user:
            session['user'] = {
                '_id': str(user['_id']),
                'email': user.get('email', ''),
                'role': user.get('role', 'user')
            }

            # Redirect berdasarkan role
            if user['role'] == 'admin':
                return redirect(url_for('admin.index'))
            else:
                return redirect(url_for('user.index'))
        
        return render_template('login.html', error='Email atau password salah')
    
    return render_template('login.html')

# ================================
# Register Route
# ================================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role'].lower()  # pastikan huruf kecil

        # Cek jika email sudah terdaftar
        if pengguna_collection.find_one({'email': email}):
            return render_template('register.html', error='Email sudah digunakan')

        pengguna_collection.insert_one({
            'email': email,
            'password': password,
            'role': role
        })
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

# ================================
# Logout Route
# ================================
@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('auth.login'))
