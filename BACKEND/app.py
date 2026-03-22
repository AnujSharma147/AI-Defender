from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid

from detect_object import detect_objects
from detect_image import detect_image
from detect_audio import detect_audio

app = FastAPI()

# ✅ CORS (React support)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ------------------ MAIN SCAN API ------------------
@app.post("/scan")
async def scan(file: UploadFile = File(...)):
    try:
        # ✅ unique filename (IMPORTANT)
        ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        path = os.path.join(UPLOAD_FOLDER, filename)

        # ✅ save file
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ---------- IMAGE ----------
        if ext.lower() in ["jpg", "jpeg", "png", "webp", "bmp"]:
            result = detect_image(path)
            detections = detect_objects(path)

            os.remove(path)  # 🔥 cleanup

            return {
                "type": "image",
                "result": result,
                "detections": detections,
            }

        # ---------- AUDIO ----------
        elif ext.lower() in ["wav", "mp3"]:
            result = detect_audio(path)

            os.remove(path)

            return {
                "type": "audio",
                "result": result
            }

        # ---------- VIDEO ----------
        elif ext.lower() in ["mp4", "avi", "mov"]:
            detections = detect_objects(path)

            os.remove(path)

            return {
                "type": "video",
                "detections": detections
            }

        else:
            os.remove(path)
            return {"error": "Unsupported file format"}

    except Exception as e:
        return {"error": str(e)}


# ------------------ HEALTH CHECK ------------------
@app.get("/health")
def health():
    return {"status": "ok"}