# 🎧 Aplikasi Rekomendasi Aksesoris Audio (Flask + MongoDB)

Aplikasi web berbasis Flask untuk memberikan rekomendasi produk audio seperti headphone, speaker, dll, menggunakan MongoDB sebagai database utama.

---

## 📦 Struktur Singkat

- `app.py` – file utama untuk menjalankan aplikasi
- `templates/` – menyimpan tampilan HTML (Flask Jinja2)
- `static/uploads/` – tempat gambar produk
- `auth.py`, `user.py` – blueprint untuk login, register, dan fitur pengguna
- `pengguna`,`pengguna_data`, `aktivitas`, `produk` – koleksi utama di MongoDB

---

## 🧰 Setup Lingkungan

    Install Dependensi :
    pip install -r requirements.txt

    Instalasi dan Setup MongoDB :

   1. Install MongoDB Community Edition
        Unduh dari: https://www.mongodb.com/try/download/community
        Ikuti instruksi instalasi sesuai OS
   2. Jalankan MongoDB secara lokal

    Cara Menjalankan Aplikasi :
    Jalankan server:
    - python app.py
    Akses di browser:
    - http://127.0.0.1:5000
    

        


