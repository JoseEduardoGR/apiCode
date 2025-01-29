from flask import Flask, request, send_file, jsonify
import subprocess
import os
import threading
import time

app = Flask(__name__)

# Carpeta de descargas
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Bloqueo para permitir solo una conexión a la vez
lock = threading.Lock()

@app.route('/download', methods=['POST'])
def download_song():
    if not lock.acquire(blocking=False):  # Intentar adquirir el bloqueo sin esperar
        return jsonify({"error": "Servidor ocupado, intenta más tarde"}), 429  # 429 Too Many Requests

    try:
        data = request.json
        spotify_url = data.get("url")

        if not spotify_url:
            return jsonify({"error": "No se proporcionó una URL"}), 400

        # Comando para ejecutar spotdl
        command = ["spotdl", spotify_url, "--output", DOWNLOAD_FOLDER]
        process = subprocess.run(command, capture_output=True, text=True)

        if process.returncode != 0:
            return jsonify({"error": process.stderr}), 500

        # Buscar el archivo descargado más reciente
        files = os.listdir(DOWNLOAD_FOLDER)
        if not files:
            return jsonify({"error": "No se encontró el archivo descargado"}), 500

        latest_file = max([os.path.join(DOWNLOAD_FOLDER, f) for f in files], key=os.path.getctime)

        # Enviar el archivo al usuario
        response = send_file(latest_file, as_attachment=True)

        # Programar la limpieza de la carpeta después de un breve retraso
        threading.Thread(target=clean_downloads, daemon=True).start()

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        lock.release()  # Liberar el bloqueo

def clean_downloads():
    """Elimina todos los archivos de la carpeta de descargas después de un tiempo."""
    time.sleep(5)  # Esperar 5 segundos antes de limpiar
    for file in os.listdir(DOWNLOAD_FOLDER):
        file_path = os.path.join(DOWNLOAD_FOLDER, file)
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error al eliminar {file_path}: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
