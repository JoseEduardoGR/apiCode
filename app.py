from flask import Flask, request, send_file, jsonify
import subprocess
import os
import threading
import zipfile
import glob

app = Flask(__name__)

# Carpeta de descargas
DOWNLOAD_FOLDER = "downloads"
ZIP_PATH = os.path.join(DOWNLOAD_FOLDER, "songs.zip")  # Ruta del archivo ZIP

# Bloqueo para permitir solo una conexión a la vez
lock = threading.Lock()

@app.route('/download', methods=['POST'])
def download_song():
    if not lock.acquire(blocking=False):
        return jsonify({"error": "Servidor ocupado, intenta más tarde"}), 429

    try:
        data = request.json
        spotify_url = data.get("url")

        if not spotify_url:
            return jsonify({"error": "No se proporcionó una URL"}), 400

        # Limpiar la carpeta de descargas antes de cada nueva descarga
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
        zip_files(files)

        # Enviar el archivo ZIP
        return send_file(ZIP_PATH, as_attachment=True, mimetype="application/zip")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        lock.release()

def clean_downloads():
    """Elimina todos los archivos de la carpeta de descargas."""
    for file in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, file)
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error al eliminar {file_path}: {e}")

def zip_files(files):
    """Crea un archivo ZIP con todos los archivos MP4 descargados."""
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            zipf.write(file, os.path.basename(file))  # Agregar al ZIP sin la ruta completa

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
