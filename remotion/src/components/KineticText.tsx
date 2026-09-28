import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import type { TextEntrance } from '../types';

interface KineticTextProps {
  text: string;
  subtext?: string;
  bullets?: string[];
  entrance: TextEntrance;
  startFrame: number;
  durationInFrames: number;
  accentColor: string;
  textColor: string;
  mutedColor: string;
  emphasis?: string[];
  /** 'lower' keeps text under a screenshot card instead of on top of it */
  band?: 'center' | 'lower';
}

export const KineticText: React.FC<KineticTextProps> = ({
  text,
  subtext,
  bullets,
  entrance,
  startFrame,
  durationInFrames,
  accentColor,
  textColor,
  mutedColor,
  emphasis = [],
  band = 'center',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = frame - startFrame;

  if (localFrame < 0 || localFrame > durationInFrames) return null;

  // Exit fade (last 8 frames)
  const exitOpacity = interpolate(
    localFrame,
    [durationInFrames - 8, durationInFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Entrance animations
  let opacity = 1;
  let translateY = 0;
  let translateX = 0;
  let scale = 1;

  switch (entrance) {
    case 'fade':
      opacity = interpolate(localFrame, [0, 12], [0, 1], { extrapolateRight: 'clamp' });
      break;
    case 'slide-up':
      opacity = interpolate(localFrame, [0, 10], [0, 1], { extrapolateRight: 'clamp' });
      translateY = interpolate(localFrame, [0, 10], [40, 0], { extrapolateRight: 'clamp' });
      break;
    case 'slide-left':
      opacity = interpolate(localFrame, [0, 10], [0, 1], { extrapolateRight: 'clamp' });
      translateX = interpolate(localFrame, [0, 10], [-60, 0], { extrapolateRight: 'clamp' });
      break;
    case 'scale-pop':
      opacity = interpolate(localFrame, [0, 6], [0, 1], { extrapolateRight: 'clamp' });
      scale = spring({
        frame: localFrame,
        fps,
        config: { damping: 8, stiffness: 200, mass: 0.5 },
      });
      break;
    case 'typewriter':
      opacity = 1;
      break;
  }

  // For typewriter: reveal characters progressively
  const visibleChars =
    entrance === 'typewriter'
      ? Math.floor(interpolate(localFrame, [0, Math.min(30, durationInFrames / 2)], [0, text.length], { extrapolateRight: 'clamp' }))
      : text.length;

  const displayText = text.slice(0, visibleChars);

  // Render text with emphasis words highlighted
  const renderHighlightedText = (t: string) => {
    if (emphasis.length === 0) return t;
    const regex = new RegExp(`\\b(${emphasis.join('|')})\\b`, 'gi');
    const parts = t.split(regex);
    return parts.map((part, i) => {
      const isEmphasis = emphasis.some((e) => e.toLowerCase() === part.toLowerCase());
      if (isEmphasis) {
        return (
          <span key={i} style={{ color: accentColor, fontWeight: 800 }}>
            {part}
          </span>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div
      style={{
        position: 'absolute',
        top: band === 'lower' ? '61%' : 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: band === 'lower' ? 'flex-start' : 'center',
        alignItems: 'center',
        padding: band === 'lower' ? '40px 60px 0' : '120px 60px 80px',
        opacity: opacity * exitOpacity,
        transform: `translate(${translateX}px, ${translateY}px) scale(${scale})`,
      }}
    >
      {/* Main text */}
      <div
        style={{
          fontSize: text.length > 60 ? 52 : text.length > 40 ? 62 : 72,
          fontWeight: 700,
          color: textColor,
          textAlign: 'center',
          lineHeight: 1.2,
          fontFamily: "'Inter', system-ui, sans-serif",
          textShadow: '0 0 8px rgba(0,0,0,0.85), 0 4px 24px rgba(0,0,0,0.75), 0 0 2px rgba(0,0,0,1)',
          WebkitTextStroke: '1.5px rgba(0,0,0,0.9)',
          paintOrder: 'stroke fill',
          maxWidth: 900,
        }}
      >
        {renderHighlightedText(displayText)}
      </div>

      {/* Subtext */}
      {subtext && (
        <div
          style={{
            fontSize: 32,
            color: mutedColor,
            textAlign: 'center',
            marginTop: 20,
            fontFamily: "'Inter', system-ui, sans-serif",
            fontWeight: 500,
            opacity: interpolate(localFrame, [8, 18], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
            textShadow: '0 0 6px rgba(0,0,0,0.8), 0 2px 16px rgba(0,0,0,0.7)',
            WebkitTextStroke: '1px rgba(0,0,0,0.85)',
            paintOrder: 'stroke fill',
          }}
        >
          {subtext}
        </div>
      )}

      {/* Bullets */}
      {bullets && bullets.length > 0 && (
        <div style={{ marginTop: 30, maxWidth: 800 }}>
          {bullets.map((bullet, i) => {
            const bulletDelay = 10 + i * 8;
            const bulletOpacity = interpolate(localFrame, [bulletDelay, bulletDelay + 8], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            const bulletY = interpolate(localFrame, [bulletDelay, bulletDelay + 8], [20, 0], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            return (
              <div
                key={i}
                style={{
                  fontSize: 36,
                  color: textColor,
                  fontFamily: "'Inter', system-ui, sans-serif",
                  fontWeight: 500,
                  padding: '8px 0',
                  opacity: bulletOpacity,
                  transform: `translateY(${bulletY}px)`,
                  textShadow: '0 0 6px rgba(0,0,0,0.8), 0 2px 16px rgba(0,0,0,0.7)',
            WebkitTextStroke: '1px rgba(0,0,0,0.85)',
            paintOrder: 'stroke fill',
                }}
              >
                <span style={{ color: accentColor, marginRight: 12 }}>✓</span>
                {renderHighlightedText(bullet)}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
