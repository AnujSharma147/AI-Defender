import { motion } from "framer-motion";
import { RotateCcw, Image, Video, AudioLines } from "lucide-react";

export interface Detection {
  object: string;
  confidence: number;
}

export interface ModelPrediction {
  name: string;
  prediction: string;
  real_prob: number;
  fake_prob: number;
}

export interface AudioAnalysisResult {
  prediction: string;
  confidence: number;
  real_prob_avg: number;
  fake_prob_avg: number;
  votes?: {
    REAL: number;
    FAKE: number;
  };
  individual_models?: {
    [key: string]: {
      prediction: string;
      real_prob: number;
      fake_prob: number;
    };
  };
  duration_sec?: number;
  model?: string;
}

export interface MediaResult {
  id: string;
  filename: string;
  mediaType: "image" | "video" | "audio";
  detections: Detection[];
  prediction?: string;
  confidence?: number;
  score?: number;
  threshold?: number;
  detector?: string;
  qualityWarnings?: string[];
  audioAnalysis?: AudioAnalysisResult;
  audioFile?: File;
}

interface ResultCardProps {
  results: MediaResult[];
  onRestore: () => void;
}

export default function ResultCard({ results, onRestore }: ResultCardProps) {

  const getMediaIcon = (mediaType: MediaResult["mediaType"]) => {
    if (mediaType === "video") {
      return <Video className="w-5 h-5" style={{ color: "var(--dd-magenta)" }} />;
    }
    if (mediaType === "audio") {
      return <AudioLines className="w-5 h-5" style={{ color: "#f59e0b" }} />;
    }
    return <Image className="w-5 h-5" style={{ color: "var(--dd-cyan)" }} />;
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.8, type: "spring" }}
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.85)", backdropFilter: "blur(15px)" }}
    >
      <div
        className="w-full max-w-4xl mx-5 glass-panel p-6 md:p-8"
        style={{ maxHeight: "88vh", overflowY: "auto" }}
      >

        <motion.h1
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-2xl md:text-3xl font-black tracking-wider text-glow-cyan-heavy mb-2"
        >
          SCAN RESULTS
        </motion.h1>

        <p className="font-mono-hud text-xs text-muted-foreground mb-6">
          Files analyzed: {results.length}
        </p>

        <div className="space-y-4 mb-8">

          {results.map((item, index) => {

            const avgConfidence = typeof item.score === "number"
              ? item.score
              : item.detections.length > 0
                ? item.detections.reduce((a, b) => a + b.confidence, 0) / item.detections.length
                : 0.5;

            const realPercent = Math.round(avgConfidence * 100);
            const fakePercent = 100 - realPercent;

            return (

              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.25 + index * 0.05 }}
                className="rounded-2xl p-4"
                style={{
                  background: "rgba(10, 10, 30, 0.7)",
                  border: "1px solid rgba(34, 211, 238, 0.25)",
                }}
              >

                {/* Header */}
                <div className="flex items-center gap-3 mb-3">

                  {getMediaIcon(item.mediaType)}

                  <div>
                    <p className="font-mono-hud text-xs md:text-sm text-glow-cyan truncate">
                      {item.filename}
                    </p>

                    <p className="font-mono-hud text-[10px] text-muted-foreground uppercase tracking-widest">
                      {item.mediaType}
                    </p>
                  </div>

                </div>

                {/* Fake / Real meter */}

                <div className="grid grid-cols-2 gap-3 mb-4">

                  <div
                    className="rounded-xl px-4 py-3"
                    style={{
                      background: "rgba(239,68,68,0.15)",
                      border: "1px solid rgba(239,68,68,0.35)"
                    }}
                  >
                    <p className="text-xs text-red-300 font-mono-hud tracking-widest">
                      FAKE
                    </p>
                    <p className="text-xl font-black text-red-400">
                      {fakePercent}%
                    </p>
                  </div>

                  <div
                    className="rounded-xl px-4 py-3"
                    style={{
                      background: "rgba(34,211,238,0.15)",
                      border: "1px solid rgba(34,211,238,0.35)"
                    }}
                  >
                    <p className="text-xs text-cyan-200 font-mono-hud tracking-widest">
                      REAL
                    </p>
                    <p className="text-xl font-black text-cyan-300">
                      {realPercent}%
                    </p>
                  </div>

                </div>

                {item.prediction && (
                  <div
                    className="rounded-xl px-4 py-3 mb-4"
                    style={{
                      background: "rgba(34,211,238,0.08)",
                      border: "1px solid rgba(34,211,238,0.2)",
                    }}
                  >
                    <p className="font-mono-hud text-xs text-cyan-200 tracking-widest mb-1">
                      FINAL RESULT
                    </p>

                    <p className="text-lg font-black text-cyan-100 mb-1 tracking-wide">
                      {item.prediction}
                    </p>

                    {typeof item.confidence === "number" && (
                      <p className="font-mono-hud text-[11px] text-cyan-300">
                        Confidence: {(item.confidence * 100).toFixed(1)}%
                      </p>
                    )}
                  </div>
                )}

                {/* Audio Player */}
                {item.mediaType === "audio" && (
                  <div className="rounded-xl px-4 py-4 mb-4" style={{
                    background: "rgba(245,158,11,0.1)",
                    border: "1px solid rgba(245,158,11,0.3)"
                  }}>
                    <p className="font-mono-hud text-xs text-amber-200 mb-3 tracking-widest">
                      🎵 AUDIO PLAYBACK
                    </p>
                    <audio 
                      controls 
                      style={{ width: "100%" }}
                      className="rounded-lg"
                    >
                      <source src={item.audioFile ? URL.createObjectURL(item.audioFile) : ""} />
                      Your browser does not support the audio element.
                    </audio>
                  </div>
                )}

                {/* Ensemble Model Predictions */}
                {item.mediaType === "audio" && item.audioAnalysis?.individual_models && (
                  <div className="rounded-xl px-4 py-4 mb-4" style={{
                    background: "rgba(168,85,247,0.1)",
                    border: "1px solid rgba(168,85,247,0.3)"
                  }}>
                    <p className="font-mono-hud text-xs text-purple-200 mb-3 tracking-widest">
                      🤖 INDIVIDUAL MODEL ANALYSIS
                    </p>
                    
                    <div className="space-y-3">
                      {Object.entries(item.audioAnalysis.individual_models).map(([modelKey, modelData]) => {
                        const modelName = modelKey
                          .replace(/_/g, " ")
                          .replace("Model", "Model")
                          .split("_")
                          .slice(1)
                          .join(" ");
                        
                        return (
                          <div key={modelKey} className="rounded-lg p-3" style={{
                            background: "rgba(20,20,40,0.6)",
                            border: "1px solid rgba(168,85,247,0.2)"
                          }}>
                            <div className="flex justify-between items-center mb-2">
                              <p className="font-mono-hud text-xs text-purple-300">
                                {modelName}
                              </p>
                              <span className={`font-bold text-xs px-2 py-1 rounded ${
                                modelData.prediction === "REAL" 
                                  ? "bg-cyan-900/30 text-cyan-300" 
                                  : "bg-red-900/30 text-red-300"
                              }`}>
                                {modelData.prediction}
                              </span>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-[11px]">
                              <div>
                                <span className="text-cyan-200">REAL: </span>
                                <span className="text-cyan-300 font-bold">{modelData.real_prob.toFixed(1)}%</span>
                              </div>
                              <div>
                                <span className="text-red-200">FAKE: </span>
                                <span className="text-red-300 font-bold">{modelData.fake_prob.toFixed(1)}%</span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Ensemble Voting Results */}
                {item.mediaType === "audio" && item.audioAnalysis?.votes && (
                  <div className="rounded-xl px-4 py-4 mb-4" style={{
                    background: "rgba(34,211,238,0.08)",
                    border: "1px solid rgba(34,211,238,0.2)"
                  }}>
                    <p className="font-mono-hud text-xs text-cyan-200 mb-3 tracking-widest">
                      🗳️ ENSEMBLE MAJORITY VOTE
                    </p>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="rounded-lg p-3" style={{
                        background: "rgba(34,211,238,0.15)",
                        border: "1px solid rgba(34,211,238,0.3)"
                      }}>
                        <p className="font-mono-hud text-[10px] text-cyan-300 mb-1">REAL VOTES</p>
                        <p className="text-2xl font-black text-cyan-300">{item.audioAnalysis.votes.REAL}/3</p>
                      </div>
                      <div className="rounded-lg p-3" style={{
                        background: "rgba(239,68,68,0.15)",
                        border: "1px solid rgba(239,68,68,0.3)"
                      }}>
                        <p className="font-mono-hud text-[10px] text-red-300 mb-1">FAKE VOTES</p>
                        <p className="text-2xl font-black text-red-300">{item.audioAnalysis.votes.FAKE}/3</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Average Probabilities */}
                {item.mediaType === "audio" && item.audioAnalysis && (
                  <div className="rounded-xl px-4 py-4 mb-4" style={{
                    background: "rgba(34,211,238,0.08)",
                    border: "1px solid rgba(34,211,238,0.2)"
                  }}>
                    <p className="font-mono-hud text-xs text-cyan-200 mb-3 tracking-widest">
                      📊 ENSEMBLE AVERAGES
                    </p>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="font-mono-hud text-[11px] text-cyan-300 mb-1">Avg REAL Probability</p>
                        <p className="text-xl font-black text-cyan-300">{item.audioAnalysis.real_prob_avg.toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="font-mono-hud text-[11px] text-red-300 mb-1">Avg FAKE Probability</p>
                        <p className="text-xl font-black text-red-300">{item.audioAnalysis.fake_prob_avg.toFixed(1)}%</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Audio Duration */}
                {item.mediaType === "audio" && item.audioAnalysis?.duration_sec && (
                  <div className="rounded-xl px-4 py-2 mb-4 text-[11px]" style={{
                    background: "rgba(34,211,238,0.08)",
                    border: "1px solid rgba(34,211,238,0.2)"
                  }}>
                    <p className="font-mono-hud text-cyan-300">
                      Duration: {item.audioAnalysis.duration_sec.toFixed(2)}s | 
                      Model: 3-Model Ensemble (Wav2Vec2 + WavLM)
                    </p>
                  </div>
                )}

                {item.mediaType === "image" && (
                  <div
                    className="rounded-xl px-4 py-3"
                    style={{
                      background: "rgba(34,211,238,0.08)",
                      border: "1px solid rgba(34,211,238,0.2)"
                    }}
                  >

                    <p className="font-mono-hud text-xs text-cyan-200 mb-2 tracking-widest">
                      DETECTED OBJECTS
                    </p>

                    {item.detections.length === 0 && (
                      <p className="text-xs text-muted-foreground">
                        No objects detected
                      </p>
                    )}

                    {item.detections.map((det, i) => (

                      <div
                        key={i}
                        className="flex justify-between text-sm font-mono-hud py-1"
                      >

                        <span className="text-cyan-200">
                          {det.object}
                        </span>

                        <span className="text-cyan-300">
                          {(det.confidence * 100).toFixed(1)}%
                        </span>

                      </div>

                    ))}

                  </div>
                )}

              </motion.div>

            );
          })}

        </div>

        <motion.button
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45 }}
          onClick={onRestore}
          className="btn-gradient py-4 px-10 text-sm tracking-[0.2em] uppercase flex items-center gap-3 mx-auto"
        >
          <RotateCcw className="w-5 h-5" />
          SYSTEM RESTORE
        </motion.button>

      </div>

    </motion.div>
  );
}