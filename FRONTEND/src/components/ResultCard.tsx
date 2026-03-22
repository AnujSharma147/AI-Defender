import { motion } from "framer-motion";

import { RotateCcw } from "lucide-react";

interface ResultCardProps {
  isDeepfake: boolean;
  confidence: number;
  onRestore: () => void;
}

export default function ResultCard({ isDeepfake, confidence, onRestore }: ResultCardProps) {
  const message = isDeepfake
    ? "JARVIS has identified synthetic neural artifacts. This media has been digitally manipulated with high confidence. Exercise extreme caution."
    : "JARVIS analysis complete. No synthetic artifacts detected. Media integrity verified across all neural checkpoints.";


  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.8, type: "spring" }}
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.85)", backdropFilter: "blur(15px)" }}
    >

      <div className="flex flex-col items-center max-w-lg text-center px-6">
        {/* Glowing orb */}
        <motion.div
          className="animate-float animate-pulse-glow rounded-full mb-8"
          style={{
            width: 180,
            height: 180,
            background: isDeepfake
              ? "radial-gradient(circle, rgba(255,68,68,0.3), rgba(255,68,68,0.05), transparent)"
              : "radial-gradient(circle, rgba(34,211,238,0.3), rgba(34,211,238,0.05), transparent)",
            boxShadow: isDeepfake
              ? "0 0 60px rgba(255,68,68,0.3), 0 0 120px rgba(255,68,68,0.1)"
              : "0 0 60px rgba(34,211,238,0.3), 0 0 120px rgba(34,211,238,0.1)",
          }}
        />

        {/* Title */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className={`text-3xl md:text-4xl font-black tracking-wider mb-4 ${
            isDeepfake ? "text-glow-danger" : "text-glow-cyan-heavy"
          }`}
        >
          {isDeepfake ? "DEEPFAKE DETECTED" : "MEDIA AUTHENTIC"}
        </motion.h1>

        {/* Percentage */}
        <motion.div
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, type: "spring" }}
          className="mb-6"
        >
          <span
            className="font-black gradient-cv"
            style={{ fontSize: "5rem", lineHeight: 1 }}
          >
            {confidence}%
          </span>
        </motion.div>

        {/* Message */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="font-mono-hud text-sm text-muted-foreground leading-relaxed mb-10 max-w-md"
        >
          {message}
        </motion.p>

        {/* Restore button */}
        <motion.button
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
          onClick={onRestore}
          className="btn-gradient py-4 px-10 text-sm tracking-[0.2em] uppercase flex items-center gap-3"
        >
          <RotateCcw className="w-5 h-5" />
          SYSTEM RESTORE
        </motion.button>

      </div>
    </motion.div>
  );
}
