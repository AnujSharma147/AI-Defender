import { useState, useRef } from "react";
import { motion } from "framer-motion";
import { Shield, Upload, Zap } from "lucide-react";

interface ScanPanelProps {
  onScan: (url: string) => void;
  isScanning: boolean;
}

export default function ScanPanel({ onScan, isScanning }: ScanPanelProps) {
  const [url, setUrl] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

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
        onDrop={(e) => { e.preventDefault(); setDragOver(false); }}
        onClick={() => fileRef.current?.click()}
      >
        <input ref={fileRef} type="file" className="hidden" accept="image/*,video/*" />
        <Upload className="w-8 h-8 mb-3" style={{ color: "rgba(34, 211, 238, 0.4)" }} />
        <span className="font-mono-hud text-xs text-muted-foreground">DROP MEDIA OR CLICK TO UPLOAD</span>
      </div>

      <button
        onClick={() => onScan(url)}
        disabled={isScanning}
        className="btn-gradient py-4 px-8 text-sm font-bold tracking-[0.2em] uppercase flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Zap className="w-5 h-5" />
        {isScanning ? "SCANNING..." : "INITIATE DEEP SCAN"}
      </button>
    </motion.div>
  );
}
