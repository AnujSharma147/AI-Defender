FROM python:3.10-slim

WORKDIR /app

# System libraries jo OpenCV, librosa, soundfile ke liye chahiye
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# PyTorch CPU-only (GPU wala bahut bada hai — free tier pe nahi chalega)
RUN pip install --no-cache-dir \
    torch==2.5.1+cpu \
    torchvision==0.20.1+cpu \
    torchaudio==2.5.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# TensorFlow CPU-only
RUN pip install --no-cache-dir tensorflow-cpu==2.15.1 keras==2.15.0

# Baaki sab requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
