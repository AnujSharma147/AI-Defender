import { useState, useCallback, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import ParticleField from "@/components/ParticleField";
import ScanPanel from "@/components/ScanPanel";
import StatusPanel from "@/components/StatusPanel";
import JarvisOverlay from "@/components/JarvisOverlay";
import ResultCard from "@/components/ResultCard";
import ShatterEffect from "@/components/ShatterEffect";
import { useVoice } from "@/hooks/useVoice";
import { useMouseGlow } from "@/hooks/useMouseGlow";
import { useScanSound } from "@/hooks/useScanSound";
import { Shield } from "lucide-react";

type Phase = "idle" | "scanning" | "shatter" | "result";

const Index = () => {
  const [phase, setPhase] = useState<Phase>("idle");
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<{ isDeepfake: boolean; confidence: number } | null>(null);
  const { speak } = useVoice();
  const mouse = useMouseGlow();
  const playScanSound = useScanSound();

  const startScan = useCallback((_url: string) => {
    playScanSound();
    setPhase("scanning");
    setProgress(0);
  }, [playScanSound]);

  // Simulate progress
  useEffect(() => {
    if (phase !== "scanning") return;
    const interval = setInterval(() => {
      setProgress((p) => {
        if (p >= 99) {
          clearInterval(interval);
          setPhase("shatter");
          return 99;
        }
        return p + Math.random() * 3 + 1;
      });
    }, 100);
    return () => clearInterval(interval);
  }, [phase]);

  const onShatterComplete = useCallback(() => {
    const isDeepfake = Math.random() > 0.5;
    const confidence = isDeepfake
      ? Math.floor(85 + Math.random() * 14)
      : Math.floor(90 + Math.random() * 9);
    setResult({ isDeepfake, confidence });
    setPhase("result");

    // Voice
    setTimeout(() => {
      speak(
        isDeepfake
          ? `Warning. Deepfake detected with ${confidence} percent confidence. Synthetic neural artifacts identified. Exercise caution.`
          : `Analysis complete. Media verified as authentic with ${confidence} percent confidence. No synthetic artifacts detected.`
      );
    }, 800);
  }, [speak]);

  const restore = useCallback(() => {
    setPhase("idle");
    setProgress(0);
    setResult(null);
  }, []);

  return (
    <div className="min-h-screen relative cursor-none">
      {/* Mouse glow */}
      <div
        className="pointer-events-none fixed z-[100] rounded-full"
        style={{
          left: mouse.x - 150,
          top: mouse.y - 150,
          width: 300,
          height: 300,
          background: "radial-gradient(circle, rgba(34,211,238,0.07) 0%, transparent 70%)",
          transition: "left 0.05s linear, top 0.05s linear",
        }}
      />
      {/* Cyan neon cursor */}
      <div
        className="pointer-events-none fixed z-[101] rounded-full"
        style={{
          left: mouse.x - 6,
          top: mouse.y - 6,
          width: 12,
          height: 12,
          background: "var(--dd-cyan)",
          boxShadow: "0 0 8px var(--dd-cyan), 0 0 20px rgba(34,211,238,0.4)",
          transition: "left 0.02s linear, top 0.02s linear",
        }}
      />
      <ParticleField />

      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="relative z-10 flex items-center justify-between px-8 py-6"
      >
        <div className="flex items-center gap-3">
          <Shield className="w-8 h-8" style={{ color: "var(--dd-cyan)", filter: "drop-shadow(0 0 8px rgba(34,211,238,0.5))" }} />
          <div>
            <h1 className="text-xl font-black tracking-wider text-glow-cyan">DEEP-DEFEND</h1>
            <span className="font-mono-hud text-[10px] text-muted-foreground tracking-[0.3em]">v4.0 // NEURAL DEFENSE SYSTEM</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="w-2 h-2 rounded-full" style={{ background: "var(--dd-cyan)", boxShadow: "0 0 10px var(--dd-cyan)" }} />
          <span className="font-mono-hud text-xs text-glow-cyan">SYSTEM ONLINE</span>
        </div>
      </motion.header>

      {/* Main Grid */}
      <main className="relative z-10 px-8 py-4 max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-8">
          <ScanPanel onScan={startScan} isScanning={phase === "scanning"} />
          <StatusPanel progress={Math.min(progress, 100)} isScanning={phase === "scanning"} />
        </div>

        {/* Footer tagline */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="text-center mt-12"
        >
          <p className="font-mono-hud text-xs text-muted-foreground/40 tracking-[0.4em]">
            POWERED BY JARVIS NEURAL ENGINE • QUANTUM VERIFIED
          </p>
        </motion.div>
      </main>

      {/* Overlays */}
      <AnimatePresence>
        {phase === "scanning" && (
          <JarvisOverlay progress={Math.min(Math.round(progress), 99)} onComplete={() => {}} />
        )}
      </AnimatePresence>

      {phase === "shatter" && <ShatterEffect onComplete={onShatterComplete} />}

      <AnimatePresence>
        {phase === "result" && result && (
          <ResultCard
            isDeepfake={result.isDeepfake}
            confidence={result.confidence}
            onRestore={restore}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default Index;
