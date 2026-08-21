from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import yt_dlp
import requests
import os
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.errorhandler(500)
def err500(e):
    return jsonify({"error": "Erreur serveur"}), 500

@app.route('/')
def home():
    return jsonify({"status":"ok"})

@app.route('/health')
def health():
    return jsonify({"status":"ok"})

@app.route('/api/info', methods=['POST','OPTIONS'])
def get_info():
    if request.method == 'OPTIONS':
        return jsonify({"ok":True})
    try:
        url = request.json.get('url')
        if not url:
            return jsonify({"error":"URL manquante"}), 400
        ydl_opts = {
            'quiet': True,
            'noplaylist': True,
            'skip_download': True,
            'extractor_args': {'youtube': {'player_client': ['android','web']}}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "title": info.get('title','video'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration',0)
            })
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 400

@app.route('/api/download')
def download_proxy():
    try:
        url = request.args.get('url')
        quality = request.args.get('quality','720')
        if not url:
            return jsonify({"error":"URL manquante"}), 400

        is_audio = quality == 'mp3'
        
        ydl_opts = {
            'quiet': True,
            'noplaylist': True,
            'skip_download': True,
            'extractor_args': {'youtube': {'player_client': ['android','web']}}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return jsonify({"error":"Lien non supporté"}), 400
            
            title = info.get('title','video')
            clean = re.sub(r'[\\/*?:"<>|]', '_', title)[:40] or 'video'
            filename = f"{clean}.{'mp3' if is_audio else 'mp4'}"
            
            formats = info.get('formats', [])
            direct_url = None
            
            if is_audio:
                audios = [f for f in formats if f.get('acodec')!='none' and f.get('vcodec')=='none']
                if audios:
                    direct_url = sorted(audios, key=lambda x: x.get('abr',0) or 0, reverse=True)[0].get('url')
            else:
                q = int(quality) if quality.isdigit() else 720
                cand = [f for f in formats if f.get('height') and f.get('height') <= q and f.get('ext')=='mp4']
                if not cand:
                    cand = [f for f in formats if f.get('height') and f.get('height') <= q]
                if cand:
                    direct_url = sorted(cand, key=lambda x: x.get('height',0) or 0, reverse=True)[0].get('url')
            
            if not direct_url:
                direct_url = info.get('url')
            if not direct_url and formats:
                direct_url = formats[-1].get('url')
            
            if not direct_url:
                return jsonify({"error":"Pas de lien trouvé"}), 400

            # PROXY: télécharge la vidéo côté serveur et la renvoie
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36'
            }
            r = requests.get(direct_url, stream=True, headers=headers, timeout=60)
            
            if r.status_code != 200:
                # fallback: renvoie le lien direct si proxy échoue
                return jsonify({"download_url": direct_url, "filename": filename})

            def generate():
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk

            return Response(
                stream_with_context(generate()),
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Content-Type': 'video/mp4' if not is_audio else 'audio/mpeg'
                }
            )

    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
