import os
import platform
from flask import Flask, render_template, request, jsonify, send_file
from yt_dlp import YoutubeDL

app = Flask(__name__)

# Detectar si estamos en Termux
def is_termux():
    return 'com.termux' in os.environ.get('PREFIX', '')

# Configuración adaptativa para FFmpeg
def get_ffmpeg_location():
    if is_termux():
        return '/data/data/com.termux/files/usr/bin/'
    elif platform.system() == 'Windows':
        return './ffmpeg/bin/'
    else:
        return '/usr/bin/'  # Linux/macOS

# Crear directorio de descargas si no existe
os.makedirs('downloads', exist_ok=True)

YDL_OPTS_SEARCH = {'quiet': True, 'skip_download': True}

# Configuración FLAC optimizada
YDL_OPTS_DOWNLOAD = {
    'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'ffmpeg_location': get_ffmpeg_location(),
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'flac',
        'preferredquality': '0',
    }],
    # Optimizaciones para Termux
    'socket_timeout': 30,
    'retries': 3,
}

# Configuración MP3 optimizada
YDL_OPTS_DOWNLOAD_MP3 = {
    'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'ffmpeg_location': get_ffmpeg_location(),
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',
    }],
    # Optimizaciones para Termux
    'socket_timeout': 30,
    'retries': 3,
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    query = request.args.get('query', '')
    max_results = 4
    results = []

    try:
        with YoutubeDL({'quiet': True, 'skip_download': True, 'format': 'bestaudio', 'socket_timeout': 30}) as ydl:
            info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            entries = info.get('entries', [])
            for e in entries:
                results.append({
                    'id': e['id'],
                    'title': e['title'],
                    'duration': e.get('duration'),
                    'thumbnail': e.get('thumbnail'),
                    'audio_url': e['url']
                })
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return jsonify({'error': 'Error en la búsqueda'})

    return jsonify(results)

@app.route('/download/<video_id>')
def download(video_id):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        with YoutubeDL(YDL_OPTS_DOWNLOAD) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.flac'
        return send_file(filename, as_attachment=True)
    except Exception as e:
        print(f"Error en descarga FLAC: {e}")
        return f"Error: {e}", 500

@app.route('/download-mp3/<video_id>')
def download_mp3(video_id):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        with YoutubeDL(YDL_OPTS_DOWNLOAD_MP3) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
        return send_file(filename, as_attachment=True)
    except Exception as e:
        print(f"Error en descarga MP3: {e}")
        return f"Error: {e}", 500

@app.route('/status')
def status():
    """Endpoint para verificar el estado del sistema"""
    return jsonify({
        'platform': platform.system(),
        'termux': is_termux(),
        'ffmpeg_location': get_ffmpeg_location(),
        'downloads_dir': os.path.exists('downloads')
    })

if __name__ == '__main__':
    # Configuración optimizada para Termux
    host = '0.0.0.0' if is_termux() else '127.0.0.1'
    print(f"🚀 Iniciando MusicFinder en {'Termux' if is_termux() else 'PC'}")
    print(f"📱 Acceso: http://{host}:5000")
    app.run(host=host, port=5000, debug=True)