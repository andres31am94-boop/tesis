@echo off
REM Fase 7.3: YOLO (epoca 1) + NMS + ByteTrack sobre el video de prueba.
cd /d "%~dp0"
.venv\Scripts\python.exe -u scripts\probar_tracking_video.py --pesos results\vision\entrenamiento\hotwheels_v1_epoca1\weights\best.pt --video data\raw\hotwheels\video_IMG_0566.mov > results\vision\tracking_epoca1_log.txt 2>&1
