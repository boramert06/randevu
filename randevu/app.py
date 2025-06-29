from flask import Flask, request, render_template, redirect, url_for, session, flash
from datetime import datetime, timedelta
import hashlib
import os
from flask import jsonify
import json

app = Flask(__name__)
app.secret_key = 'gizli_anahtar'  # Güvenlik için değiştirin

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def user_exists(email):
    if not os.path.exists('users.txt'):
        return False
    with open('users.txt', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().split('|')[0] == email:
                return True
    return False

def check_user(email, password):
    if not os.path.exists('users.txt'):
        return False
    hashed = hash_password(password)
    with open('users.txt', 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 2 and parts[0] == email and parts[1] == hashed:
                return True
    return False

def get_user_fullname(email):
    if not os.path.exists('users.txt'):
        return ""
    with open('users.txt', 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 3 and parts[0] == email:
                return parts[2]  # fullname
    return email.split('@')[0]  # fallback

@app.route('/register', methods=['GET', 'POST'])
def register():
    mesaj = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        fullname = request.form.get('fullname')
        if not email or not password or not fullname:
            mesaj = "Lütfen tüm alanları doldurun."
        elif user_exists(email):
            mesaj = "Bu e-posta ile kayıtlı bir kullanıcı var."
        else:
            with open('users.txt', 'a', encoding='utf-8') as f:
                f.write(f"{email}|{hash_password(password)}|{fullname}\n")
            return redirect(url_for('login'))
    return render_template('register.html', mesaj=mesaj)

@app.route('/login', methods=['GET', 'POST'])
def login():
    mesaj = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if check_user(email, password):
            session['user'] = email
            return redirect(url_for('home'))
        else:
            mesaj = "E-posta veya şifre hatalı."
    # Giriş ekranında login.html sayfası gelir
    return render_template('login.html', mesaj=mesaj)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/randevu_iptal', methods=['POST'])
def randevu_iptal():
    if 'user' not in session:
        return redirect(url_for('login'))
    kullanici = session['user']
    tarih = request.form.get('tarih', '').strip()
    saat = request.form.get('saat', '').strip()
    kuafor = request.form.get('kuafor', '').strip()
    hizmet = request.form.get('hizmet', '').strip()
    isim = request.form.get('isim', '').strip()
    soyisim = request.form.get('soyisim', '').strip()
    telefon = request.form.get('telefon', '').strip()
    dosya_yolu = 'randevular.txt'
    yeni_satirlar = []
    silindi = False
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        yeni_satirlar = lines[:2]  # başlık ve çizgi
        for satir in lines[2:]:
            parcalar = [p.strip() for p in satir.split('|')]
            if (
                len(parcalar) >= 8 and
                parcalar[0] == tarih and
                parcalar[1] == saat and
                parcalar[2] == isim and
                parcalar[3] == soyisim and
                parcalar[4] == telefon and
                parcalar[5] == kuafor and
                parcalar[6] == hizmet and
                parcalar[7] == kullanici
            ):
                silindi = True
                continue  # bu satırı atla (sil)
            yeni_satirlar.append(satir)
        with open(dosya_yolu, 'w', encoding='utf-8') as f:
            f.writelines(yeni_satirlar)
    except FileNotFoundError:
        pass
    if silindi:
        flash("Randevunuz iptal edildi.", "success")
    else:
        flash("Randevu iptal edilemedi.", "danger")
    return redirect(url_for('randevularim'))

@app.route('/randevularim')
def randevularim():
    if 'user' not in session:
        return redirect(url_for('login'))
    kullanici = session['user']
    randevular = []
    dosya_yolu = 'randevular.txt'
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for satir in lines[2:]:  # ilk iki satır başlık ve çizgi
                parcalar = [p.strip() for p in satir.split('|')]
                # 8 sütunlu yeni kayıtlar için
                if len(parcalar) >= 8 and parcalar[7] == kullanici:
                    randevular.append({
                        'tarih': parcalar[0],
                        'saat': parcalar[1],
                        'isim': parcalar[2],
                        'soyisim': parcalar[3],
                        'telefon': parcalar[4],
                        'kuafor': parcalar[5],
                        'hizmet': parcalar[6]
                    })
    except FileNotFoundError:
        pass
    return render_template('randevularim.html', randevular=randevular)

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    mesaj = None
    saatler = [f"{str(saat).zfill(2)}:00" for saat in range(9, 19)]
    kuaforler = ["Ahmet", "Mehmet", "Ayşe", "Fatma"]
    tarih = request.form.get('tarih') if request.method == 'POST' else request.args.get('tarih')
    secili_kuafor = request.form.get('kuafor') if request.method == 'POST' else request.args.get('kuafor')
    dosya_yolu = 'randevular.txt'
    dolu_saatler = set()
    if tarih and secili_kuafor:
        try:
            with open(dosya_yolu, 'r', encoding='utf-8') as f:
                for satir in f:
                    if satir.startswith(tarih):
                        parcalar = satir.split('|')
                        if len(parcalar) > 5 and parcalar[5].strip() == secili_kuafor:
                            dolu_saatler.add(parcalar[1].strip())
        except FileNotFoundError:
            pass
    if request.method == 'POST':
        isim = request.form.get('isim')
        soyisim = request.form.get('soyisim')
        telefon = request.form.get('telefon')
        saat = request.form.get('saat')
        kuafor = request.form.get('kuafor')
        hizmet = request.form.get('hizmet')
        # Baş harfleri büyük yap
        if isim:
            isim = isim.strip().capitalize()
        if soyisim:
            soyisim = soyisim.strip().capitalize()
        # Tarihten gün adı bul ve personel çalışıyor mu kontrolü
        TURKCE_GUNLER = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
        try:
            secilen_tarih_obj = datetime.strptime(tarih, "%Y-%m-%d")
            gun_adi = TURKCE_GUNLER[secilen_tarih_obj.weekday()]
        except:
            gun_adi = None
        personel_listesi = get_personeller()
        secili_kuafor_bilgisi = next((p for p in personel_listesi if p['isim'] == kuafor), None)
        if secili_kuafor_bilgisi and gun_adi and gun_adi not in secili_kuafor_bilgisi.get('gunler', []):
            mesaj = f"{kuafor}, {gun_adi} günleri çalışmamaktadır. Lütfen farklı bir gün seçin."
        # Tüm alanlar doluysa kayıt işlemi yap
        elif not all([isim, soyisim, telefon, saat, kuafor, tarih, hizmet]):
            mesaj = "Lütfen tüm alanları doldurun."
        elif saat in dolu_saatler:
            mesaj = f"{kuafor} için {tarih} günü {saat} saati dolu! Lütfen başka bir saat veya kuaför seçin."
        else:
            mesaj = "Randevunuz başarıyla oluşturuldu!"
            kayit = f"{tarih:<12} | {saat:<5} | {isim:<15} | {soyisim:<15} | {telefon:<15} | {kuafor:<10} | {hizmet:<15} | {session['user']}\n"
            try:
                with open(dosya_yolu, 'r', encoding='utf-8') as f:
                    ilk_satir = f.readline()
            except FileNotFoundError:
                ilk_satir = ''
            with open(dosya_yolu, 'a', encoding='utf-8') as f:
                if not ilk_satir:
                    f.write(f"{'Tarih':<12} | {'Saat':<5} | {'İsim':<15} | {'Soyisim':<15} | {'Telefon':<15} | {'Kuaför':<10} | {'Hizmet':<15} | {'Email'}\n")
                    f.write('-'*110 + '\n')
                f.write(kayit)
            # Admin paneli için bildirim kaydı (isteğe bağlı, burada zaten randevular.txt okunuyor)
            # Eğer ayrı bir dosya veya bildirim sistemi istenirse burada eklenebilir.
    return render_template(
        'randevu.html',
        mesaj=mesaj,
        saatler=saatler,
        dolu_saatler=dolu_saatler,
        secili_tarih=tarih,
        kuaforler=kuaforler,
        secili_kuafor=secili_kuafor
    )

from datetime import datetime

@app.route('/degerlendirme', methods=['GET', 'POST'])
def degerlendirme():
    if 'user' not in session:
        return redirect(url_for('login'))
    mesaj = None
    dosya_yolu = 'yorumlar.txt'
    kuaforler = ["Ahmet", "Mehmet", "Ayşe", "Fatma"]
    if request.method == 'POST':
        kuafor = request.form.get('kuafor')
        puan = request.form.get('puan')
        yorum = request.form.get('yorum')
        if not all([kuafor, puan, yorum]):
            mesaj = "Lütfen tüm alanları doldurun."
        else:
            tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
            with open(dosya_yolu, 'a', encoding='utf-8') as f:
                f.write(f"{kuafor}|{puan}|{yorum}|{tarih}\n")
            mesaj = "Yorumunuz kaydedildi, teşekkürler!"
    # Yorumları oku
    yorumlar = []
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as f:
            for satir in f:
                parcalar = satir.strip().split('|')
                if len(parcalar) >= 4:
                    yorumlar.append({
                        'kuafor': parcalar[0],
                        'puan': parcalar[1],
                        'yorum': parcalar[2],
                        'tarih': parcalar[3]
                    })
    except FileNotFoundError:
        pass
    return render_template('degerlendirme.html', kuaforler=kuaforler, yorumlar=yorumlar, mesaj=mesaj)

@app.route('/ayarlar', methods=['GET', 'POST'])
def ayarlar():
    if 'user' not in session:
        return redirect(url_for('login'))
    mesaj = None
    email = session['user']
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'fullname':
            new_fullname = request.form.get('fullname')
            if not new_fullname:
                mesaj = "Ad Soyad boş olamaz."
            else:
                lines = []
                with open('users.txt', 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split('|')
                        if len(parts) >= 3 and parts[0] == email:
                            parts[2] = new_fullname
                            line = '|'.join(parts) + '\n'
                        lines.append(line)
                with open('users.txt', 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                mesaj = "Ad Soyad başarıyla güncellendi."
        elif action == 'email':
            new_email = request.form.get('new_email')
            if not new_email:
                mesaj = "Mail adresi boş olamaz."
            elif user_exists(new_email):
                mesaj = "Bu mail adresi zaten kayıtlı."
            else:
                lines = []
                updated = False
                with open('users.txt', 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split('|')
                        if len(parts) >= 3 and parts[0] == email:
                            parts[0] = new_email
                            line = '|'.join(parts) + '\n'
                            updated = True
                        lines.append(line)
                with open('users.txt', 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                if updated:
                    session['user'] = new_email
                    mesaj = "Mail adresi başarıyla güncellendi."
        elif action == 'password':
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            if not old_password or not new_password:
                mesaj = "Şifre alanları boş olamaz."
            else:
                updated = False
                lines = []
                with open('users.txt', 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split('|')
                        if len(parts) >= 3 and parts[0] == email and parts[1] == hash_password(old_password):
                            parts[1] = hash_password(new_password)
                            line = '|'.join(parts) + '\n'
                            updated = True
                        lines.append(line)
                with open('users.txt', 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                if updated:
                    mesaj = "Şifre başarıyla güncellendi."
                else:
                    mesaj = "Eski şifre yanlış!"
        elif action == 'delete':
            # Kullanıcıyı sil
            lines = []
            deleted = False
            with open('users.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split('|')
                    if len(parts) >= 3 and parts[0] == email:
                        deleted = True
                        continue  # kullanıcıyı atla
                    lines.append(line)
            with open('users.txt', 'w', encoding='utf-8') as f:
                f.writelines(lines)
            session.pop('user', None)
            if deleted:
                return redirect(url_for('login'))
            else:
                mesaj = "Hesap silinemedi."
    return render_template('ayarlar.html', mesaj=mesaj)

# Örnek hizmetler ve personeller
HIZMETLER = [
    {"ad": "Saç Kesimi", "sure": 30},
    {"ad": "Boya", "sure": 60},
    {"ad": "Manikür", "sure": 40},
    {"ad": "Fön", "sure": 25},
    {"ad": "Sakal Tıraşı", "sure": 20}
]

PERSONELLER = [
    {
        "isim": "Ahmet",
        "uzmanlik": ["Saç Kesimi", "Fön", "Sakal Tıraşı"],
        "calisma_saatleri": "09:00 - 18:00",
        "gunler": ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"],
        "takvim": ["2025-07-01 09:00", "2025-07-01 10:00"]
    },
    {
        "isim": "Mehmet",
        "uzmanlik": ["Boya", "Saç Kesimi"],
        "calisma_saatleri": "10:00 - 19:00",
        "gunler": ["Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi"],
        "takvim": ["2025-07-01 11:00", "2025-07-01 13:00"]
    },
    {
        "isim": "Ayşe",
        "uzmanlik": ["Manikür", "Boya"],
        "calisma_saatleri": "08:30 - 17:30",
        "gunler": ["Pazartesi", "Çarşamba", "Cuma", "Cumartesi"],
        "takvim": []
    },
    {
        "isim": "Fatma",
        "uzmanlik": ["Fön", "Manikür"],
        "calisma_saatleri": "09:30 - 18:30",
        "gunler": ["Pazartesi", "Salı", "Perşembe", "Cuma"],
        "takvim": []
    }
]

def get_personeller():
    dosya = 'personeller.json'
    if os.path.exists(dosya):
        with open(dosya, 'r', encoding='utf-8') as f:
            return json.load(f)
    return PERSONELLER

@app.route('/personeller')
def personeller():
    return render_template('personeller.html', personeller=get_personeller())

@app.route('/personel/<isim>')
def personel_detay(isim):
    personeller = get_personeller()
    p = next((x for x in personeller if x["isim"].lower() == isim.lower()), None)
    if not p:
        return "Personel bulunamadı", 404
    return render_template('personel_detay.html', personel=p)

ADMIN_FILE = 'admins.txt'

def is_admin():
    return session.get('admin', False)

def admin_exists(email):
    if not os.path.exists(ADMIN_FILE):
        return False
    with open(ADMIN_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().split('|')[0] == email:
                return True
    return False

def check_admin(email, password):
    if not os.path.exists(ADMIN_FILE):
        return False
    hashed = hash_password(password)
    with open(ADMIN_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 2 and parts[0] == email and parts[1] == hashed:
                return True
    return False

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    mesaj = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            mesaj = "Lütfen tüm alanları doldurun."
        elif admin_exists(email):
            mesaj = "Bu admin e-posta zaten kayıtlı."
        else:
            with open(ADMIN_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{email}|{hash_password(password)}\n")
            return redirect(url_for('admin_login'))
    return render_template('admin_register.html', mesaj=mesaj)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    mesaj = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if check_admin(email, password):
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            mesaj = "Admin e-posta veya şifre hatalı."
    return render_template('admin_login.html', mesaj=mesaj)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_panel():
    if not is_admin():
        return redirect(url_for('admin_login'))
    # Randevuları oku
    randevular = []
    dosya_yolu = 'randevular.txt'
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for satir in lines[2:]:
                parcalar = [p.strip() for p in satir.split('|')]
                if len(parcalar) >= 8:
                    randevular.append({
                        'tarih': parcalar[0],
                        'saat': parcalar[1],
                        'isim': parcalar[2],
                        'soyisim': parcalar[3],
                        'telefon': parcalar[4],
                        'kuafor': parcalar[5],
                        'hizmet': parcalar[6],
                        'email': parcalar[7]
                    })
    except FileNotFoundError:
        pass
    return render_template('admin_panel.html', randevular=randevular)

@app.route('/admin/yorum_sil/<int:yorum_id>', methods=['POST'])
def admin_yorum_sil(yorum_id):
    if not is_admin():
        return redirect(url_for('admin_login'))
    dosya_yolu = 'yorumlar.txt'
    yorumlar = []
    silindi = False
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as f:
            yorumlar = f.readlines()
        if 0 <= yorum_id < len(yorumlar):
            del yorumlar[yorum_id]
            silindi = True
        with open(dosya_yolu, 'w', encoding='utf-8') as f:
            f.writelines(yorumlar)
    except FileNotFoundError:
        pass
    return redirect(url_for('admin_yorumlar'))

@app.route('/admin/yorumlar')
def admin_yorumlar():
    if not is_admin():
        return redirect(url_for('admin_login'))
    dosya_yolu = 'yorumlar.txt'
    yorumlar = []
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as f:
            for satir in f:
                parcalar = satir.strip().split('|')
                if len(parcalar) >= 4:
                    yorumlar.append({
                        'kuafor': parcalar[0],
                        'puan': parcalar[1],
                        'yorum': parcalar[2],
                        'tarih': parcalar[3]
                    })
    except FileNotFoundError:
        pass
    return render_template('admin_yorumlar.html', yorumlar=yorumlar)

@app.route('/admin/hizmetler', methods=['GET', 'POST'])
def admin_hizmetler():
    if not is_admin():
        return redirect(url_for('admin_login'))
    dosya = 'hizmetler.json'
    # Hizmetler dosyası yoksa ilk açılışta mevcut HIZMETLER listesini kaydet
    if not os.path.exists(dosya):
        with open(dosya, 'w', encoding='utf-8') as f:
            json.dump(HIZMETLER, f, ensure_ascii=False)
    # POST ile ekleme/silme/güncelleme
    if request.method == 'POST':
        action = request.form.get('action')
        ad = request.form.get('ad')
        sure = request.form.get('sure')
        idx = request.form.get('idx')
        with open(dosya, 'r', encoding='utf-8') as f:
            hizmetler = json.load(f)
        if action == 'ekle' and ad and sure:
            hizmetler.append({"ad": ad, "sure": int(sure)})
        elif action == 'sil' and idx is not None:
            try:
                idx = int(idx)
                if 0 <= idx < len(hizmetler):
                    del hizmetler[idx]
            except:
                pass
        elif action == 'guncelle' and idx is not None and ad and sure:
            try:
                idx = int(idx)
                if 0 <= idx < len(hizmetler):
                    hizmetler[idx] = {"ad": ad, "sure": int(sure)}
            except:
                pass
        with open(dosya, 'w', encoding='utf-8') as f:
            json.dump(hizmetler, f, ensure_ascii=False)
        return redirect(url_for('admin_hizmetler'))
    # GET
    with open(dosya, 'r', encoding='utf-8') as f:
        hizmetler = json.load(f)
    return render_template('admin_hizmetler.html', hizmetler=hizmetler)

@app.route('/admin/personeller', methods=['GET', 'POST'])
def admin_personeller():
    if not is_admin():
        return redirect(url_for('admin_login'))
    dosya = 'personeller.json'
    # Personeller dosyası yoksa ilk açılışta mevcut PERSONELLER listesini kaydet
    if not os.path.exists(dosya):
        with open(dosya, 'w', encoding='utf-8') as f:
            json.dump(PERSONELLER, f, ensure_ascii=False)
    # POST ile ekleme/silme/güncelleme
    if request.method == 'POST':
        action = request.form.get('action')
        isim = request.form.get('isim')
        uzmanlik = request.form.get('uzmanlik')
        calisma_saatleri = request.form.get('calisma_saatleri')
        gunler = request.form.get('gunler')
        idx = request.form.get('idx')
        with open(dosya, 'r', encoding='utf-8') as f:
            personeller = json.load(f)
        if action == 'ekle' and isim and uzmanlik and calisma_saatleri and gunler:
            personeller.append({
                "isim": isim,
                "uzmanlik": [u.strip() for u in uzmanlik.split(',')],
                "calisma_saatleri": calisma_saatleri,
                "gunler": [g.strip() for g in gunler.split(',')],
                "takvim": []
            })
        elif action == 'sil' and idx is not None:
            try:
                idx = int(idx)
                if 0 <= idx < len(personeller):
                    del personeller[idx]
            except:
                pass
        elif action == 'guncelle' and idx is not None and isim and uzmanlik and calisma_saatleri and gunler:
            try:
                idx = int(idx)
                if 0 <= idx < len(personeller):
                    personeller[idx]["isim"] = isim
                    personeller[idx]["uzmanlik"] = [u.strip() for u in uzmanlik.split(',')]
                    personeller[idx]["calisma_saatleri"] = calisma_saatleri
                    personeller[idx]["gunler"] = [g.strip() for g in gunler.split(',')]
            except:
                pass
        with open(dosya, 'w', encoding='utf-8') as f:
            json.dump(personeller, f, ensure_ascii=False)
        return redirect(url_for('admin_personeller'))
    # GET
    with open(dosya, 'r', encoding='utf-8') as f:
        personeller = json.load(f)
    return render_template('admin_personeller.html', personeller=personeller)

@app.route('/hizmetler')
def hizmetler():
    dosya = 'hizmetler.json'
    if os.path.exists(dosya):
        with open(dosya, 'r', encoding='utf-8') as f:
            hizmetler = json.load(f)
    else:
        hizmetler = HIZMETLER
    return render_template('hizmetler.html', hizmetler=hizmetler)

# Not: randevu.html dosyası c:\Users\boram\Desktop\randevu\templates\ klasöründe olmalı.
# Not: randevu.html dosyası c:\Users\boram\Desktop\randevu\templates\ klasöründe olmalı.
if __name__ == '__main__':
    app.run(debug=True)
# Kayıt işleminden sonra sadece login sayfasına yönlendirme var, e-posta onayı yok.
# Kayıt işleminden sonra sadece login sayfasına yönlendirme var, e-posta onayı yok.
if __name__ == '__main__':
    app.run(debug=True)
# Kayıt işleminden sonra sadece login sayfasına yönlendirme var, e-posta onayı yok.
# Not: randevu.html dosyası c:\Users\boram\Desktop\randevu\templates\ klasöründe olmalı.
if __name__ == '__main__':
    app.run(debug=True)
# Kayıt işleminden sonra sadece login sayfasına yönlendirme var, e-posta onayı yok.
