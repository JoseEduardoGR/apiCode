from fastapi import FastAPI, HTTPException
import os
import subprocess
import shutil
import zipfile
from tempfile import TemporaryDirectory
from fastapi.responses import FileResponse

app = FastAPI()

def instalar_paquete(paquete):
    try:
        subprocess.run(["pip", "install", paquete], check=True)
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail=f"Error al instalar {paquete}")

def verificar_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        instalar_paquete("ffmpeg")

def descargar_spotify(url: str, directorio: str):
    os.makedirs(directorio, exist_ok=True)
    comando = ["spotdl", url, "--output", os.path.join(directorio, "{title}.{ext}")]
    try:
        subprocess.run(comando, check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error al descargar: {e}")

def crear_zip(directorio: str, zip_path: str):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(directorio):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, directorio))

@app.get("/descargar/")
def descargar_canciones(url: str):
    with TemporaryDirectory() as temp_dir:
        musica_dir = os.path.join(temp_dir, "Musica_Spotify")
        zip_path = os.path.join(temp_dir, "musica.zip")
        
        descargar_spotify(url, musica_dir)
        crear_zip(musica_dir, zip_path)
        
        return FileResponse(zip_path, filename="musica.zip", media_type="application/zip")

if __name__ == "__main__":
    instalar_paquete("spotdl")
    verificar_ffmpeg()
