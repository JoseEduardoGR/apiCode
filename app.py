from flask import Flask, request, send_file, jsonify
import subprocess
import os
import threading
import time
import glob

app = Flask(__name__)

# Carpeta de descargas
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

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
        process = subprocess.run(command, capture_output=True, text=True)

        if process.returncode != 0:
            return jsonify({"error": process.stderr}), 500

        # Buscar el archivo descargado más reciente
        files = glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.mp4"))
        if not files:
            return jsonify({"error": "No se encontró el archivo descargado"}), 500

        latest_file = max(files, key=os.path.getctime)

        # Verificar que el archivo existe y tiene un tamaño mayor que cero
        if not os.path.exists(latest_file) or os.path.getsize(latest_file) == 0:
            return jsonify({"error": "El archivo descargado está vacío o no existe"}), 500

        # Enviar el archivo al usuario
        return send_file(latest_file, as_attachment=True, mimetype='audio/mp4')

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
