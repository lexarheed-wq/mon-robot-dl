from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import re
import os
import traceback

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.errorhandler(500)
def handle_500(e):
    return jsonify({"error": "Erreur serveur"}), 500

@app.route('/')
def home():
    return jsonify({"status": "ok"})

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/api/info', methods=['POST', 'OPTIONS'])
def get_info():
    if request.method == 'OPTIONS':
        return jsonify({"ok": True})
    try:
        data = request.get_json()
        url = data.get('url') if data else None
        if not url:
            return jsonify({"error": "URL manquante"}), 400

        ydl_opts = {
            'quiet': True,
            'noplaylist': True,
            'skip_download': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'web'],
                    'player_skip': ['configs'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return jsonify({"error": "Lien non supporté, essaie TikTok/Instagram"}), 400
            return jsonify({
                "title": info.get('title', 'video'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration', 0),
                "uploader": info.get('uploader', '')
            })
    except Exception as e:
        print(traceback.format_exc())
        msg = str(e)
        if 'Sign in to confirm' in msg or 'not a bot' in msg:
            return jsonify({"error": "YouTube bloque Render (bot). Essaie un lien TikTok, Instagram, ou Facebook pour tester. Pour YouTube, réessaie avec une autre vidéo ou attends 10 min."}), 400
        return jsonify({"error": f"Erreur: {msg[:200]}"}), 400

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
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'web'],
                    'player_skip': ['configs'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return jsonify({"error": "Lien non supporté"}), 400
            title = info.get('title', 'video')
            clean_title = re.sub(r'[\\/*?:"<>|]', '_', title)[:50]
            filename = f"{clean_title}.{'mp3' if is_audio else 'mp4'}"
            formats = info.get('formats', [])
            best_url = None
            if is_audio:
                audios = [f for f in formats if f.get('acodec')!= 'none' and f.get('vcodec') == 'none']
                if audios:
                    best_url = sorted(audios, key=lambda x: x.get('abr', 0) or 0, reverse=True)[0].get('url')
            else:
                q = int(quality) if quality.isdigit() else 720
                candidates = [f for f in formats if f.get('height') and f.get('height') <= q and f.get('ext') == 'mp4']
                if not candidates:
                    candidates = [f for f in formats if f.get('height') and f.get('height') <= q]
                if candidates:
                    best_url = sorted(candidates, key=lambda x: x.get('height', 0) or 0, reverse=True)[0].get('url')
            if not best_url:
                best_url = info.get('url')
            if not best_url and formats:
                best_url = formats[-1].get('url')
            if not best_url:
                return jsonify({"error": "Pas de lien direct"}), 400
            return jsonify({"download_url": best_url, "filename": filename, "title": title})
    except Exception as e:
        print(traceback.format_exc())
        msg = str(e)
        if 'Sign in to confirm' in msg or 'not a bot' in msg:
            return jsonify({"error": "YouTube bloque ce serveur. Teste avec TikTok/Instagram, ça marche 100%."}), 400
        return jsonify({"error": f"Erreur: {msg[:200]}"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
