from flask import Flask, render_template, request, send_file, jsonify, send_from_directory
import os
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image
import uuid
import yt_dlp
import moviepy.editor as mp
import ffmpeg
import pysrt
import json
import subprocess
import requests
from io import BytesIO

from pdf2docx import Converter
from docx2pdf import convert as docx2pdf_convert
from pdf2image import convert_from_path
import zipfile
import base64
from bs4 import BeautifulSoup
import nltk
from gtts import gTTS
from rembg import remove


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"


# =========================
# Home Route
# =========================
@app.route("/")
def home():
    return render_template("index.html")


@app.route('/robots.txt')
def robots():
    return send_from_directory('.', 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml')


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy-policy.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    success = False
    if request.method == "POST":
        success = True
    return render_template("contact.html", success=success)


# =========================
# YouTube Thumbnail Tool
# =========================
@app.route("/youtube-thumbnail", methods=["GET", "POST"])
def youtube_thumbnail():
    video_id = None
    error_message = None
    if request.method == "POST":
        video_url = request.form.get("video_url", "").strip()
        if video_url:
            if "youtu.be/" in video_url:
                video_id = video_url.split("youtu.be/")[1].split("?")[0].split("&")[0]
            elif "youtube.com" in video_url:
                if "v=" in video_url:
                    video_id = video_url.split("v=")[1].split("&")[0]
            if not video_id:
                error_message = "Invalid YouTube URL. Please paste a valid YouTube video link."
    return render_template("youtube-thumbnail.html", video_id=video_id, error_message=error_message)


# =========================
# YouTube Thumbnail Download
# =========================
@app.route("/download-thumbnail/<video_id>")
def download_thumbnail(video_id):
    try:
        qualities = ["maxresdefault", "sddefault", "hqdefault", "mqdefault", "default"]
        for quality in qualities:
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
            response = requests.get(thumbnail_url, timeout=5)
            if response.status_code == 200:
                img_bytes = BytesIO(response.content)
                img_bytes.seek(0)
                return send_file(
                    img_bytes,
                    mimetype="image/jpeg",
                    as_attachment=True,
                    download_name=f"youtube_thumbnail_{video_id}.jpg"
                )
        return "Thumbnail not found", 404
    except Exception as e:
        return f"Error downloading thumbnail: {str(e)}", 500


# =========================
# PDF Merger Tool
# =========================
@app.route("/pdf-merger", methods=["GET", "POST"])
def pdf_merger():
    if request.method == "POST":
        files = request.files.getlist("pdf_files")
        merger = PdfMerger()
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
        for file in files:
            filepath = os.path.join("uploads", file.filename)
            file.save(filepath)
            merger.append(filepath)
        output_path = os.path.join("uploads", "merged.pdf")
        merger.write(output_path)
        merger.close()
        return send_file(output_path, as_attachment=True)
    return render_template("pdf-merger.html")


# =========================
# Image to WebP Converter
# =========================
@app.route("/image-to-webp", methods=["GET", "POST"])
def image_to_webp():
    if request.method == "POST":
        file = request.files["image_file"]
        if file:
            if not os.path.exists("uploads"):
                os.makedirs("uploads")
            unique_name = str(uuid.uuid4()) + ".webp"
            input_path = os.path.join("uploads", file.filename)
            output_path = os.path.join("uploads", unique_name)
            file.save(input_path)
            img = Image.open(input_path)
            img.save(output_path, "webp", quality=80)
            return send_file(output_path, as_attachment=True)
    return render_template("image-to-webp.html")


# =========================
# Instagram Reel Downloader
# =========================
@app.route("/instagram-reel-downloader", methods=["GET", "POST"])
def instagram_reel_downloader():
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            try:
                if not os.path.exists("uploads"):
                    os.makedirs("uploads")
                ydl_opts = {
                    'outtmpl': 'uploads/%(title)s.%(ext)s',
                    'format': 'best',
                    'quiet': True,
                    'cookiefile': 'cookies.txt'
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    return send_file(filename, as_attachment=True)
            except Exception as e:
                return f"Error: {str(e)}"
    return render_template("instagram-reel-downloader.html")


# =========================
# Video to MP3 Converter
# =========================
@app.route("/video-to-mp3", methods=["GET", "POST"])
def video_to_mp3():
    if request.method == "POST":
        file = request.files["video_file"]
        if file:
            if not os.path.exists("uploads"):
                os.makedirs("uploads")
            input_path = os.path.join("uploads", file.filename)
            output_path = os.path.join("uploads", file.filename.rsplit('.', 1)[0] + '.mp3')
            file.save(input_path)
            video = mp.VideoFileClip(input_path)
            video.audio.write_audiofile(output_path)
            return send_file(output_path, as_attachment=True)
    return render_template("video-to-mp3.html")


# =========================
# Video Metadata Viewer
# =========================
@app.route("/video-metadata", methods=["GET", "POST"])
def video_metadata():
    metadata = None
    if request.method == "POST":
        file = request.files["video_file"]
        if file:
            if not os.path.exists("uploads"):
                os.makedirs("uploads")
            input_path = os.path.join("uploads", file.filename)
            file.save(input_path)
            try:
                probe = ffmpeg.probe(input_path)
                video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
                audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
                format_info = probe['format']
                metadata = {
                    'filename': file.filename,
                    'duration': format_info.get('duration'),
                    'size': format_info.get('size'),
                    'bitrate': format_info.get('bit_rate'),
                    'video_codec': video_stream.get('codec_name') if video_stream else None,
                    'audio_codec': audio_stream.get('codec_name') if audio_stream else None,
                    'width': video_stream.get('width') if video_stream else None,
                    'height': video_stream.get('height') if video_stream else None,
                }
            except Exception as e:
                metadata = f"Unable to extract metadata: {str(e)}"
    return render_template("video-metadata.html", metadata=metadata)


# =========================
# Subtitle Extractor
# =========================
@app.route("/subtitle-extractor", methods=["GET", "POST"])
def subtitle_extractor():
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            try:
                ydl_opts = {
                    'writesubtitles': True,
                    'subtitleslangs': ['en'],
                    'skip_download': True,
                    'outtmpl': 'uploads/%(title)s.%(ext)s',
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info['title']
                    for file in os.listdir('uploads'):
                        if title in file and (file.endswith('.en.vtt') or file.endswith('.en.srt')):
                            return send_file(os.path.join('uploads', file), as_attachment=True)
                    return "No subtitles found or available"
            except Exception as e:
                return f"Error: {str(e)}"
    return render_template("subtitle-extractor.html")


# =========================
# Video Compressor
# =========================
@app.route("/video-compressor", methods=["GET", "POST"])
def video_compressor():
    if request.method == "POST":
        file = request.files["video_file"]
        quality = request.form.get("quality", "medium")
        if file:
            if not os.path.exists("uploads"):
                os.makedirs("uploads")
            input_path = os.path.join("uploads", file.filename)
            output_path = os.path.join("uploads", "compressed_" + file.filename)
            file.save(input_path)
            if quality == "low":
                bitrate = "500k"
            elif quality == "medium":
                bitrate = "1000k"
            else:
                bitrate = "2000k"
            ffmpeg.input(input_path).output(output_path, video_bitrate=bitrate).run()
            return send_file(output_path, as_attachment=True)
    return render_template("video-compressor.html")


# =========================
# TikTok Downloader
# =========================
@app.route("/tiktok-downloader", methods=["GET", "POST"])
def tiktok_downloader():
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            try:
                ydl_opts = {
                    'outtmpl': 'uploads/%(title)s.%(ext)s',
                    'format': 'best',
                    'quiet': True,
                    'cookiefile': 'cookies.txt'
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    return send_file(filename, as_attachment=True)
            except Exception as e:
                return f"Error: {str(e)}"
    return render_template("tiktok-downloader.html")


# =========================
# YouTube Video Downloader
# =========================
@app.route("/youtube-downloader", methods=["GET", "POST"])
def youtube_downloader():
    error = None
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        quality = request.form.get("quality", "720p")

        if url:
            try:
                if not os.path.exists("uploads"):
                    os.makedirs("uploads")

                cookiefile_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), 'cookies.txt'
                )
                cookie_file = cookiefile_path if os.path.exists(cookiefile_path) else None

                height_map = {
                    '1080p': 1080,
                    '720p': 720,
                    '480p': 480,
                    '320p': 360,
                }

                common_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'cookiefile': cookie_file,
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept-Language': 'en-US,en;q=0.9',
                    },
                }

                # Step 1: Pehle available formats fetch karo
                with yt_dlp.YoutubeDL(common_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                formats = info.get('formats', [])

                if quality == 'audio_only':
                    # Best audio format dhundho
                    audio_formats = [
                        f for f in formats
                        if f.get('vcodec') == 'none'
                        and f.get('acodec') not in ('none', None)
                    ]
                    if audio_formats:
                        best_audio = max(
                            audio_formats,
                            key=lambda x: x.get('abr') or 0
                        )
                        format_id = best_audio['format_id']
                    else:
                        format_id = formats[-1]['format_id'] if formats else 'best'
                else:
                    target_height = height_map.get(quality, 720)

                    # Sirf PROGRESSIVE formats — video aur audio already combined
                    # ffmpeg ki bilkul zaroorat nahi!
                    progressive = [
                        f for f in formats
                        if f.get('vcodec') not in ('none', None)
                        and f.get('acodec') not in ('none', None)
                        and f.get('height') is not None
                    ]

                    # Target height ke andar wale formats
                    suitable = [
                        f for f in progressive
                        if (f.get('height') or 0) <= target_height
                    ]

                    if suitable:
                        # Sabse achi quality select karo
                        best = max(
                            suitable,
                            key=lambda x: (x.get('height') or 0, x.get('tbr') or 0)
                        )
                        format_id = best['format_id']
                    elif progressive:
                        # Target height nahi mili to jo bhi available hai
                        best = max(
                            progressive,
                            key=lambda x: (x.get('height') or 0, x.get('tbr') or 0)
                        )
                        format_id = best['format_id']
                    else:
                        # Last resort — koi bhi combined format
                        combined = [
                            f for f in formats
                            if f.get('acodec') not in ('none', None)
                            and f.get('vcodec') not in ('none', None)
                        ]
                        if combined:
                            format_id = combined[-1]['format_id']
                        else:
                            format_id = formats[-1]['format_id'] if formats else 'best'

                # Step 2: Exact format_id se download karo
                ydl_opts = {
                    **common_opts,
                    'outtmpl': 'uploads/%(title)s.%(ext)s',
                    'format': format_id,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    dl_info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(dl_info)

                    if os.path.exists(filename):
                        return send_file(filename, as_attachment=True)
                    else:
                        upload_files = [
                            os.path.join('uploads', f)
                            for f in os.listdir('uploads')
                            if os.path.isfile(os.path.join('uploads', f))
                        ]
                        if upload_files:
                            latest = max(upload_files, key=os.path.getmtime)
                            return send_file(latest, as_attachment=True)
                        error = "File nahi mili, dobara try karo."

            except Exception as e:
                error = str(e)

    return render_template("youtube-downloader.html", error=error)

# =========================
# PDF to Word Converter
# =========================
@app.route("/pdf-to-word", methods=["GET", "POST"])
def pdf_to_word():
    if request.method == "POST":
        file = request.files.get("pdf_file")
        if file:
            if not os.path.exists("uploads"):
                os.makedirs("uploads")
            input_path = os.path.join("uploads", file.filename)
            output_path = os.path.join("uploads", file.filename.rsplit('.', 1)[0] + ".docx")
            file.save(input_path)
            try:
                cv = Converter(input_path)
                cv.convert(output_path)
                cv.close()
                return send_file(output_path, as_attachment=True)
            except Exception as e:
                return f"Error converting PDF to Word: {e}"
    return render_template("pdf-to-word.html")


# =========================
# Word to PDF Converter
# =========================
@app.route("/word-to-pdf", methods=["GET", "POST"])
def word_to_pdf():
    if request.method == "POST":
        file = request.files.get("word_file")
        if file:
            if not os.path.exists("uploads"):
                os.makedirs("uploads")
            input_path = os.path.join("uploads", file.filename)
            output_path = os.path.join("uploads", file.filename.rsplit('.', 1)[0] + ".pdf")
            file.save(input_path)
            try:
                docx2pdf_convert(input_path, output_path)
                return send_file(output_path, as_attachment=True)
            except Exception as e:
                return f"Error converting Word to PDF: {e}"
    return render_template("word-to-pdf.html")


# =========================
# PDF to Image Converter
# =========================
@app.route("/pdf-to-image", methods=["GET", "POST"])
def pdf_to_image():
    if request.method == "POST":
        file = request.files.get("pdf_file")
        if file:
            if not os.path.exists("uploads"):
                os.makedirs("uploads")
            input_path = os.path.join("uploads", file.filename)
            zip_path = os.path.join("uploads", file.filename.rsplit('.', 1)[0] + "_images.zip")
            file.save(input_path)
            try:
                pages = convert_from_path(input_path)
                with zipfile.ZipFile(zip_path, 'w') as zf:
                    for i, page in enumerate(pages, start=1):
                        img_name = f"page_{i}.png"
                        img_path = os.path.join("uploads", img_name)
                        page.save(img_path, "PNG")
                        zf.write(img_path, arcname=img_name)
                        os.remove(img_path)
                return send_file(zip_path, as_attachment=True)
            except Exception as e:
                return f"Error converting PDF to images: {e}"
    return render_template("pdf-to-image.html")


# =========================
# PDF Protect Tool
# =========================
@app.route("/pdf-protect", methods=["GET", "POST"])
def pdf_protect():
    if request.method == "POST":
        file = request.files.get("pdf_file")
        password = request.form.get("password")
        if file and password:
            if not os.path.exists("uploads"):
                os.makedirs("uploads")
            input_path = os.path.join("uploads", file.filename)
            output_path = os.path.join("uploads", file.filename.rsplit('.', 1)[0] + "_protected.pdf")
            file.save(input_path)
            try:
                reader = PdfReader(input_path)
                writer = PdfWriter()
                for page in reader.pages:
                    writer.add_page(page)
                writer.encrypt(password)
                with open(output_path, "wb") as f:
                    writer.write(f)
                return send_file(output_path, as_attachment=True)
            except Exception as e:
                return f"Error protecting PDF: {e}"
    return render_template("pdf-protect.html")


# =========================
# PDF Unlock Tool
# =========================
@app.route("/pdf-unlock", methods=["GET", "POST"])
def pdf_unlock():
    if request.method == "POST":
        file = request.files.get("pdf_file")
        password = request.form.get("password")
        if file and password:
            if not os.path.exists("uploads"):
                os.makedirs("uploads")
            input_path = os.path.join("uploads", file.filename)
            output_path = os.path.join("uploads", file.filename.rsplit('.', 1)[0] + "_unlocked.pdf")
            file.save(input_path)
            try:
                reader = PdfReader(input_path)
                if reader.is_encrypted:
                    reader.decrypt(password)
                writer = PdfWriter()
                for page in reader.pages:
                    writer.add_page(page)
                with open(output_path, "wb") as f:
                    writer.write(f)
                return send_file(output_path, as_attachment=True)
            except Exception as e:
                return f"Error unlocking PDF: {e}"
    return render_template("pdf-unlock.html")


# =========================
# PDF to HTML Converter
# =========================
@app.route("/pdf-to-html", methods=["GET", "POST"])
def pdf_to_html():
    if request.method == "POST":
        file = request.files.get("pdf_file")
        if file:
            if not os.path.exists("uploads"):
                os.makedirs("uploads")
            input_path = os.path.join("uploads", file.filename)
            html_filename = file.filename.rsplit('.', 1)[0] + ".html"
            html_path = os.path.join("uploads", html_filename)
            file.save(input_path)
            try:
                pages = convert_from_path(input_path)
                html_content = "<html><body>"
                for page in pages:
                    buffered = BytesIO()
                    page.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    html_content += f"<img src='data:image/png;base64,{img_str}'/><br/>"
                html_content += "</body></html>"
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                return send_file(html_path, as_attachment=True)
            except Exception as e:
                return f"Error converting PDF to HTML: {e}"
    return render_template("pdf-to-html.html")


# =========================
# Image Background Remover
# =========================
@app.route("/remove-bg", methods=["GET", "POST"])
def remove_bg():
    if request.method == "POST":
        file = request.files.get("image_file")
        if file:
            if not os.path.exists("uploads"):
                os.makedirs("uploads")
            input_path = os.path.join("uploads", file.filename)
            output_path = os.path.join("uploads", "no_bg_" + file.filename)
            file.save(input_path)
            try:
                with Image.open(input_path) as img:
                    result = remove(img)
                    result.save(output_path)
                return send_file(output_path, as_attachment=True)
            except Exception as e:
                return f"Error removing background: {e}"
    return render_template("remove-bg.html")


# =========================
# GIF to Video Converter
# =========================
@app.route("/gif-to-video", methods=["GET", "POST"])
def gif_to_video():
    if request.method == "POST":
        file = request.files.get("gif_file")
        if file:
            if not os.path.exists("uploads"):
                os.makedirs("uploads")
            input_path = os.path.join("uploads", file.filename)
            output_path = os.path.join("uploads", file.filename.rsplit('.', 1)[0] + ".mp4")
            file.save(input_path)
            try:
                clip = mp.VideoFileClip(input_path)
                clip.write_videofile(output_path)
                return send_file(output_path, as_attachment=True)
            except Exception as e:
                return f"Error converting GIF to video: {e}"
    return render_template("gif-to-video.html")


# =========================
# Website Media Downloader
# =========================
@app.route("/site-downloader", methods=["GET", "POST"])
def site_downloader():
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            try:
                if not os.path.exists("uploads"):
                    os.makedirs("uploads")
                response = requests.get(url)
                soup = BeautifulSoup(response.text, "html.parser")
                files = []
                for tag in soup.find_all(["img", "video"]):
                    src = tag.get("src") or tag.get("data-src")
                    if src:
                        if src.startswith("//"):
                            src = "https:" + src
                        elif src.startswith("/"):
                            from urllib.parse import urljoin
                            src = urljoin(url, src)
                        fname = os.path.basename(src.split("?")[0])
                        r = requests.get(src)
                        path = os.path.join("uploads", fname)
                        with open(path, "wb") as f:
                            f.write(r.content)
                        files.append(path)
                if not files:
                    return "No media found on page"
                zip_path = os.path.join("uploads", "site_media.zip")
                with zipfile.ZipFile(zip_path, 'w') as zf:
                    for fpath in files:
                        zf.write(fpath, os.path.basename(fpath))
                return send_file(zip_path, as_attachment=True)
            except Exception as e:
                return f"Error downloading site media: {e}"
    return render_template("site-downloader.html")


# =========================
# Facebook Video Downloader
# =========================
@app.route("/facebook-downloader", methods=["GET", "POST"])
def facebook_downloader():
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            try:
                ydl_opts = {
                    'outtmpl': 'uploads/%(title)s.%(ext)s',
                    'format': 'best',
                    'cookiefile': 'cookies.txt',
                    'quiet': True,
                    'no_warnings': True,
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    },
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    return send_file(filename, as_attachment=True)
            except Exception as e:
                return f"Error: {e}"
    return render_template("facebook-downloader.html")


# =========================
# Twitter / X Downloader
# =========================
@app.route("/twitter-downloader", methods=["GET", "POST"])
def twitter_downloader():
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            try:
                ydl_opts = {'outtmpl': 'uploads/%(title)s.%(ext)s', 'format': 'best'}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    return send_file(filename, as_attachment=True)
            except Exception as e:
                return f"Error: {e}"
    return render_template("twitter-downloader.html")


# =========================
# Text to Speech Tool
# =========================
@app.route("/text-to-speech", methods=["GET", "POST"])
def text_to_speech():
    if request.method == "POST":
        text = request.form.get("text")
        if text:
            try:
                tts = gTTS(text)
                output_path = os.path.join("uploads", "speech.mp3")
                tts.save(output_path)
                return send_file(output_path, as_attachment=True)
            except Exception as e:
                return f"Error generating speech: {e}"
    return render_template("text-to-speech.html")


# =========================
# Hashtag Generator Tool
# =========================
@app.route("/hashtag-generator", methods=["GET", "POST"])
def hashtag_generator():
    hashtags = []
    if request.method == "POST":
        text = request.form.get("text", "")
        if text:
            try:
                nltk.download('stopwords')
                from nltk.corpus import stopwords
                words = [w.strip('.,!?"\'') for w in text.split()]
                filtered = [w for w in words if w.lower() not in stopwords.words('english') and len(w) > 2]
                unique = []
                for w in filtered:
                    lw = w.lower()
                    if lw not in unique:
                        unique.append(lw)
                hashtags = ["#" + w for w in unique[:10]]
            except Exception as e:
                hashtags = [f"Error generating hashtags: {e}"]
    return render_template("hashtag-generator.html", hashtags=hashtags)


# =========================
# Run App
# =========================
if __name__ == "__main__":
    app.run(debug=True)
