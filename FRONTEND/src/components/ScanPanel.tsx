import { useState, useRef } from "react";
import { motion } from "framer-motion";
import { Shield, Upload, Zap, X, Image, Video, AudioLines } from "lucide-react";

interface ScanPanelProps {
  onScan: (payload: { url: string; files: File[] }) => void;
  isScanning: boolean;
  backendConnected: boolean | null;
}

export default function ScanPanel({ onScan, isScanning, backendConnected }: ScanPanelProps) {

  const [url, setUrl] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  const MAX_VIDEO_SIZE = 1024 * 1024 * 1024;
  const MAX_IMAGE_SIZE = 50 * 1024 * 1024;
  const MAX_AUDIO_SIZE = 200 * 1024 * 1024;

  const handleFileSelect = (files: FileList | null) => {

    if (!files) return;

    const validFiles: File[] = [];
    const errors: string[] = [];

    Array.from(files).forEach((file) => {

      const isVideo = file.type.startsWith("video/");
      const isImage = file.type.startsWith("image/");
      const isAudio = file.type.startsWith("audio/");

      if (!isVideo && !isImage && !isAudio) {
        errors.push(`${file.name}: Invalid file type`);
        return;
      }

      if (isVideo && file.size > MAX_VIDEO_SIZE) {
        errors.push(`${file.name}: Video exceeds 1GB limit`);
        return;
      }

      if (isImage && file.size > MAX_IMAGE_SIZE) {
        errors.push(`${file.name}: Image exceeds 50MB limit`);
        return;
      }

      if (isAudio && file.size > MAX_AUDIO_SIZE) {
        errors.push(`${file.name}: Audio exceeds 200MB limit`);
        return;
      }

      validFiles.push(file);

    });

    if (errors.length > 0) {
      alert(errors.join("\n"));
    }

    setSelectedFiles((prev) => {
      const deduped = new Map<string, File>();

      [...prev, ...validFiles].forEach((file) => {
        const key = `${file.name}-${file.size}-${file.lastModified}`;
        deduped.set(key, file);
      });

      return Array.from(deduped.values());
    });
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number): string => {

    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB";
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + " MB";

    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + " GB";
  };

  const canStartScan = !isScanning && selectedFiles.length > 0 && backendConnected !== false;

  const startScan = () => {
    if (!canStartScan) return;

    onScan({
      url: url.trim(),
      files: [...selectedFiles],
    });
  };

  return (

    <motion.div
      initial={{ opacity: 0, x: -40 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.8, delay: 0.2 }}
      className="glass-panel p-8 flex flex-col gap-6 relative overflow-hidden"
    >

      {isScanning && (
        <div
          className="absolute left-0 right-0 h-px animate-scan-line z-10"
          style={{
            background: "linear-gradient(90deg, transparent, #22d3ee, transparent)",
            boxShadow: "0 0 15px #22d3ee",
          }}
        />
      )}

      <div className="flex items-center gap-3">
        <Shield className="w-6 h-6" style={{ color: "var(--dd-cyan)" }} />
        <h2 className="text-xl font-bold text-glow-cyan tracking-wide">
          Neural Scan
        </h2>
      </div>

      <div>

        <label className="font-mono-hud text-xs text-muted-foreground tracking-widest mb-2 block">
          TARGET URL
        </label>

        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://target-media-url.com"
          className="w-full px-5 py-3 rounded-2xl font-mono-hud text-sm text-glow-cyan placeholder:text-muted-foreground/40 outline-none"
        />

      </div>

      <div
        className="relative rounded-2xl flex flex-col items-center justify-center py-10 cursor-pointer transition-all"
        style={{
          border: `1px dashed ${dragOver ? "rgba(34, 211, 238, 0.55)" : "rgba(34, 211, 238, 0.2)"}`,
          background: dragOver ? "rgba(34, 211, 238, 0.08)" : "rgba(10, 10, 30, 0.35)",
          opacity: isScanning ? 0.7 : 1,
          pointerEvents: isScanning ? "none" : "auto",
        }}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          if (isScanning) return;
          setDragOver(false);
          handleFileSelect(e.dataTransfer.files);
        }}
        onClick={() => {
          if (isScanning) return;
          fileRef.current?.click();
        }}
      >

        <input
          ref={fileRef}
          type="file"
          className="hidden"
          accept="image/*,video/*,audio/*,.mp3,.mp4,.wav,.ogg,.m4a,.mpeg,.mp2,.m2a"
          multiple
          onChange={(e) => {
            handleFileSelect(e.target.files);
            e.currentTarget.value = "";
          }}
        />

        <Upload className="w-8 h-8 mb-3" />

        <span className="font-mono-hud text-xs text-muted-foreground text-center px-4">
          DROP MULTIPLE IMAGES / VIDEOS / AUDIO
        </span>

      </div>

      {selectedFiles.length > 0 && (

        <div className="space-y-2 max-h-48 overflow-y-auto">

          {selectedFiles.map((file, index) => {

            const isVideo = file.type.startsWith("video/");
            const isAudio = file.type.startsWith("audio/");

            return (

              <div key={index} className="flex items-center gap-3 p-3 rounded-xl">

                {isVideo
                  ? <Video className="w-5 h-5" />
                  : isAudio
                    ? <AudioLines className="w-5 h-5" />
                    : <Image className="w-5 h-5" />}

                <div className="flex-1 min-w-0">
                  <div className="text-xs truncate">{file.name}</div>
                  <div className="text-[10px]">
                    {formatFileSize(file.size)}
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(index);
                  }}
                >
                  <X className="w-4 h-4 text-red-400" />
                </button>

              </div>

            );
          })}
        </div>
      )}

      {backendConnected === false && (
        <div
          className="rounded-xl px-4 py-3 font-mono-hud text-xs"
          style={{
            color: "#fca5a5",
            background: "rgba(239, 68, 68, 0.12)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
          }}
        >
          Backend offline. Please start FastAPI server first.
        </div>
      )}

      <button
        onClick={startScan}
        disabled={!canStartScan}
        className="btn-gradient w-full py-4 px-8 flex items-center justify-center gap-3 font-mono-hud text-sm tracking-[0.15em] disabled:opacity-50 disabled:cursor-not-allowed"
      >

        <Zap className="w-5 h-5" />

        {isScanning
          ? "SCANNING..."
          : backendConnected === false
            ? "BACKEND OFFLINE"
            : selectedFiles.length === 0
              ? "ADD FILES TO SCAN"
              : "INITIATE DEEP SCAN"}

      </button>

    </motion.div>

  );
}