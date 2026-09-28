import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

interface GradientBackgroundProps {
  colors: string[];
}

export const GradientBackground: React.FC<GradientBackgroundProps> = ({ colors }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();

  // Slowly rotating gradient
  const angle = (frame * 0.3) % 360;

  // Ken Burns subtle zoom
  const zoom = interpolate(frame, [0, durationInFrames], [1.05, 1.0], {
    extrapolateRight: 'clamp',
  });

  // Breathing glow
  const glowOpacity = 0.06 + Math.sin(frame * 0.02) * 0.03;
  const glowX = 50 + Math.sin(frame * 0.008) * 15;
  const glowY = 50 + Math.cos(frame * 0.006) * 15;

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width,
        height,
        overflow: 'hidden',
      }}
    >
      {/* Main rotating gradient */}
      <div
        style={{
          position: 'absolute',
          top: '-5%',
          left: '-5%',
          width: '110%',
          height: '110%',
          background: `linear-gradient(${angle}deg, ${colors[0]}, ${colors[1]}, ${colors[2] || colors[0]})`,
          transform: `scale(${zoom})`,
        }}
      />

      {/* Radial glow overlay */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: `radial-gradient(circle at ${glowX}% ${glowY}%, ${colors[1]}44, transparent 60%)`,
          opacity: glowOpacity * 10,
        }}
      />

      {/* Subtle noise/texture overlay */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'radial-gradient(circle at 50% 50%, transparent 40%, rgba(0,0,0,0.3) 100%)',
        }}
      />
    </div>
  );
};
