import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import type { BrandTheme } from '../types';

interface CTAEndCardProps {
  brand: BrandTheme;
  startFrame: number;
  durationInFrames: number;
}

export const CTAEndCard: React.FC<CTAEndCardProps> = ({ brand, startFrame, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = frame - startFrame;

  if (localFrame < 0) return null;

  // Brand name entrance
  const nameScale = spring({
    frame: localFrame,
    fps,
    config: { damping: 10, stiffness: 150, mass: 0.6 },
  });

  // URL fade in
  const urlOpacity = interpolate(localFrame, [15, 25], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // CTA text slide up
  const ctaY = interpolate(localFrame, [25, 35], [30, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaOpacity = interpolate(localFrame, [25, 35], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Subtle pulse on URL
  const urlScale = 1 + 0.02 * Math.sin(localFrame * 0.08);

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        gap: 24,
      }}
    >
      {/* Brand name */}
      <div
        style={{
          fontSize: 72,
          fontWeight: 800,
          color: brand.text,
          fontFamily: "'Inter', system-ui, sans-serif",
          transform: `scale(${nameScale})`,
          letterSpacing: -1,
        }}
      >
        {brand.name}
      </div>

      {/* Accent line */}
      <div
        style={{
          width: interpolate(localFrame, [10, 20], [0, 120], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
          height: 3,
          backgroundColor: brand.accent,
          borderRadius: 2,
        }}
      />

      {/* URL */}
      {brand.ctaUrl && (
        <div
          style={{
            fontSize: 36,
            color: brand.accent,
            fontFamily: "'Inter', system-ui, sans-serif",
            fontWeight: 600,
            opacity: urlOpacity,
            transform: `scale(${urlScale})`,
          }}
        >
          {brand.cta || brand.ctaUrl}
        </div>
      )}

      {/* CTA subtext */}
      {brand.ctaSubtext && (
        <div
          style={{
            fontSize: 24,
            color: brand.textMuted,
            fontFamily: "'Inter', system-ui, sans-serif",
            fontWeight: 400,
            opacity: ctaOpacity,
            transform: `translateY(${ctaY}px)`,
          }}
        >
          {brand.ctaSubtext}
        </div>
      )}
    </div>
  );
};
