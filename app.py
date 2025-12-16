from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp
import os
import threading

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Global dict to track download progress and status
download_progress = {"status": "idle", "percent": 0, "message": ""}


def download_audio(url):
    ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
    'progress_hooks': [progress_hook],
    'cookiefile': 'cookies.txt'   # <--- your exported browser cookies
}


    # Reset progress
    download_progress["status"] = "downloading"
    download_progress["percent"] = 0
    download_progress["message"] = ""

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        download_progress["status"] = "completed"
        download_progress["percent"] = 100
        download_progress["message"] = "Download completed successfully!"
    except yt_dlp.utils.DownloadError as e:
        download_progress["status"] = "error"
        download_progress["percent"] = 0
        download_progress["message"] = str(e)
    except Exception as e:
        download_progress["status"] = "error"
        download_progress["percent"] = 0
        download_progress["message"] = f"Unexpected error: {str(e)}"


def progress_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)
        if total:
            download_progress["percent"] = int(downloaded / total * 100)
            download_progress["status"] = "downloading"
            download_progress["message"] = "Downloading..."


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"status": "error", "message": "No URL provided"}), 400

    # Start download in a separate thread
    threading.Thread(target=download_audio, args=(url,)).start()
    return jsonify({"status": "started", "message": "Download started"})


@app.route("/progress")
def progress():
    return jsonify(download_progress)


@app.route("/files/<filename>")
def files(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
