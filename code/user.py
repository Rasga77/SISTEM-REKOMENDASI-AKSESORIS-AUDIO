from flask import Blueprint, render_template, session, request, redirect, url_for
from bson import ObjectId
from pymongo import MongoClient
from auth import login_required

user_bp = Blueprint('user', __name__, url_prefix='/user')

# Koneksi MongoDB
mongo_client = MongoClient('mongodb://localhost:27017')
db = mongo_client['ecommerce_audio']
produk_collection = db['produk']
aktivitas_collection = db['aktivitas']  # Menyimpan preferensi, pembelian, dilihat

@user_bp.route('/')
@login_required

def index():
    user_id = session['user']['_id']

    # Ambil semua produk
    produk = list(produk_collection.find())

    # Produk yang disukai user
    liked_produk_ids = aktivitas_collection.find({
        'user_id': user_id,
        'jenis': 'like'
    })
    liked_ids = set([str(doc['produk_id']) for doc in liked_produk_ids])

    # ------------------------------
    # Rekomendasi 1: Dibeli Bersamaan
    beli_user = aktivitas_collection.find({
        'user_id': user_id,
        'jenis': 'beli'
    })
    produk_user_beli = [a['produk_id'] for a in beli_user]

    related_aktivitas = aktivitas_collection.find({
        'produk_id': {"$in": produk_user_beli},
        'jenis': 'beli',
        'user_id': {"$ne": user_id}
    })
    produk_terkait = {}
    for a in related_aktivitas:
        pid = a['produk_id']
        if pid not in produk_user_beli:
            produk_terkait[pid] = produk_terkait.get(pid, 0) + 1
    rekomendasi_bersamaan = list(produk_collection.find({
        '_id': {'$in': [ObjectId(pid) for pid in list(produk_terkait)[:5]]}
    }))

    # ------------------------------
    # Rekomendasi 2: Berdasarkan preferensi
    pengguna_data = db['pengguna_data'].find_one({'user_id': user_id})
    rekomendasi_preferensi = []
    if pengguna_data:
        kategori = pengguna_data.get('preferensi', {}).get('kategori', [])
        tags = pengguna_data.get('preferensi', {}).get('tags', [])

        rekomendasi_preferensi = list(produk_collection.find({
            "$or": [
                {"kategori": {"$in": kategori}},
                {"tags": {"$in": tags}}
            ]
        }).limit(10))

    # ------------------------------
    # Rekomendasi 3: Populer di kalangan user serupa
    populer_ids = []
    if pengguna_data:
        kategori = pengguna_data.get('preferensi', {}).get('kategori', [])
        pengguna_lain = db['pengguna_data'].find({
            'user_id': {'$ne': user_id},
            'preferensi.kategori': {'$in': kategori}
        })
        produk_populer = {}
        for u in pengguna_lain:
            for pid in u.get('riwayat_beli', []):
                produk_populer[pid] = produk_populer.get(pid, 0) + 1
        populer_ids = list(produk_populer)
    rekomendasi_populer = list(produk_collection.find({
        '_id': {'$in': [ObjectId(pid) for pid in populer_ids[:5]]}
    }))

    return render_template('user/index.html', 
        produk=produk, 
        liked_ids=liked_ids,
        rekomendasi_bersamaan=rekomendasi_bersamaan,
        rekomendasi_preferensi=rekomendasi_preferensi,
        rekomendasi_populer=rekomendasi_populer
    )
    
@user_bp.route('/beli/<produk_id>', methods=['GET', 'POST'])
@login_required
def beli_produk(produk_id):
    user_id = session['user']['_id']
    produk = produk_collection.find_one({'_id': ObjectId(produk_id)})

    if not produk:
        return "Produk tidak ditemukan", 404

    if request.method == 'POST':
        aktivitas_collection.insert_one({
            'user_id': user_id,
            'produk_id': produk_id,
            'jenis': 'beli'
        })
        update_user_data(user_id, produk_id, 'beli')
        return redirect(url_for('user.riwayat'))

    return render_template('user/konfirmasi_beli.html', produk=produk)

@user_bp.route('/klik/<produk_id>')
@login_required
def klik_produk(produk_id):
    user_id = session['user']['_id']
    aktivitas_collection.insert_one({
        'user_id': user_id,
        'produk_id': produk_id,
        'jenis': 'klik'
    })
    update_user_data(user_id, produk_id, 'klik')
    return redirect(url_for('user.index'))


@user_bp.route('/like/<produk_id>')
@login_required
def like_produk(produk_id):
    user_id = session['user']['_id']

    # Cek apakah sudah pernah like, jika belum baru tambahkan
    existing = aktivitas_collection.find_one({
        'user_id': user_id,
        'produk_id': produk_id,
        'jenis': 'like'
    })
    if not existing:
        aktivitas_collection.insert_one({
            'user_id': user_id,
            'produk_id': produk_id,
            'jenis': 'like'
        })
        update_user_data(user_id, produk_id, 'like') 
    return redirect(url_for('user.index'))

@user_bp.route('/keranjang/tambah/<produk_id>')
@login_required
def tambah_keranjang(produk_id):
    user_id = session['user']['_id']

    # Cek apakah sudah pernah dimasukkan ke keranjang
    existing = aktivitas_collection.find_one({
        'user_id': user_id,
        'produk_id': produk_id,
        'jenis': 'keranjang'
    })

    if not existing:
        aktivitas_collection.insert_one({
            'user_id': user_id,
            'produk_id': produk_id,
            'jenis': 'keranjang'
        })
        update_user_data(user_id, produk_id, 'keranjang')

    return redirect(url_for('user.index'))


@user_bp.route('/keranjang')
@login_required
def lihat_keranjang():
    user_id = session['user']['_id']
    aktivitas = aktivitas_collection.find({
        'user_id': user_id,
        'jenis': 'keranjang'
    })

    keranjang = []
    for item in aktivitas:
        produk = produk_collection.find_one({'_id': ObjectId(item['produk_id'])})
        if produk:
            keranjang.append(produk)

    return render_template('user/keranjang.html', keranjang=keranjang)

@user_bp.route('/keranjang/hapus/<produk_id>', methods=['POST'])
@login_required
def hapus_keranjang(produk_id):
    user_id = session['user']['_id']
    aktivitas_collection.delete_one({
        'user_id': user_id,
        'produk_id': produk_id,
        'jenis': 'keranjang'
    })
    return redirect(url_for('user.lihat_keranjang'))

@user_bp.route('/keranjang/beli/<produk_id>', methods=['POST'])
@login_required
def beli_dari_keranjang_per_produk(produk_id):
    user_id = session['user']['_id']

    # Cek apakah produk ada di keranjang
    item = aktivitas_collection.find_one({
        'user_id': user_id,
        'produk_id': produk_id,
        'jenis': 'keranjang'
    })

    if item:
        # Catat pembelian
        aktivitas_collection.insert_one({
            'user_id': user_id,
            'produk_id': produk_id,
            'jenis': 'beli'
        })

        # Hapus dari keranjang
        aktivitas_collection.delete_one({
            'user_id': user_id,
            'produk_id': produk_id,
            'jenis': 'keranjang'
        })

    return redirect(url_for('user.lihat_keranjang'))


@user_bp.route('/riwayat')
@login_required
def riwayat():
    user_id = session['user']['_id']
    aktivitas_raw = list(aktivitas_collection.find({'user_id': user_id}))

    riwayat = []
    for a in aktivitas_raw:
        produk = produk_collection.find_one({'_id': ObjectId(a['produk_id'])})
        if produk:
            riwayat.append({
                'nama_produk': produk['nama'],
                'kategori': produk.get('kategori', 'Tidak diketahui'),
                'jenis': a['jenis'],
                'waktu': str(a.get('_id').generation_time.strftime('%d-%m-%Y %H:%M'))  # Timestamp dari ObjectId
            })

    return render_template('user/riwayat.html', riwayat=riwayat)

@user_bp.route('/riwayat/hapus', methods=['POST'])
@login_required
def hapus_riwayat():
    user_id = session['user']['_id']
    aktivitas_collection.delete_many({'user_id': user_id})
    return redirect(url_for('user.riwayat'))



def update_user_data(user_id, produk_id, jenis_aktivitas):
    pengguna_data = db['pengguna_data']
    produk = produk_collection.find_one({'_id': ObjectId(produk_id)})
    
    if not produk:
        return

    kategori = produk.get('kategori')
    tags = produk.get('tags', [])

    update_fields = {}

    if jenis_aktivitas == 'beli':
        update_fields['riwayat_beli'] = produk_id
    elif jenis_aktivitas == 'klik':
        update_fields['produk_dilihat'] = produk_id
    elif jenis_aktivitas in ['like', 'keranjang']:
        if kategori:
            update_fields.setdefault('preferensi.kategori', []).append(kategori)
        for tag in tags:
            update_fields.setdefault('preferensi.tags', []).append(tag)

    # Build MongoDB update
    update_query = {"$addToSet": {}}
    for key, value in update_fields.items():
        update_query["$addToSet"][key] = value

    pengguna_data.update_one(
        {"user_id": user_id},
        update_query,
        upsert=True
    )


def rekomendasi_berdasarkan_pembelian_bersamaan(user_id):
    beli_user = aktivitas_collection.find({
        'user_id': user_id,
        'jenis': 'beli'
    })
    produk_user = [a['produk_id'] for a in beli_user]

    if not produk_user:
        return []

    # Cari pembelian user lain yang membeli produk yang sama
    related_aktivitas = aktivitas_collection.find({
        'produk_id': {"$in": produk_user},
        'jenis': 'beli',
        'user_id': {"$ne": user_id}
    })

    produk_terkait = {}
    for a in related_aktivitas:
        if a['produk_id'] not in produk_user:
            produk_terkait[a['produk_id']] = produk_terkait.get(a['produk_id'], 0) + 1

    # Urutkan berdasarkan frekuensi
    rekomendasi_ids = sorted(produk_terkait, key=produk_terkait.get, reverse=True)[:5]

    return list(produk_collection.find({'_id': {'$in': [ObjectId(pid) for pid in rekomendasi_ids]}}))


def rekomendasi_serupa(user_id):
    pengguna = db['pengguna_data'].find_one({'user_id': user_id})
    if not pengguna:
        return []

    preferensi = pengguna.get('preferensi', {})
    kategori = preferensi.get('kategori', [])
    tags = preferensi.get('tags', [])

    query = {
        "$or": [
            {"kategori": {"$in": kategori}},
            {"tags": {"$in": tags}}
        ]
    }

    return list(produk_collection.find(query).limit(5))

def rekomendasi_dari_user_serupa(user_id):
    pengguna = db['pengguna_data'].find_one({'user_id': user_id})
    if not pengguna:
        return []

    preferensi = pengguna.get('preferensi', {})
    kategori = preferensi.get('kategori', [])

    # Cari user lain yang suka kategori sama
    pengguna_lain = db['pengguna_data'].find({
        "user_id": {"$ne": user_id},
        "preferensi.kategori": {"$in": kategori}
    })

    produk_populer = {}
    for p in pengguna_lain:
        for pid in p.get('riwayat_beli', []):
            produk_populer[pid] = produk_populer.get(pid, 0) + 1

    rekomendasi_ids = sorted(produk_populer, key=produk_populer.get, reverse=True)[:5]

    return list(produk_collection.find({'_id': {'$in': [ObjectId(pid) for pid in rekomendasi_ids]}}))


