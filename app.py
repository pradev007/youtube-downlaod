from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp
import os
import threading

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

progress_data = {
    "status": "idle",
    "percent": 0,
    "completed": False
}


def progress_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)
        if total:
            progress_data["percent"] = int(downloaded / total * 100)
            progress_data["status"] = "downloading"
            progress_data["completed"] = False

    elif d['status'] == 'finished':
        progress_data["percent"] = 100
        progress_data["status"] = "finished"
        progress_data["completed"] = True

# added

def download_audio(url):
    progress_data["percent"] = 0
    progress_data["status"] = "starting"
    progress_data["completed"] = False


    ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
    'progress_hooks': [progress_hook],
    'noplaylist': True,  # <- THIS PREVENTS PLAYLIST DOWNLOADS
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}


    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    url = request.json.get("url")
    if not url:
        return jsonify({"error": "URL required"}), 400

    thread = threading.Thread(target=download_audio, args=(url,))
    thread.start()

    return jsonify({"message": "Download started"})


@app.route("/progress")
def progress():
    return jsonify(progress_data)


@app.route("/files/<filename>")
def files(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
