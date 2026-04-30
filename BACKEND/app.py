from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
import time # Time add kiya hai
import threading
from pydantic import BaseModel
from typing import List

# ✅ Importing functions properly
from detect_object import detect_objects
from detect_image import detect_image, get_image_model_status
from detect_audio import detect_audio_logic, warmup_audio_model, get_audio_model_status
from detect_video import detect_video_logic, warmup_video_models, get_video_model_status

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class WarmupRequest(BaseModel):
    media_types: List[str] = []


@app.on_event("startup")
def warmup_video_models_on_startup():
    def _warmup():
        try:
            warmup_video_models()
        except Exception as e:
            print(f"[WARNING] Video warmup failed: {e}")

    threading.Thread(target=_warmup, daemon=True).start()

# Helper function to safely delete files on Windows
def safe_remove(path):
    try:
        if path and os.path.exists(path):
            # Thoda wait karte hain taaki process file release kar de
            os.remove(path)
    except Exception as e:
        print(f"[WARNING] Could not delete temp file: {e}")

@app.post("/scan")
async def scan(file: UploadFile = File(...)):
    path = "" 
    try:
        ext = file.filename.split(".")[-1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        path = os.path.join(UPLOAD_FOLDER, filename)

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ---------- IMAGE SCAN ----------
        if ext in ["jpg", "jpeg", "png", "webp", "bmp"]:
            result = detect_image(path)
            detections = detect_objects(path)
            safe_remove(path) # Use safe_remove
            return {"type": "image", "result": result, "detections": detections}

        # ---------- AUDIO SCAN ----------
        elif ext in ["wav", "mp3", "ogg", "m4a", "mpeg", "mp2", "m2a"]:
            result = detect_audio_logic(path)
            safe_remove(path)
            return {"type": "audio", "result": result}

        # ---------- VIDEO SCAN ----------
        elif ext in ["mp4", "avi", "mov"]:
            # Video analysis runs here
            result = detect_video_logic(path)
            # Video models file release karne mein time lete hain
            # Isliye hum response ke baad delete karne ki koshish karenge
            safe_remove(path)
            return {
                "type": "video",
                "result": result,
                "deepfake_result": result,
            }

        else:
            safe_remove(path)
            return {"error": f"Unsupported format: {ext}"}

    except Exception as e:
        safe_remove(path)
        return {"error": str(e)}


@app.get("/model-status")
def model_status():
    return {
        "image": get_image_model_status(),
        "audio": get_audio_model_status(),
        "video": get_video_model_status(),
    }


@app.post("/warmup-models")
def warmup_models(payload: WarmupRequest):
    requested = {t.strip().lower() for t in payload.media_types if isinstance(t, str)}
    if not requested:
        requested = {"image", "audio", "video"}

    result = {}

    if "image" in requested:
        image_status = get_image_model_status()
        result["image"] = {"ok": bool(image_status.get("loaded")), "status": image_status}

    if "audio" in requested:
        result["audio"] = warmup_audio_model()

    if "video" in requested:
        result["video"] = warmup_video_models()

    return {
        "requested": sorted(requested),
        "models": result,
        "status": model_status(),
    }

@app.get("/audio-loading-status")
def audio_loading_status():
    """Get current audio model loading progress"""
    from detect_audio import _models, _loading_in_progress, _error, _loading_stage
    
    return {
        "loading": _loading_in_progress,
        "loaded": _models["loaded"],
        "stage": _loading_stage,
        "model1": _models["model1"] is not None,
        "model2": _models["model2"] is not None,
        "model3": _models["model3"] is not None,
        "error": _error
    }


@app.get("/video-loading-status")
def video_loading_status():
    """Get current video model loading progress"""
    return get_video_model_status()

@app.get("/health")
def health():
    return {"status": "Deep-Defend is Live"}

 
