import asyncio
from datetime import datetime
import hashlib
import os
import random
import threading
from flask import Flask
import requests
from telegram import BotCommand, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# --- 1. RENDER İÇİN WEB SUNUCUSU ---
app_web = Flask('')


@app_web.route('/')
def home():
    return 'Bot 7/24 Canli!'


def run_web():
    app_web.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()


# --- 2. BOT AYARLARI ---
ADMIN_ID = 8200746117
TOKEN = '8870037601:AAFmFTITU4Fi9H2wrXZpu1tRNfjOT4DXCxw'
BELO_ID = 8200746117

itiraflar = []
HEDEF_GRUP_ID = None

# Gruptaki kullanıcıları ID ve Ad olarak tutan hafıza
grup_uyeleri = {}
gunun_cifti_hafiza = {}


# --- 3. PRO ASTROLOJİ HAVUZU ---
BURC_ISIMLERI = {
    'koc': 'Koç',
    'boga': 'Boğa',
    'ikizler': 'İkizler',
    'yengec': 'Yengeç',
    'aslan': 'Aslan',
    'basak': 'Başak',
    'terazi': 'Terazi',
    'akrep': 'Akrep',
    'yay': 'Yay',
    'oglak': 'Oğlak',
    'kova': 'Kova',
    'balik': 'Balık',
}

GENEL_DURUM = [
    (
        'Yönetici gezegeninin açıları bugün sana içsel bir huzur ve yüksek bir'
        ' farkındalık getiriyor. Sezgilerine güven.'
    ),
    (
        'Bugün gökyüzü, geçmişte bıraktığını sandığın bazı konuları tekrar'
        ' gündeme getirebilir. Sakin kalmalı ve mantığını kullanmalısın.'
    ),
    (
        'Enerjinin çok yüksek olduğu bir gün! Çevrendekileri motive eden, lider'
        ' ruhunu ortaya koyan bir tavrın var.'
    ),
    (
        "Ay'ın konumu duygusal olarak dalgalanmalara açık olduğunu gösteriyor."
        ' Olaylara objektif bir pencereden bakmaya çalış.'
    ),
    (
        'Uzun zamandır zihnini kurcalayan o belirsizlik bugün yerini net'
        ' kararlara bırakıyor. Harekete geçmek için doğru zaman.'
    ),
    (
        'Güne hafif bir yorgunlukla başlasan da öğleden sonra alacağın ufak bir'
        ' haberle tüm enerjin değişebilir.'
    ),
    (
        'Bugün yıldızlar, konfor alanından çıkman için seni destekliyor. Yeni'
        ' başlangıçlara ve risklere açıksın.'
    ),
    (
        'İletişim evindeki hareketlilik, bugün yanlış anlaşılmalara yol açabilir.'
        ' Söylediklerine ve mesajlarına ekstra dikkat et.'
    ),
    (
        'Beklemediğin insanlardan destek göreceğin, şansın senden yana olduğu'
        ' oldukça pozitif bir gün.'
    ),
    (
        'Zihnin çok yoğun. Her şeyi aynı anda düşünmek yerine işleri sıraya'
        ' koyarsan çok daha rahat edeceksin.'
    ),
]

IS_PARA = [
    (
        'Kariyer evindeki olumlu etkileşimler, uzun süredir beklediğin takdiri'
        ' görmeni sağlayabilir.'
    ),
    (
        'Maddi konularda beklenmedik harcamalar çıkabilir, bütçeni kontrol'
        ' altında tutmakta fayda var.'
    ),
    (
        'İş yerinde veya okulda üstlendiğin sorumluluklar artabilir, ancak'
        ' disiplinli yapınla hepsinin üstesinden geleceksin.'
    ),
    (
        'Yaratıcılığının zirvesinde olduğun bir dönem. Yeni projeler üretmek'
        ' veya parlak fikirlerini sunmak için harika bir gün.'
    ),
    (
        'Bugün finansal konularda risk almaktan kaçınmalı, elindeki kaynakları'
        ' korumaya odaklanmalısın.'
    ),
    (
        'Ortaklı işlerde veya takım çalışmalarında parlayacağın, sözünün'
        ' dinleneceği bir gündesin.'
    ),
    (
        'Uzun vadeli hedeflerin için bugün atacağın ufak bir adım, ileride büyük'
        ' kazançlara dönüşebilir.'
    ),
    (
        'Gereksiz detaylara takılıp vakit kaybedebilirsin. Odak noktanı büyük'
        ' resme çevirmelisin.'
    ),
]

ASK_ILISKI = [
    (
        'İkili ilişkilerde romantizmin ve tutkunun arttığı bir gün. Karşındaki'
        ' kişiyle arandaki bağ güçleniyor.'
    ),
    (
        'Aşk hayatında iletişim sorunları yaşanabilir. Karşındakini dinlemeden'
        ' fevri tepkiler vermekten kaçınmalısın.'
    ),
    (
        'Eğer yalnızsan, sosyal çevrende katılacağın bir ortamda beklemediğin'
        ' kadar etkileyici biriyle tanışabilirsin.'
    ),
    (
        'İlişkilerinde gereksiz kıskançlıklar veya kuruntular yüzünden kendini'
        ' yıpratma. Akışta kalmak en iyisi.'
    ),
    (
        'Sevdiklerine zaman ayırmak, değer verdiğin insanlarla dertleşmek bugün'
        ' ruhuna ilaç gibi gelecek.'
    ),
    (
        'Geçmişten gelen bir mesaj veya karşılaşma kafanı karıştırabilir, eski'
        ' defterleri açmadan önce iyi düşün.'
    ),
    (
        'Duygularını açıkça ifade etmekten çekinme. Bugün dürüstlük sana'
        ' partnerinle aranda yepyeni kapılar açacak.'
    ),
    (
        'Kendi iç dünyana çekilip ilişkilerini sorgulayabilirsin. Kendi'
        ' değerini bilerek hareket et.'
    ),
]


# --- 4. 30 DAKİKADA BİR OTOMATİK MESAJ ---
async def otomatik_duyuru(app):
    global HEDEF_GRUP_ID
    while True:
        await asyncio.sleep(600)
        if HEDEF_GRUP_ID:
            try:
                duyuru_metni = (
                    'HALK KAZANDI MİLLET KAZANDI DEVLET KAZANDI KAPTAN HALİT TUĞRUL OYLARIN %51'ini ALARAK TEK BAŞINA İKTİDAR'
                )
                await app.bot.send_message(
                    chat_id=HEDEF_GRUP_ID, text=duyuru_metni
                )
            except Exception as e:
                print(f'Otomatik duyuru hatası: {e}')


# --- 5. KOMUTLAR VE OTOMATİK MENÜ ---
async def post_init(app):
    komutlar = [
        BotCommand('itiraf', 'Anonim itiraf gönder (Sadece özel mesajda)'),
        BotCommand('itirafgetir', 'Havuza eklenen itirafı gruba getir'),
        BotCommand('hava', 'Hava durumunu öğren (Örn: /hava izmit)'),
        BotCommand('burc', 'Günlük burç yorumu (Örn: /burc koc)'),
        BotCommand('belo', 'Belo ve Fehmiyi etiketler'),
        BotCommand('cift', 'Günün çiftini seçer ❤️'),
    ]
    await app.bot.set_my_commands(komutlar)
    asyncio.create_task(otomatik_duyuru(app))


def grup_ve_kullanici_kaydet(update: Update):
    global HEDEF_GRUP_ID, grup_uyeleri
    if update.effective_chat and update.effective_chat.type in [
        'group',
        'supergroup',
    ]:
        chat_id = update.effective_chat.id
        HEDEF_GRUP_ID = chat_id

        if chat_id not in grup_uyeleri:
            grup_uyeleri[chat_id] = {}

        user = update.effective_user
        if user and not user.is_bot:
            grup_uyeleri[chat_id][user.id] = user.full_name


# HER MESAJDA KULLANICI KAYDEDEN DINLEYICI
async def mesaj_dinleyici(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grup_ve_kullanici_kaydet(update)


# 🌤️ HAVA DURUMU
async def hava_durumu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grup_ve_kullanici_kaydet(update)
    sehir = ' '.join(context.args) if context.args else 'Izmit'
    try:
        headers = {'User-Agent': 'curl/7.68.0'}
        url = f'https://wttr.in/{sehir}?format=%C+%t+%w&lang=tr'
        res = requests.get(url, headers=headers, timeout=5)

        if res.status_code == 200 and 'Unknown' not in res.text:
            durum = res.text.strip()
            mesaj = f'🌤️ {sehir.capitalize()} için Hava Durumu:\n\n{durum}'
        else:
            mesaj = '⚠️ Şehir bulunamadı. Örnek kullanım: /hava izmit'
    except Exception:
        mesaj = '⚠️ Hava durumu bilgisi alınamadı, lütfen tekrar deneyin.'

    await update.message.reply_text(mesaj)


# 🔮 GÜNLÜK BURÇ YORUMU
async def burc_yorum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grup_ve_kullanici_kaydet(update)
    if not context.args:
        await update.message.reply_text(
            'Lütfen bir burç adı yazın. Örnek: /burc koc\n'
            'Burçlar: koc, boga, ikizler, yengec, aslan, basak, terazi, akrep,'
            ' yay, oglak, kova, balik'
        )
        return

    girdi = context.args[0].lower().strip()
    tr_map = {
        'koç': 'koc',
        'boğa': 'boga',
        'yengeç': 'yengec',
        'başak': 'basak',
        'oğlak': 'oglak',
        'balık': 'balik',
    }
    burc_key = tr_map.get(girdi, girdi)

    if burc_key not in BURC_ISIMLERI:
        await update.message.reply_text(
            '⚠️ Geçersiz burç adı. Örnek kullanım: /burc koc'
        )
        return

    burc_adi = BURC_ISIMLERI[burc_key]
    bugun_str = datetime.now().strftime('%Y-%m-%d')
    tarih_str = datetime.now().strftime('%d.%m.%Y')

    h_genel = int(
        hashlib.md5(f'{bugun_str}-{burc_key}-genel'.encode('utf-8')).hexdigest(),
        16,
    )
    h_is = int(
        hashlib.md5(f'{bugun_str}-{burc_key}-is'.encode('utf-8')).hexdigest(), 16
    )
    h_ask = int(
        hashlib.md5(f'{bugun_str}-{burc_key}-ask'.encode('utf-8')).hexdigest(),
        16,
    )

    idx_genel = h_genel % len(GENEL_DURUM)
    idx_is = h_is % len(IS_PARA)
    idx_ask = h_ask % len(ASK_ILISKI)

    mesaj = (
        f'🔮 {burc_adi.upper()} BURCU GÜNLÜK YORUMU ({tarih_str}):\n\n'
        f'✨ Genel Durum:\n{GENEL_DURUM[idx_genel]}\n\n'
        f'💼 İş ve Para:\n{IS_PARA[idx_is]}\n\n'
        f'❤️ Aşk ve İlişkiler:\n{ASK_ILISKI[idx_ask]}'
    )

    await update.message.reply_text(mesaj)


# ❤️ GÜNÜN ÇİFTİ KOMUTU
async def gunun_cifti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grup_ve_kullanici_kaydet(update)
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Bu komut sadece gruplarda çalışır.")
        return

    chat_id = update.effective_chat.id
    uyeler = grup_uyeleri.get(chat_id, {})

    if len(uyeler) < 2:
        await update.message.reply_text("⚠️ Günün çiftini seçmek için grupta en az 2 kişinin mesaj yazmış olması gerekir.")
        return

    bugun_str = datetime.now().strftime('%Y-%m-%d')
    tarih_str = datetime.now().strftime('%d.%m.%Y')

    # Eğer bugün bu grup için zaten çift seçildiyse hafızadan getir
    if chat_id in gunun_cifti_hafiza and gunun_cifti_hafiza[chat_id]['tarih'] == bugun_str:
        secilenler = gunun_cifti_hafiza[chat_id]['cift']
        uyum = gunun_cifti_hafiza[chat_id]['uyum']
    else:
        # Bugün henüz seçilmediyse yeni çift seç ve kaydet
        secilenler = random.sample(list(uyeler.items()), 2)
        uyum = random.randint(85, 100)
        gunun_cifti_hafiza[chat_id] = {
            'tarih': bugun_str,
            'cift': secilenler,
            'uyum': uyum
        }

    mesaj = (
        f"💘 GÜNÜN ÇİFTİ ({tarih_str}) 💘\n\n"
        f"👩‍❤️‍👨 {secilenler[0][1]}  +  {secilenler[1][1]}\n\n"
        f"Uyum Derecesi: %{uyum} 🔥\n"
        f"Harikasınız Bebeğim! 🎉"
    )
    await update.message.reply_text(mesaj)

# 🏷️ BELO VE FEHMİ ETİKETLEME
async def belo_etiketle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grup_ve_kullanici_kaydet(update)
    belo_metin = f'[belo](tg://user?id={BELO_ID})'
    mesaj = f'{belo_metin} @fehmi99'
    await update.message.reply_text(mesaj, parse_mode='Markdown')


# 📩 İTİRAF SİSTEMİ
async def itiraf_et(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != 'private':
        await update.message.reply_text(
            'İtirafları sadece özel mesajdan gönderebilirsin!'
        )
        return

    metin = ' '.join(context.args)
    if not metin:
        await update.message.reply_text(
            'Lütfen itirafını yaz. Örnek: /itiraf Hocaya aşık oldum'
        )
        return

    user = update.effective_user
    zaman = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    numarali_itiraf = f'📢 ANONİM İTİRAF:\n\n{metin}'
    itiraflar.append(numarali_itiraf)

    if ADMIN_ID != 0:
        admin_mesaj = (
            f'📥 YENİ İTİRAF HAVUZA EKLENDİ\n\n'
            f'👤 Gönderen: {user.full_name} (@{user.username})\n'
            f'🆔 User ID: {user.id}\n'
            f'🕒 Zaman: {zaman}\n\n'
            f'📝 İtiraf: {metin}'
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_mesaj)
        except Exception as e:
            print(f'Admin bildirim hatası: {e}')

    await update.message.reply_text(
        'İtirafın anonim olarak havuza kaydedildi! 👍'
    )


async def itiraf_getir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grup_ve_kullanici_kaydet(update)
    if not itiraflar:
        await update.message.reply_text('Şu an havuzda hiç itiraf yok!')
        return

    siradaki_itiraf = itiraflar.pop(0)
    await update.message.reply_text(siradaki_itiraf)


if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    # Gruptaki her normal mesajda gönderen kişiyi hafızaya alan dinleyici
    app.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), mesaj_dinleyici)
    )

    app.add_handler(CommandHandler('itiraf', itiraf_et))
    app.add_handler(CommandHandler('itirafgetir', itiraf_getir))
    app.add_handler(CommandHandler('hava', hava_durumu))
    app.add_handler(CommandHandler('burc', burc_yorum))
    app.add_handler(CommandHandler('belo', belo_etiketle))
    app.add_handler(CommandHandler('cift', gunun_cifti))

    print('Bot aktif!')
    app.run_polling()
