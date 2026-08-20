from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import re
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/api/info', methods=['POST'])
def get_info():
    try:
        url = request.get_json().get('url')
        if not url:
            return jsonify({"error": "URL manquante"}), 400

        ydl_opts = {
            'quiet': True,
            'noplaylist': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "title": info.get('title', 'video'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration', 0),
                "uploader": info.get('uploader', '')
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download')
def download():
    try:
        url = request.args.get('url')
        quality = request.args.get('quality', '720')
        is_audio = quality == 'mp3'

        if not url:
            return jsonify({"error": "URL manquante"}), 400

        ydl_opts = {
            'quiet': True,
            'noplaylist': True,
            'skip_download': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')

            # CORRECTION DU BUG "pattern" - nettoie le nom de fichier
            clean_title = re.sub(r'[\\/*?:"<>|]', '_', title)[:50]
            filename = f"{clean_title}.{'mp3' if is_audio else 'mp4'}"

            formats = info.get('formats', [])
            best_url = None

            if is_audio:
                audios = [f for f in formats if f.get('acodec')!= 'none' and f.get('vcodec') == 'none']
                if audios:
                    best_url = sorted(audios, key=lambda x: x.get('abr', 0) or 0, reverse=True)[0]['url']
            else:
                q = int(quality) if quality.isdigit() else 720
                # Cherche MP4 compatible tous lecteurs
                candidates = [f for f in formats if f.get('height') and f.get('height') <= q and f.get('ext') == 'mp4']
                if not candidates:
                    candidates = [f for f in formats if f.get('height') and f.get('height') <= q]
                if candidates:
                    best_url = sorted(candidates, key=lambda x: x.get('height', 0) or 0, reverse=True)[0]['url']

            # Fallback si rien trouvé
            if not best_url:
                if info.get('url'):
                    best_url = info.get('url')
                elif formats:
                    best_url = formats[-1]['url']

            if not best_url:
                return jsonify({"error": "Impossible de trouver le lien direct"}), 500

            return jsonify({
                "download_url": best_url,
                "filename": filename,
                "title": title
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
