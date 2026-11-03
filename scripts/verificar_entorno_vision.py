"""
Fase 7, paso 7.0: comprueba el entorno para vision artificial (no instala nada).

Muestra: version de Python, si hay GPU NVIDIA (nvidia-smi), y si estan instalados PyTorch, Ultralytics (YOLO) y OpenCV,
con sus versiones y si PyTorch puede usar la GPU (CUDA).

Uso (desde la carpeta tesis):
  .\\.venv\\Scripts\\python.exe scripts\\verificar_entorno_vision.py
"""
import importlib
import platform
import shutil
import subprocess
import sys


def version_de(modulo):
    try:
        return importlib.import_module(modulo).__version__
    except ImportError:
        return None


def main():
    print(f"Sistema operativo : {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python            : {sys.version.split()[0]}  ({sys.executable})")
    print(f"Procesador        : {platform.processor()}")

    if shutil.which("nvidia-smi"):
        salida = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                                capture_output=True, text=True)
        print(f"GPU NVIDIA        : {salida.stdout.strip() or salida.stderr.strip()}")
    else:
        print("GPU NVIDIA        : no se encontro nvidia-smi (sin GPU NVIDIA o sin driver)")

    torch_version = version_de("torch")
    print(f"PyTorch           : {torch_version or 'NO instalado'}")
    if torch_version:
        import torch
        print(f"  CUDA disponible : {torch.cuda.is_available()}"
              + (f" ({torch.cuda.get_device_name(0)}, CUDA {torch.version.cuda})" if torch.cuda.is_available() else ""))
    print(f"Ultralytics (YOLO): {version_de('ultralytics') or 'NO instalado'}")
    print(f"OpenCV            : {version_de('cv2') or 'NO instalado'}")


if __name__ == "__main__":
    main()
