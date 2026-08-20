from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp, os, tempfile, uuid
app = Flask(__name__)
CORS(app)
@app.route('/health')
def health(): return jsonify({"status":"ok"})
@app.route('/api/info', methods=['POST'])
def info():
    url = request.get_json().get('url')
    with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
        i = ydl.extract_info(url, download=False)
        return jsonify({"title":i.get('title'), "thumbnail":i.get('thumbnail')})
@app.route('/api/download')
def dl():
    url = request.args.get('url')
    with yt_dlp.YoutubeDL({'outtmpl':'/tmp/%(title)s.%(ext)s'}) as ydl:
        info = ydl.extract_info(url, download=True)
        file = ydl.prepare_filename(info)
        return send_file(file, as_attachment=True)
app.run(host='0.0.0.0', port=5000)
