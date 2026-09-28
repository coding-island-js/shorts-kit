import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';

/**
 * Chunk-based captions: a short phrase holds still while the spoken word pops.
 * A short phrase (1-3 words) sits STILL; every word is white; only the word being
 * spoken pops in the brand accent color. The whole chunk swaps in with a spring.
 * No sliding window, no dimmed past words (that read as "disoriented").
 *
 * data.captions = [{ start, end, words: [{ text, ws, we }] }]  — all in FRAMES.
 */
export interface CaptionChunk {
  start: number;
  end: number;
  words: { text: string; ws: number; we: number }[];
}

// 16-point circular stroke for hard readability over any b-roll
const stroke = (px: number, color: string) =>
  Array.from({ length: 16 }, (_, i) => {
    const a = (i / 16) * Math.PI * 2;
    return `${Math.cos(a) * px}px ${Math.sin(a) * px}px 0 ${color}`;
  }).join(', ');

export const ChunkCaptions: React.FC<{
  captions: CaptionChunk[];
  accent: string;
  position?: number; // fraction from top of the caption block center
  fontSize?: number;
}> = ({ captions, accent, position = 0.6, fontSize = 86 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!captions || captions.length === 0) return null;

  const chunk = captions.find((c) => frame >= c.start && frame < c.end);
  if (!chunk) return null;

  // Per-chunk entrance: snap-scale + slight rise (MrBeast-snappy)
  const s = spring({ frame: frame - chunk.start, fps, config: { damping: 12, mass: 0.5, stiffness: 200 } });
  const scale = interpolate(s, [0, 1], [0.72, 1]);
  const rise = interpolate(s, [0, 1], [44, 0]);
  const op = interpolate(s, [0, 1], [0, 1]);

  const hardStroke = stroke(7, '#0a0f1a');
  const glow = `0 0 22px ${accent}aa`;

  return (
    <div
      style={{
        position: 'absolute',
        top: `${position * 100}%`,
        left: 40,
        right: 40,
        transform: `translateY(-50%)`,
        display: 'flex',
        justifyContent: 'center',
        zIndex: 200,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignItems: 'center',
          gap: `${fontSize * 0.1}px ${fontSize * 0.4}px`,
          maxWidth: '92%',
          transform: `translateY(${rise}px) scale(${scale})`,
          opacity: op,
        }}
      >
        {chunk.words.map((w, i) => {
          const on = frame >= w.ws && frame <= w.we;
          const pop = on
            ? interpolate(frame - w.ws, [0, 3, 7], [1.0, 1.1, 1.05], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              })
            : 1.0;
          return (
            <span
              key={i}
              style={{
                fontFamily: 'Inter, "Helvetica Neue", Arial, sans-serif',
                fontWeight: 900,
                fontSize,
                lineHeight: 1.02,
                letterSpacing: '-0.02em',
                color: on ? accent : '#FFFFFF',
                textShadow: on ? `${hardStroke}, ${glow}` : hardStroke,
                transform: `scale(${pop})`,
                display: 'inline-block',
                textTransform: 'uppercase',
              }}
            >
              {w.text}
            </span>
          );
        })}
      </div>
    </div>
  );
};
