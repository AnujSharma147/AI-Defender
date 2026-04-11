import { motion } from "framer-motion";
import { Activity, Cpu, Download } from "lucide-react";
import { useEffect, useState } from "react";

interface StatusPanelProps {
  progress: number;
  isScanning: boolean;
  backendConnected: boolean | null;
  modelStageText: string;
  engineStageText: string;
  activeMediaLabel: string;
}

interface AudioLoadingStatus {
  loading: boolean;
  loaded: boolean;
  stage: string;
  model1: boolean;
  model2: boolean;
  model3: boolean;
  error: string | null;
}

export default function StatusPanel({
  progress,
  isScanning,
  backendConnected,
  modelStageText,
  engineStageText,
  activeMediaLabel,
}: StatusPanelProps) {
  const [audioLoadingStatus, setAudioLoadingStatus] = useState<AudioLoadingStatus | null>(null);

  // Poll audio loading status when scanning
  useEffect(() => {
    if (!isScanning) {
      setAudioLoadingStatus(null);
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch("http://127.0.0.1:8001/audio-loading-status");
        if (res.ok) {
          const data = await res.json();
          setAudioLoadingStatus(data);
        }
      } catch (e) {
        // Silently fail if endpoint not available
      }
    }, 500);

    return () => clearInterval(pollInterval);
  }, [isScanning]);

  const backendLabel =
    backendConnected === null
      ? "Checking"
      : backendConnected
        ? "Connected"
        : "Offline";

  const getStageLabel = (stage: string) => {
    const labels: { [key: string]: string } = {
      idle: "Ready",
      initializing: "Initializing...",
      loading_model1: "Loading Model 1 (Wav2Vec2)...",
      loading_model2: "Loading Model 2 (Fallback)...",
      loading_model3: "Loading Model 3 (WavLM)...",
      complete: "✓ All Models Ready",
      failed: "⚠ Loading Failed",
    };
    return labels[stage] || stage;
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 40 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.8, delay: 0.4 }}
      className="glass-panel p-8 flex flex-col gap-6"
    >
      <div className="flex items-center gap-3">
        <Cpu className="w-6 h-6" style={{ color: "var(--dd-cyan)" }} />
        <h2 className="text-xl font-bold text-glow-cyan tracking-wide">System Status</h2>
      </div>

      {/* Engine Load */}
      <div>
        <div className="flex justify-between mb-2">
          <span className="font-mono-hud text-xs text-muted-foreground tracking-widest">ENGINE LOAD</span>
          <span className="font-mono-hud text-xs text-glow-cyan">{progress}%</span>
        </div>
        <div className="h-2 rounded-full overflow-hidden" style={{ background: "rgba(34, 211, 238, 0.1)" }}>
          <motion.div
            className="h-full rounded-full"
            style={{ background: "var(--dd-gradient)" }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
      </div>

      {/* Status cards */}
      <div className="space-y-3">
        {[
          { label: "Model Load", value: modelStageText, active: isScanning },
          { label: "Engine Load", value: engineStageText, active: isScanning },
          { label: "Media Queue", value: activeMediaLabel, active: isScanning },
          { label: "Backend", value: backendLabel, active: backendConnected !== false },
        ].map((item) => (
          <div
            key={item.label}
            className="flex items-center justify-between px-5 py-3 rounded-2xl"
            style={{
              background: "rgba(10, 10, 30, 0.6)",
              border: "1px solid rgba(34, 211, 238, 0.08)",
            }}
          >
            <span className="font-mono-hud text-xs text-muted-foreground">{item.label}</span>
            <span className={`font-mono-hud text-xs ${item.active ? "text-glow-cyan" : "text-muted-foreground"}`}>
              {item.value}
            </span>
          </div>
        ))}

        {/* Audio Models Loading Status */}
        {audioLoadingStatus && audioLoadingStatus.loading && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="px-5 py-4 rounded-2xl"
            style={{
              background: "rgba(168, 85, 247, 0.1)",
              border: "1px solid rgba(168, 85, 247, 0.3)",
            }}
          >
            <div className="flex items-center gap-2 mb-3">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              >
                <Download className="w-4 h-4" style={{ color: "rgba(168, 85, 247, 1)" }} />
              </motion.div>
              <span className="font-mono-hud text-xs text-purple-300">
                {getStageLabel(audioLoadingStatus.stage)}
              </span>
            </div>

            {/* Individual Model Status */}
            <div className="space-y-2">
              {[
                { model: "Model 1", loaded: audioLoadingStatus.model1 },
                { model: "Model 2", loaded: audioLoadingStatus.model2 },
                { model: "Model 3", loaded: audioLoadingStatus.model3 },
              ].map((m) => (
                <motion.div
                  key={m.model}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5 }}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-[11px] font-mono-hud"
                  style={{
                    background: m.loaded
                      ? "rgba(34, 211, 238, 0.15)"
                      : "rgba(100, 100, 150, 0.15)",
                    border: m.loaded
                      ? "1px solid rgba(34, 211, 238, 0.3)"
                      : "1px solid rgba(100, 100, 150, 0.2)",
                  }}
                >
                  <motion.div
                    animate={m.loaded ? { scale: [1, 1.2, 1] } : { opacity: 0.5 }}
                    transition={{ duration: 0.8, repeat: Infinity }}
                  >
                    {m.loaded ? (
                      <span style={{ color: "rgba(34, 211, 238, 1)" }}>✓</span>
                    ) : (
                      <span style={{ color: "rgba(100, 100, 150, 1)" }}>◐</span>
                    )}
                  </motion.div>
                  <span style={{ color: m.loaded ? "rgba(34, 211, 238, 1)" : "rgba(100, 100, 150, 1)" }}>
                    {m.model}: {m.loaded ? "Ready" : "Loading..."}
                  </span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {audioLoadingStatus && audioLoadingStatus.loaded && !audioLoadingStatus.loading && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="px-5 py-3 rounded-2xl"
            style={{
              background: "rgba(34, 211, 238, 0.15)",
              border: "1px solid rgba(34, 211, 238, 0.3)",
            }}
          >
            <div className="flex items-center gap-2">
              <span style={{ color: "rgba(34, 211, 238, 1)" }}>✓</span>
              <span className="font-mono-hud text-xs text-cyan-300">
                Audio Models Ready (3/3)
              </span>
            </div>
          </motion.div>
        )}
      </div>

      {/* Activity indicator */}
      <div className="flex items-center gap-3 mt-auto">
        <Activity
          className="w-4 h-4"
          style={{
            color:
              backendConnected === false
                ? "#ef4444"
                : isScanning
                  ? "var(--dd-cyan)"
                  : "rgba(34,211,238,0.2)",
          }}
        />
        <span className="font-mono-hud text-xs text-muted-foreground">
          {backendConnected === false
            ? "BACKEND CONNECTION LOST"
            : isScanning
              ? "DEEP SCAN IN PROGRESS"
              : "AWAITING COMMAND"}
        </span>
      </div>
    </motion.div>
  );
}
