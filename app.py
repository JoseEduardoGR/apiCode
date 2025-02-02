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
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Esperar a que el archivo comience a descargarse
        latest_file = None
        timeout = 30  # Tiempo máximo de espera en segundos

        start_time = time.time()
        while time.time() - start_time < timeout:
            files = glob.glob(os.path.join(DOWNLOAD_FOLDER, "*.mp4"))
            if files:
                latest_file = max(files, key=os.path.getctime)
                if os.path.exists(latest_file) and os.path.getsize(latest_file) > 1024:  # Al menos 1 KB
                    break
            time.sleep(1)

        if not latest_file or not os.path.exists(latest_file):
            return jsonify({"error": "No se encontró el archivo descargado"}), 500

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
