import React from 'react';
import { Composition } from 'remotion';
import { KineticShort } from './KineticShort';
import type { KineticVideoData } from './types';
import { DEFAULT_THEME } from './types';

// Placeholder props so `npx remotion studio` opens without a render queued.
// Real renders pass work/<slug>/data.json with --props.
const PREVIEW: KineticVideoData = {
  title: 'Preview',
  slug: 'preview',
  fps: 30,
  width: 1080,
  height: 1920,
  totalDurationInFrames: 150,
  audioFile: '',
  slides: [
    { section: 'HOOK', text: 'Render a Short to see it here.', entrance: 'scale-pop', startFrame: 0, durationInFrames: 90 },
    { section: 'CTA', text: '', entrance: 'fade', startFrame: 90, durationInFrames: 60 },
  ],
  brand: DEFAULT_THEME,
};

export const RemotionRoot: React.FC = () => (
  <Composition
    id="KineticShort"
    component={KineticShort as unknown as React.FC<Record<string, unknown>>}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={PREVIEW.totalDurationInFrames}
    defaultProps={PREVIEW as unknown as Record<string, unknown>}
    calculateMetadata={({ props }) => {
      const p = props as unknown as KineticVideoData;
      return { durationInFrames: p.totalDurationInFrames, fps: p.fps, width: p.width, height: p.height };
    }}
  />
);
