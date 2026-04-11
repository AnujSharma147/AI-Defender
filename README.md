# Deep Defend OS

Deep Defend OS is a multi-modal AI forensics platform built to detect manipulation across image, audio, and video inputs from a single operational interface.

It combines deepfake-oriented classifiers with object-level context extraction so investigators can move from raw media to an evidence-focused decision quickly.

## Why This Project Matters

Modern misinformation is no longer text-only. Fake media can now look and sound real enough to bypass casual verification. Deep Defend OS addresses this by providing:

- A single scan pipeline for images, audio, and video
- Model-backed prediction outputs with confidence signals
- Object-level detections that provide scene context
- A clean frontend designed for fast triage and repeated analysis

## Core Capabilities

- Image analysis
	- Deepfake score estimation using TensorFlow/Keras model pipeline
	- Optional fallback logic and calibration support in detector module
	- YOLO-assisted object detection to enrich context

- Audio analysis
	- Mel-spectrogram transformation from waveform
	- ResNet-based binary classification (real vs fake)
	- Deterministic percentage outputs for reporting

- Video analysis
	- Upload handling and object-level analysis on sampled frames
	- Separate advanced video detector module prepared for deepfake + object fusion

- Platform behavior
	- FastAPI backend with upload orchestration and cleanup
	- React + TypeScript frontend with staged scan UX
	- Backend health monitoring from the UI

## System Architecture

1. Frontend sends media file(s) for analysis.
2. Backend stores files with unique IDs to avoid collisions.
3. Media type routing triggers the corresponding detector path.
4. Detector outputs are normalized into structured JSON.
5. Temporary files are removed after processing.
6. Frontend renders confidence, verdict, and detection evidence.

## Tech Stack

- Frontend: React 18, TypeScript, Vite, Tailwind CSS, Framer Motion, shadcn/ui
- Backend: FastAPI, Python
- ML/CV: TensorFlow/Keras, PyTorch, Librosa, OpenCV, Ultralytics YOLO, Transformers

## Repository Structure

```text
.
|- BACKEND/
|  |- app.py
|  |- detect_image.py
|  |- detect_audio.py
|  |- detect_video.py
|  |- detect_object.py
|  |- models/
|  |- model_cache/
|  |- uploads/
|
|- FRONTEND/
|  |- src/
|  |  |- pages/Index.tsx
|  |  |- components/
|  |- package.json
|
|- README.md
```

## Model Training And Evaluation

This project is built as a train-and-improve workflow, not only an inference demo.

- Image pipeline includes calibration and evaluation utilities for model quality checks
- Audio pipeline uses a trained classifier checkpoint for real-vs-fake discrimination
- Detector modules are structured so future retraining can replace model artifacts without major code changes

Useful backend scripts:

- `python calibrate_image_detector.py`
- `python evaluate_image_detector.py`
- `python test_audio.py`
- `python test_audio_file.py`

## Quick Start

### 1. Clone

```bash
git clone https://github.com/<your-username>/deep-defend-os.git
cd deep-defend-os
```

### 2. Run Backend

From BACKEND directory:

```bash
python -m uvicorn app:app --reload --port 8001
```

Backend URL:

```text
http://127.0.0.1:8001
```

### 3. Run Frontend

From FRONTEND directory:

```bash
npm install
npm run dev
```

Frontend URL (default Vite):

```text
http://127.0.0.1:5173
```

## Evaluation Orientation

This project is designed for practical demonstration and academic review:

- Clear modular separation between inference layers
- Reproducible local deployment with minimal setup
- Extensible detector design for future model upgrades
- Investigator-style result visualization instead of raw probability dumps

## Engineering Highlights

- Collision-safe file handling using UUID-based upload naming
- Explicit cleanup after scan to reduce storage residue
- Model loading paths that support offline and cached operation
- Typed frontend workflows for predictable UI behavior

## Future Extensions

- Unified warmup and model-status APIs for all modalities
- Batch upload analytics with downloadable reports
- Explainability overlays and confidence calibration dashboards
- Dockerized deployment for reproducible lab demonstrations

## Team Note

Deep Defend OS is positioned as a real-world defensive AI prototype, built not only to classify media but to support trust decisions with operational clarity.

If you are reviewing this as faculty, you can assess it across three dimensions:

- Technical integration depth
- Practical usability for analysts
- Extensibility for research progression
