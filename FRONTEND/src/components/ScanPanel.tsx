import { useState, useRef } from "react";
import { motion } from "framer-motion";

import { Shield, Upload, Zap, X, Image, Video } from "lucide-react";

interface ScanPanelProps {
  onScan: (url: string) => void;
  isScanning: boolean;
}

export default function ScanPanel({ onScan, isScanning }: ScanPanelProps) {
 
  const [url, setUrl] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);


  const MAX_VIDEO_SIZE = 1024 * 1024 * 1024; // 1GB
  const MAX_IMAGE_SIZE = 50 * 1024 * 1024; // 50MB

  const handleFileSelect = (files: FileList | null) => {

    if (!files) return;

    const validFiles: File[] = [];
    const errors: string[] = [];

    Array.from(files).forEach((file) => {

      const isVideo = file.type.startsWith("video/");
      const isImage = file.type.startsWith("image/");

      if (!isVideo && !isImage) {

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


      validFiles.push(file);

    });

    if (errors.length > 0) {
      alert(errors.join("\n"));
    }


    setSelectedFiles((prev) => [...prev, ...validFiles]);

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

  return (

    <motion.div
      initial={{ opacity: 0, x: -40 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.8, delay: 0.2 }}
      className="glass-panel p-8 flex flex-col gap-6 relative overflow-hidden"
    >



      {/* Scan line */}

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

        <h2 className="text-xl font-bold text-glow-cyan tracking-wide">Neural Scan</h2>
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

          className="w-full px-5 py-3 rounded-2xl font-mono-hud text-sm text-glow-cyan placeholder:text-muted-foreground/40 outline-none focus:ring-1 focus:ring-primary/40 transition-all"
          style={{
            background: "rgba(10, 10, 30, 0.8)",
            border: "1px solid rgba(34, 211, 238, 0.15)",
          }}
        />
      </div>

      {/* Drag & drop zone */}
      <div
        className="relative rounded-2xl flex flex-col items-center justify-center py-10 cursor-pointer transition-all"
        style={{
          background: dragOver ? "rgba(34, 211, 238, 0.05)" : "rgba(10, 10, 30, 0.4)",
          border: `2px dashed ${dragOver ? "rgba(34, 211, 238, 0.5)" : "rgba(34, 211, 238, 0.1)"}`,

        }}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();

          setDragOver(false);
          handleFileSelect(e.dataTransfer.files);
        }}
        onClick={() => fileRef.current?.click()}
      >

        <input
          ref={fileRef}
          type="file"
          className="hidden"

          accept="image/*,video/*"
          multiple
          onChange={(e) => handleFileSelect(e.target.files)}
        />
        <Upload className="w-8 h-8 mb-3" style={{ color: "rgba(34, 211, 238, 0.4)" }} />
        <span className="font-mono-hud text-xs text-muted-foreground text-center px-4">
          DROP MULTIPLE IMAGES/VIDEOS OR CLICK TO UPLOAD
        </span>
        <span className="font-mono-hud text-[10px] text-muted-foreground/60 mt-2">
          Images: up to 50MB | Videos: up to 1GB
        </span>
      </div>

      {/* Selected Files Display */}
      {selectedFiles.length > 0 && (
        <div className="space-y-2 max-h-48 overflow-y-auto">
          <label className="font-mono-hud text-xs text-muted-foreground tracking-widest">
            SELECTED FILES ({selectedFiles.length})
          </label>
          {selectedFiles.map((file, index) => {
            const isVideo = file.type.startsWith("video/");
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="flex items-center gap-3 p-3 rounded-xl"
                style={{
                  background: "rgba(10, 10, 30, 0.6)",
                  border: "1px solid rgba(34, 211, 238, 0.15)",
                }}
              >
                {isVideo ? (
                  <Video className="w-5 h-5 flex-shrink-0" style={{ color: "var(--dd-magenta)" }} />
                ) : (
                  <Image className="w-5 h-5 flex-shrink-0" style={{ color: "var(--dd-cyan)" }} />
                )}
                <div className="flex-1 min-w-0">
                  <div className="font-mono-hud text-xs text-glow-cyan truncate">{file.name}</div>
                  <div className="font-mono-hud text-[10px] text-muted-foreground">
                    {formatFileSize(file.size)} • {isVideo ? "Video" : "Image"}
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(index);
                  }}

                  className="p-1 rounded-lg hover:bg-red-500/20 transition-colors"
                >
                  <X className="w-4 h-4 text-red-400" />
                </button>
              </motion.div>

            );
          })}
        </div>
      )}


      <button
        onClick={() => onScan(url)}
        disabled={isScanning || (!url.trim() && selectedFiles.length === 0)}
        className="btn-gradient py-4 px-8 text-sm font-bold tracking-[0.2em] uppercase flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Zap className="w-5 h-5" />
        {isScanning ? "SCANNING..." : "INITIATE DEEP SCAN"}
      </button>
    </motion.div>
  );
}

