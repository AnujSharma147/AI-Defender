import { useEffect, useRef } from "react";
import { motion } from "framer-motion";

interface JarvisOverlayProps {
  progress: number;
  onComplete: () => void;
  subtitle?: string;
}

export default function JarvisOverlay({ progress, onComplete, subtitle }: JarvisOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    canvas.width = 400;
    canvas.height = 400;
    let frame = 0;
    let animId: number;

    const draw = () => {
      ctx.clearRect(0, 0, 400, 400);
      const cx = 200, cy = 200;
      const time = frame * 0.02;

      // Outer rotating ring
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(time);
      ctx.strokeStyle = "rgba(157, 78, 221, 0.4)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let i = 0; i < 6; i++) {
        const angle = (i / 6) * Math.PI * 2;
        const r = 150 + Math.sin(time * 2 + i) * 10;
        const x = Math.cos(angle) * r;
        const y = Math.sin(angle) * r;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.stroke();
      ctx.restore();

      // Inner star
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(-time * 1.5);
      ctx.strokeStyle = "rgba(139, 92, 246, 0.6)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      for (let i = 0; i < 8; i++) {
        const angle = (i / 8) * Math.PI * 2;
        const r = i % 2 === 0 ? 100 : 50;
        const x = Math.cos(angle) * r;
        const y = Math.sin(angle) * r;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.stroke();
      ctx.restore();

      // Neural connections
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(time * 0.5);
      ctx.strokeStyle = "rgba(34, 211, 238, 0.15)";
      ctx.lineWidth = 0.5;
      for (let i = 0; i < 12; i++) {
        const a1 = (i / 12) * Math.PI * 2;
        const a2 = ((i + 5) / 12) * Math.PI * 2;
        ctx.beginPath();
        ctx.moveTo(Math.cos(a1) * 130, Math.sin(a1) * 130);
        ctx.lineTo(Math.cos(a2) * 80, Math.sin(a2) * 80);
        ctx.stroke();
      }
      ctx.restore();

      // Glowing center dot
      const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, 30);
      gradient.addColorStop(0, "rgba(157, 78, 221, 0.8)");
      gradient.addColorStop(1, "rgba(157, 78, 221, 0)");
      ctx.fillStyle = gradient;
      ctx.fillRect(cx - 30, cy - 30, 60, 60);

      frame++;
      animId = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animId);
  }, []);

  useEffect(() => {
    if (progress >= 100) {
      const t = setTimeout(onComplete, 500);
      return () => clearTimeout(t);
    }
  }, [progress, onComplete]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.9)", backdropFilter: "blur(10px)" }}
    >
      <div className="relative flex flex-col items-center">
        {/* Animated ring */}
        <div
          className="absolute rounded-full animate-jarvis-pulse"
          style={{
            width: 350,
            height: 350,
            border: "2px solid rgba(157, 78, 221, 0.5)",
          }}
        />
        <div
          className="absolute rounded-full animate-jarvis-rotate"
          style={{
            width: 320,
            height: 320,
            border: "1px dashed rgba(34, 211, 238, 0.2)",
          }}
        />

        <canvas ref={canvasRef} className="relative z-10" style={{ width: 400, height: 400 }} />

        <div className="absolute inset-0 flex flex-col items-center justify-center z-20">
          <span
            className="text-3xl font-black tracking-[0.3em]"
            style={{
              color: "white",
              textShadow: "0 0 20px rgba(157, 78, 221, 0.8), 0 0 40px rgba(157, 78, 221, 0.4)",
            }}
          >
            JARVIS
          </span>
          <span className="font-mono-hud text-xs text-glow-cyan mt-2 tracking-widest">
            {subtitle ?? "ANALYZING NEURAL PATTERNS"}
          </span>
        </div>

        {/* Progress bar */}
        <div className="mt-8 w-64 relative">
          <div className="h-1 rounded-full" style={{ background: "rgba(34, 211, 238, 0.1)" }}>
            <motion.div
              className="h-full rounded-full"
              style={{ background: "var(--dd-gradient)" }}
              initial={{ width: "0%" }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
          <div className="flex justify-between mt-2">
            <span className="font-mono-hud text-xs text-glow-cyan">{progress}%</span>
            <span className="font-mono-hud text-xs text-muted-foreground">DEEP SCAN</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
