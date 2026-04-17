import os
import uuid
import yt_dlp
from datetime import datetime
from flask import Flask, request, render_template_string, send_from_directory

app = Flask(__name__)

# مجلد التحميلات
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# تخزين مؤقت للروابط
url_cache = {}

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>ADAMOX DOWNLOAD PRO</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Cairo:wght@400;600;800&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root { --accent: #6366f1; --accent-2: #a855f7; --bg: #020617; --glass: rgba(255, 255, 255, 0.05); --border: rgba(255, 255, 255, 0.1); }
        body { margin: 0; font-family: 'Cairo', sans-serif; background: var(--bg); color: #fff; background-image: radial-gradient(circle at top, #1e1b4b, #020617); min-height: 100vh; overflow-x: hidden; }
        .container { max-width: 850px; margin: 0 auto; padding: 20px; min-height: 80vh; box-sizing: border-box; }
        .logo { text-align: center; font-family: 'Orbitron'; font-size: 2.5rem; padding: 20px 0; background: linear-gradient(to right, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

        .search-wrapper { background: var(--glass); padding: 5px; border-radius: 50px; border: 1px solid var(--border); display: flex; margin-bottom: 30px; backdrop-filter: blur(10px); }
        .search-wrapper input { flex: 1; background: transparent; border: none; padding: 12px 25px; color: #fff; outline: none; font-size: 1rem; width: 10%; }
        .search-wrapper button { background: linear-gradient(135deg, var(--accent), var(--accent-2)); border: none; padding: 10px 35px; border-radius: 50px; color: #fff; font-weight: bold; cursor: pointer; transition: 0.3s; white-space: nowrap; }

        .result-card { display: flex; flex-direction: row; gap: 20px; background: rgba(255, 255, 255, 0.02); padding: 20px; border-radius: 25px; border: 1px solid var(--border); backdrop-filter: blur(15px); animation: fadeIn 0.5s ease; box-sizing: border-box; align-items: flex-start; }
        .image-part { flex: 0 0 35%; border-radius: 18px; overflow: hidden; border: 2px solid var(--accent); box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .image-part img { width: 100%; aspect-ratio: 9/16; object-fit: cover; display: block; }

        .content-part { flex: 1; display: flex; flex-direction: column; gap: 15px; min-width: 0; }
        .info-box { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 18px; border: 1px solid var(--border); }

        .uploader-name { font-size: 1.2rem; font-weight: 800; color: #fff; display: block; margin-bottom: 5px; word-wrap: break-word; }
        .meta-data { font-size: 0.8rem; color: #94a3b8; display: flex; gap: 15px; margin-bottom: 10px; flex-wrap: wrap; }
        .badge { background: var(--accent); color: white; padding: 2px 8px; border-radius: 5px; font-size: 0.65rem; font-family: 'Orbitron'; white-space: nowrap; }

        .video-description { font-size: 0.85rem; color: #cbd5e1; line-height: 1.6; margin: 0; max-height: 100px; overflow-y: auto; word-wrap: break-word; }

        .action-btns { display: flex; flex-direction: column; gap: 10px; }
        .dl-btn { display: flex; align-items: center; justify-content: space-between; background: var(--glass); padding: 15px 20px; border-radius: 15px; text-decoration: none; color: #fff; border: 1px solid var(--border); transition: 0.3s; gap: 10px; cursor: pointer; }
        .dl-btn:hover { background: rgba(255,255,255,0.1); border-color: var(--accent); transform: translateX(-5px); }
        .dl-btn i { font-size: 1.3rem; color: var(--accent); flex-shrink: 0; }
        .dl-btn-text { flex: 1; min-width: 0; }
        .dl-btn b { display: block; word-wrap: break-word; }

        .footer-content { padding: 40px 20px; background: rgba(0, 0, 0, 0.3); border-top: 1px solid var(--border); margin-top: 50px; text-align: center; box-sizing: border-box; }
        .social-links { display: flex; justify-content: center; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
        .social-btn { width: 45px; height: 45px; display: flex; align-items: center; justify-content: center; background: var(--glass); border: 1px solid var(--border); border-radius: 50%; color: #fff; text-decoration: none; transition: 0.3s; font-size: 1.2rem; flex-shrink: 0; }
        .social-btn:hover { background: var(--accent); transform: translateY(-5px); box-shadow: 0 5px 15px rgba(99, 102, 241, 0.4); }
        .copyright { font-family: 'Orbitron'; font-size: 0.8rem; color: #94a3b8; letter-spacing: 1px; line-height: 2; word-wrap: break-word; }
        .dev-name { color: var(--accent-2); font-weight: bold; text-decoration: none; }

        @media (max-width: 650px) {
            .container { padding: 10px; }
            .logo { font-size: 1.8rem; padding: 10px 0; }
            .result-card { flex-direction: row; gap: 10px; padding: 10px; border-radius: 15px; }
            .image-part { flex: 0 0 30%; border-radius: 10px; }
            .info-box { padding: 10px; border-radius: 10px; }
            .uploader-name { font-size: 0.9rem; }
            .meta-data { font-size: 0.65rem; gap: 8px; }
            .video-description { font-size: 0.7rem; max-height: 60px; }
            .dl-btn { padding: 8px 10px; border-radius: 10px; gap: 5px; }
            .dl-btn b { font-size: 0.75rem; }
            .dl-btn small { font-size: 0.6rem; }
            .dl-btn i { font-size: 1rem; }
            .social-btn { width: 35px; height: 35px; font-size: 0.9rem; }
        }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">ADAMOX TIK V1</div>
        <form method="POST" class="search-wrapper">
            <input type="text" name="url" placeholder="أدخل الرابط..." required>
            <button type="submit" id="extractBtn">استخراج</button>
        </form>

        {% if v %}
        <div class="result-card">
            <div class="image-part">
                <img src="{{ v.thumbnail }}" alt="Cover">
            </div>

            <div class="content-part">
                <div class="info-box">
                    <span style="color: var(--accent-2); font-size: 0.7rem; font-weight: bold;">الناشر:</span>
                    <span class="uploader-name">{{ v.uploader }}</span>
                    <div class="meta-data">
                        <span><i class="far fa-calendar-alt"></i> {{ v.upload_date }}</span>
                        <span class="badge">ULTRA HD</span>
                    </div>
                    <hr style="border: 0; border-top: 1px solid var(--border); margin: 5px 0;">
                    <p class="video-description">{{ v.description }}</p>
                </div>

                <div class="action-btns">
                    <a onclick="handleDownload('/download/video/{{ v.id }}', this)" class="dl-btn">
                        <div class="dl-btn-text"><b>تحميل فيديو</b><br><small style="color: #94a3b8;">MP4</small></div>
                        <i class="fas fa-video"></i>
                    </a>

                    <a onclick="handleDownload('/download/audio/{{ v.id }}', this)" class="dl-btn" style="border-color: rgba(168, 85, 247, 0.4);">
                        <div class="dl-btn-text"><b>تحميل صوت</b><br><small style="color: #94a3b8;">MP3</small></div>
                        <i class="fas fa-headphones"></i>
                    </a>
                </div>
            </div>
        </div>
        {% endif %}
    </div>

    <footer class="footer-content">
        <div class="social-links">
            <a href="https://wa.me/212617023793" class="social-btn"><i class="fab fa-whatsapp"></i></a>
            <a href="https://www.tiktok.com/@veenoom__x" class="social-btn"><i class="fab fa-tiktok"></i></a>
            <a href="https://instagram.com/veenoom__x" class="social-btn"><i class="fab fa-instagram"></i></a>
            <a href="https://t.me/O_F_P_1" class="social-btn"><i class="fab fa-telegram-plane"></i></a>
        </div>
        <div class="copyright">&copy; 2026 تم التطوير بواسطة <a href="#" class="dev-name">ADAMOX ULTRA</a><br><span>جميع الحقوق محفوظة</span></div>
    </footer>

    <script>
        // دالة لمنع مغادرة الصفحة عند التحميل
        function handleDownload(url, element) {
            const originalContent = element.innerHTML;
            element.style.pointerEvents = 'none';
            element.style.opacity = '0.7';
            element.querySelector('b').innerText = 'جاري التحميل...';

            // إنشاء عنصر مخفي للتحميل
            const link = document.createElement('a');
            link.href = url;
            link.target = '_blank'; // الفتح في خلفية مخفية
            link.download = ''; 
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // إعادة الزر لحالته بعد ثواني
            setTimeout(() => {
                element.innerHTML = originalContent;
                element.style.pointerEvents = 'auto';
                element.style.opacity = '1';
            }, 3000);
        }

        document.querySelector('form').onsubmit = function() {
            document.getElementById('extractBtn').innerText = '...';
        };
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    v_data = None
    if request.method == "POST":
        url = request.form.get("url")
        unique_id = str(uuid.uuid4())
        ydl_opts = {'quiet': True, 'no_warnings': True, 'user_agent': 'Mozilla/5.0'}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                raw_date = info.get('upload_date', datetime.now().strftime('%Y%m%d'))
                formatted_date = datetime.strptime(raw_date, '%Y%m%d').strftime('%d/%m/%Y')
                v_data = {
                    'id': unique_id,
                    'thumbnail': info.get('thumbnail'),
                    'description': info.get('description', '...').strip()[:200],
                    'uploader': info.get('uploader', 'ناشر غير معروف'),
                    'upload_date': formatted_date
                }
                url_cache[unique_id] = url
        except Exception as e:
            print(f"Error: {e}")
    return render_template_string(HTML, v=v_data)

@app.route("/download/<mode>/<id>")
def download(mode, id):
    original_url = url_cache.get(id)
    if not original_url: return "خطأ", 404
    ext = "mp3" if mode == "audio" else "mp4"
    filepath_no_ext = os.path.join(DOWNLOAD_FOLDER, id)
    ydl_opts = {'outtmpl': filepath_no_ext, 'quiet': True, 'ffmpeg_location': os.getcwd()}
    if mode == "audio":
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]})
    else:
        ydl_opts.update({'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 'merge_output_format': 'mp4'})
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([original_url])
        actual_file = f"{filepath_no_ext}.{ext}"
        if not os.path.exists(actual_file): actual_file = filepath_no_ext
        return send_from_directory(DOWNLOAD_FOLDER, os.path.basename(actual_file), as_attachment=True)
    except Exception as e: return str(e)

if __name__ == "__main__":
    app.run(debug=True, port=8000)