import { useCallback, useRef } from "react";

export function useScanSound() {
  const ctxRef = useRef<AudioContext | null>(null);

  const play = useCallback(() => {
    try {
      const ctx = ctxRef.current ?? new AudioContext();
      ctxRef.current = ctx;

      // Layered sci-fi scan sound
      const now = ctx.currentTime;

      // Low sweep
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      osc1.type = "sine";
      osc1.frequency.setValueAtTime(80, now);
      osc1.frequency.exponentialRampToValueAtTime(200, now + 0.6);
      gain1.gain.setValueAtTime(0.15, now);
      gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.8);
      osc1.connect(gain1).connect(ctx.destination);
      osc1.start(now);
      osc1.stop(now + 0.8);

      // High chirp
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();
      osc2.type = "sawtooth";
      osc2.frequency.setValueAtTime(600, now);
      osc2.frequency.exponentialRampToValueAtTime(1200, now + 0.15);
      osc2.frequency.exponentialRampToValueAtTime(400, now + 0.4);
      gain2.gain.setValueAtTime(0.06, now);
      gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
      osc2.connect(gain2).connect(ctx.destination);
      osc2.start(now);
      osc2.stop(now + 0.5);

      // Beep
      const osc3 = ctx.createOscillator();
      const gain3 = ctx.createGain();
      osc3.type = "square";
      osc3.frequency.setValueAtTime(1000, now + 0.1);
      gain3.gain.setValueAtTime(0, now);
      gain3.gain.linearRampToValueAtTime(0.04, now + 0.1);
      gain3.gain.linearRampToValueAtTime(0, now + 0.25);
      osc3.connect(gain3).connect(ctx.destination);
      osc3.start(now);
      osc3.stop(now + 0.3);
    } catch {
      // Audio not available
    }
  }, []);

  return play;
}
