import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

/**
 * Animated background for --premium Shorts.
 * - Slowly rotating multi-stop gradient
 * - Two large soft accent "glow" blobs drifting on sine waves
 * - Subtle breathing vignette
 * Kept quiet on purpose so the captions stay the loudest thing on screen.
 */
export const PremiumBackground: React.FC<{ colors: string[]; accent: string }> = ({
  colors,
  accent,
}) => {
  const frame = useCurrentFrame();
  const c = colors && colors.length >= 3 ? colors : ['#0f1c33', '#15233b', '#1c3a6b'];
  const angle = 135 + Math.sin(frame * 0.006) * 12; // gentle sway

  const blob = (cx: number, cy: number, r: number, phase: number, op: number) => {
    const x = cx + Math.sin(frame * 0.01 + phase) * 6;
    const y = cy + Math.cos(frame * 0.008 + phase) * 5;
    return {
      position: 'absolute' as const,
      left: `${x}%`,
      top: `${y}%`,
      width: `${r}%`,
      height: `${r}%`,
      transform: 'translate(-50%, -50%)',
      borderRadius: '50%',
      background: `radial-gradient(circle, ${accent}${Math.round(op * 255).toString(16).padStart(2, '0')} 0%, transparent 70%)`,
      filter: 'blur(40px)',
      pointerEvents: 'none' as const,
    };
  };

  const vignette = 0.28 + Math.sin(frame * 0.02) * 0.05;

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden' }}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `linear-gradient(${angle}deg, ${c[0]} 0%, ${c[1]} 55%, ${c[2]} 100%)`,
        }}
      />
      <div style={blob(28, 30, 60, 0, 0.18)} />
      <div style={blob(78, 72, 55, 2.5, 0.14)} />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,${vignette}) 100%)`,
        }}
      />
    </div>
  );
};

/** Thin progress bar pinned to the bottom edge, fills over the whole video. */
export const ProgressBar: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const pct = interpolate(frame, [0, durationInFrames], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: 6, zIndex: 250 }}>
      <div style={{ width: `${pct}%`, height: '100%', background: accent, boxShadow: `0 0 12px ${accent}` }} />
    </div>
  );
};
