import { motion } from "framer-motion";
import { useEffect, useState } from "react";

interface ShatterEffectProps {
  onComplete: () => void;
}

export default function ShatterEffect({ onComplete }: ShatterEffectProps) {
  const [shards, setShards] = useState<Array<{ id: number; x: number; y: number; r: number; w: number; h: number }>>([]);

  useEffect(() => {
    const cols = 5, rows = 4;
    const arr = [];
    for (let i = 0; i < cols * rows; i++) {
      arr.push({
        id: i,
        x: (Math.random() - 0.5) * 2000,
        y: (Math.random() - 0.5) * 2000,
        r: (Math.random() - 0.5) * 720,
        w: 100 / cols,
        h: 100 / rows,
      });
    }
    setShards(arr);
    const t = setTimeout(onComplete, 1500);
    return () => clearTimeout(t);
  }, [onComplete]);

  return (
    <div className="fixed inset-0 z-[60] pointer-events-none">
      {shards.map((s) => (
        <motion.div
          key={s.id}
          className="absolute"
          style={{
            left: `${(s.id % 5) * s.w}%`,
            top: `${Math.floor(s.id / 5) * s.h}%`,
            width: `${s.w}%`,
            height: `${s.h}%`,
            background: "var(--dd-bg)",
            border: "1px solid rgba(34,211,238,0.1)",
          }}
          initial={{ x: 0, y: 0, rotate: 0, scale: 1, opacity: 1 }}
          animate={{ x: s.x, y: s.y, rotate: s.r, scale: 0.3, opacity: 0 }}
          transition={{ duration: 1.5, ease: [0.76, 0, 0.24, 1] }}
        />
      ))}
    </div>
  );
}
