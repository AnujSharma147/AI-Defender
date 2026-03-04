import { motion } from "framer-motion";
import { Activity, Cpu } from "lucide-react";

interface StatusPanelProps {
  progress: number;
  isScanning: boolean;
}

export default function StatusPanel({ progress, isScanning }: StatusPanelProps) {
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
          { label: "Protocol", value: isScanning ? "Active" : "Standby", active: isScanning },
          { label: "Neural Net", value: isScanning ? "Processing" : "Idle", active: isScanning },
          { label: "Threat Level", value: isScanning ? "Scanning" : "Unknown", active: isScanning },
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
      </div>

      {/* Activity indicator */}
      <div className="flex items-center gap-3 mt-auto">
        <Activity className="w-4 h-4" style={{ color: isScanning ? "var(--dd-cyan)" : "rgba(34,211,238,0.2)" }} />
        <span className="font-mono-hud text-xs text-muted-foreground">
          {isScanning ? "DEEP SCAN IN PROGRESS" : "AWAITING COMMAND"}
        </span>
      </div>
    </motion.div>
  );
}
