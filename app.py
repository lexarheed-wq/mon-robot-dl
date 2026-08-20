from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp, os, tempfile, uuid
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
DOWNLOAD_DIR = tempfile.gettempdir()

@app.route('/health')
def health(): return jsonify({"status":"ok"})

@app.route('/api/info', methods=['POST'])
def get_info():
    url = request.get_json().get('url')
    with yt_dlp.YoutubeDL({'quiet':True,'noplaylist':True}) as ydl:
        info = ydl.extract_info(url, download=False)
        return jsonify({
            "title": info.get('title'),
            "thumbnail": info.get('thumbnail'),
            "duration": info.get('duration'),
            "uploader": info.get('uploader')
        })

@app.route('/api/download')
def download():
    url = request.args.get('url')
    quality = request.args.get('quality','720')
    temp_id = str(uuid.uuid4())[:8]
    is_audio = quality == 'mp3'

    # --- CORRECTION COMPATIBILITÉ ICI ---
    if is_audio:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, f'{temp_id}_%(title)s.%(ext)s'),
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'192'}],
        }
    else:
        q = int(quality) if quality.isdigit() else 720
        ydl_opts = {
            # On force MP4 + H.264 qui marche partout
            'format': f'bestvideo[height<={q}][ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height<={q}][ext=mp4]+bestaudio/best[height<={q}]/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, f'{temp_id}_%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'postprocessors': [{'key': 'FFmpegVideoConvertor','preferedformat':'mp4'}],
            # On reconvertit en H.264 + AAC pour être compatible 100% des lecteurs
            'postprocessor_args': ['-c:v','libx264','-c:a','aac','-pix_fmt','yuv420p'],
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)
        file = [os.path.join(DOWNLOAD_DIR,f) for f in os.listdir(DOWNLOAD_DIR) if temp_id in f][0]
        return send_file(file, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
