from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/health')
def health():
    return {"status":"ok"}

@app.route('/api/info', methods=['POST'])
def info():
    url = request.json.get('url')
    with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
        i = ydl.extract_info(url, download=False)
        return jsonify({"title": i.get('title'), "thumbnail": i.get('thumbnail')})

@app.route('/api/download')
def dl():
    url = request.args.get('url')
    quality = request.args.get('quality','720')
    with yt_dlp.YoutubeDL({}) as ydl:
        info = ydl.extract_info(url, download=False)
        return jsonify({"download_url": info['url'], "filename": "video.mp4"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
