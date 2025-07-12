from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson import ObjectId
from auth import admin_required
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

mongo_client = MongoClient('mongodb://localhost:27017')
db = mongo_client['ecommerce_audio']
produk_collection = db['produk']

@admin_bp.route('/')
@admin_required
def index():
    produk = list(produk_collection.find())
    return render_template('admin/index.html', produk=produk)

@admin_bp.route('/produk/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_produk():
    if request.method == 'POST':
        data = {
            'nama': request.form['nama'],
            'deskripsi': request.form['deskripsi'],
            'kategori': request.form['kategori'],
            'harga': float(request.form['harga']),
            'tags': request.form.get('tags', '').split(',')
        }
        gambar = request.files['gambar']
        filename = secure_filename(gambar.filename)
        gambar.save(os.path.join('static/uploads', filename))
        data['gambar'] = filename
        produk_collection.insert_one(data)
        return redirect(url_for('admin.index'))
    return render_template('admin/tambah_produk.html')

@admin_bp.route('/produk/hapus/<produk_id>', methods=['POST'])
@admin_required
def hapus_produk(produk_id):
    produk = produk_collection.find_one({'_id': ObjectId(produk_id)})
    if produk and 'gambar' in produk:
        # Hapus file gambar dari folder static/uploads jika ada
        try:
            os.remove(os.path.join('static/uploads', produk['gambar']))
        except:
            pass  # file mungkin sudah tidak ada

    produk_collection.delete_one({'_id': ObjectId(produk_id)})
    return redirect(url_for('admin.index'))

@admin_bp.route('/produk/edit/<produk_id>', methods=['GET', 'POST'])
@admin_required
def edit_produk(produk_id):
    produk = produk_collection.find_one({'_id': ObjectId(produk_id)})

    if not produk:
        return "Produk tidak ditemukan", 404

    if request.method == 'POST':
        update_data = {
            'nama': request.form['nama'],
            'deskripsi': request.form['deskripsi'],
            'kategori': request.form['kategori'],
            'harga': float(request.form['harga']),
            'tags': request.form.get('tags', '').split(',')
        }

        gambar = request.files.get('gambar')
        if gambar and gambar.filename:
            # Hapus gambar lama
            if 'gambar' in produk:
                try:
                    os.remove(os.path.join('static/uploads', produk['gambar']))
                except:
                    pass

            filename = secure_filename(gambar.filename)
            gambar.save(os.path.join('static/uploads', filename))
            update_data['gambar'] = filename
        else:
            # Pertahankan gambar lama jika tidak ada gambar baru
            update_data['gambar'] = produk.get('gambar', '')

        produk_collection.update_one({'_id': ObjectId(produk_id)}, {'$set': update_data})
        return redirect(url_for('admin.index'))

    return render_template('admin/edit_produk.html', produk=produk)
