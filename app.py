from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

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
def info():
    if request.method == 'OPTIONS':
        return jsonify({"ok":True})
    try:
        url = request.json.get('url')
        ydl_opts = {
            'quiet': True,
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
def dl():
    try:
        url = request.args.get('url')
        quality = request.args.get('quality','720')
        is_audio = quality == 'mp3'
        ydl_opts = {
            'quiet': True,
            'extractor_args': {'youtube': {'player_client': ['android','web']}}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            direct = info.get('url') or (info.get('formats',[])[-1].get('url') if info.get('formats') else None)
            if not direct:
                return jsonify({"error":"Pas de lien trouvé"}), 400
            return jsonify({
                "download_url": direct,
                "filename": (info.get('title','video')[:30] + '.mp4'),
                "title": info.get('title','')
            })
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
