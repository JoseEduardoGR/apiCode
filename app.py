from flask import Flask, request, send_file, jsonify, url_for
import subprocess
import os
import threading
import zipfile
import glob
import uuid
import time

app = Flask(__name__)

# Carpeta de descargas
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Bloqueo para permitir solo una conexión a la vez
lock = threading.Lock()

# Diccionario para rastrear descargas y limpiar archivos
downloads = {}

@app.route('/download', methods=['POST'])
def download_song():
    if not lock.acquire(blocking=False):
        return jsonify({"error": "Servidor ocupado, intenta más tarde"}), 429

    try:
        data = request.json
        spotify_url = data.get("url")

        if not spotify_url:
            return jsonify({"error": "No se proporcionó una URL"}), 400

        # Generar un identificador único para esta descarga
        download_id = str(uuid.uuid4())
        zip_path = os.path.join(DOWNLOAD_FOLDER, f"{download_id}.zip")

        # Limpiar descargas antiguas
        clean_downloads()

        # Comando para ejecutar spotdl
        command = ["spotdl", spotify_url, "--output", DOWNLOAD_FOLDER]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Esperar a que el proceso termine
        process.wait()

        # Buscar todos los archivos MP4 descargados
        files = glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.mp4"))
        if not files:
            return jsonify({"error": "No se encontraron archivos descargados"}), 500

        # Comprimir todos los archivos en un solo ZIP
        zip_files(files, zip_path)

        # Guardar la descarga en el diccionario con un tiempo de expiración
        downloads[download_id] = time.time()

        # Generar el enlace de descarga
        download_url = url_for('get_download', download_id=download_id, _external=True)
        return jsonify({"download_url": download_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        lock.release()

@app.route('/get_download/<download_id>', methods=['GET'])
def get_download(download_id):
    """Devuelve el archivo ZIP si aún está disponible."""
    zip_path = os.path.join(DOWNLOAD_FOLDER, f"{download_id}.zip")
    
    if os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True, mimetype="application/zip")
    else:
        return jsonify({"error": "El archivo ya no está disponible"}), 404

def clean_downloads():
    """Elimina archivos ZIP que hayan superado un tiempo de vida."""
    expiration_time = 600  # 10 minutos
    current_time = time.time()
    
    for download_id, timestamp in list(downloads.items()):
        zip_path = os.path.join(DOWNLOAD_FOLDER, f"{download_id}.zip")
        if current_time - timestamp > expiration_time:
            if os.path.exists(zip_path):
                os.remove(zip_path)
            del downloads[download_id]

def zip_files(files, zip_path):
    """Crea un archivo ZIP con los archivos descargados."""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            zipf.write(file, os.path.basename(file))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
