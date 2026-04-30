# Deep Defend OS Backend

The backend is the detection engine behind Deep Defend OS. It accepts uploaded media, routes each file to the correct detector, and returns structured results that the frontend can render without extra translation.

## Core Responsibilities

- Accept image, audio, and video uploads.
- Dispatch each file to the correct detection pipeline.
- Warm up models before scanning when possible.
- Expose model readiness and loading progress.
- Return consistent JSON for the frontend result cards.
- Clean up temporary uploads after processing.

## API Surface

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/scan` | Scan a single uploaded file. |
| `GET` | `/model-status` | Report image, audio, and video readiness. |
| `POST` | `/warmup-models` | Preload the requested model groups. |
| `GET` | `/audio-loading-status` | Show audio ensemble loading state. |
| `GET` | `/video-loading-status` | Show video ensemble loading state. |
| `GET` | `/health` | Basic service health check. |

## Local Run

```sh
python -m uvicorn app:app --reload --port 8001
```

Run this from the `BACKEND` folder.

For Render, use this start command:

```sh
uvicorn app:app --host 0.0.0.0 --port $PORT
```

Recommended Render settings:

- Root directory: `BACKEND`
- Python version: `3.11`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`

## Model Layout

- `models/` holds the packaged detector artifacts.
- `uploads/` stores temporary files during active scans.
- `model_cache/` contains Hugging Face cache data for repeated or offline loads.

## Useful Helpers

- `python test_audio.py` - quick audio warmup and status check.
- `python test_audio_file.py` - generate a sample WAV file and run audio detection.
- `python evaluate_image_detector.py` - evaluate the image detector.

## Operational Notes

- Audio detection uses a cached ensemble path with warmup support.
- Video detection uses a notebook-aligned ensemble: ViT + EfficientNet-BiLSTM + ResNet50, with MTCNN face extraction fallback and sampled-frame inference for long clips.
- The video scanner exposes `/video-loading-status` so the frontend or Render health checks can see warmup progress.
- `/scan` returns `type: "video"`, `result`, and `deepfake_result` for video uploads.
- The backend is CORS-enabled for local development with the frontend.
- The response format is kept stable so the UI can render results directly.
