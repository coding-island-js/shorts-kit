import React from 'react';
import {
  useCurrentFrame,
  useVideoConfig,
  Audio,
  Img,
  Sequence,
  staticFile,
  OffthreadVideo,
  interpolate,
} from 'remotion';
import type { KineticVideoData, KineticSlide } from './types';
import { DEFAULT_THEME } from './types';
import { GradientBackground } from './components/GradientBackground';
import { PremiumBackground, ProgressBar } from './components/PremiumBackground';
import { KineticText } from './components/KineticText';
import { ChunkCaptions } from './components/ChunkCaptions';
import { CTAEndCard } from './components/CTAEndCard';

export const AUDIO_DELAY_FRAMES = 22; // 0.73s beat before the voice starts

type BgRun = Pick<KineticSlide, 'backgroundVideo' | 'backgroundVideoStart' | 'backgroundImage'> & {
  startFrame: number;
  durationInFrames: number;
};

// Consecutive slides that share a background become one run, so the clip or
// screenshot plays straight through instead of fading out between sentences.
const backgroundRuns = (slides: KineticSlide[]): BgRun[] => {
  const runs: BgRun[] = [];
  for (const s of slides) {
    if (!s.backgroundVideo && !s.backgroundImage) continue;
    const prev = runs[runs.length - 1];
    const same =
      prev &&
      prev.backgroundVideo === s.backgroundVideo &&
      prev.backgroundImage === s.backgroundImage &&
      prev.startFrame + prev.durationInFrames === s.startFrame;
    if (same) prev.durationInFrames += s.durationInFrames;
    else
      runs.push({
        backgroundVideo: s.backgroundVideo,
        backgroundVideoStart: s.backgroundVideoStart,
        backgroundImage: s.backgroundImage,
        startFrame: s.startFrame,
        durationInFrames: s.durationInFrames,
      });
  }
  return runs;
};

const runOpacity = (frame: number, run: BgRun, peak: number) => {
  const fade = Math.min(12, Math.floor(run.durationInFrames / 3));
  const end = run.startFrame + run.durationInFrames;
  const a = run.startFrame + fade;
  const b = Math.max(a + 1, end - fade);
  return interpolate(frame, [run.startFrame, a, b, end], [0, peak, peak, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
};

export const KineticShort: React.FC<KineticVideoData> = (data) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const brand = data.brand || DEFAULT_THEME;
  const hasShots = data.slides.some((s) => s.backgroundImage);

  return (
    <div style={{ width, height, backgroundColor: brand.bg, position: 'relative', overflow: 'hidden' }}>
      {/* Layer 1: gradient */}
      {data.animatedBg ? (
        <PremiumBackground colors={brand.gradientColors} accent={brand.accent} />
      ) : (
        <GradientBackground colors={brand.gradientColors} />
      )}

      {/* Layer 2: per-slide b-roll clip or screenshot, slow push-in */}
      {backgroundRuns(data.slides).map((slide, i) => {
        const progress = interpolate(
          frame,
          [slide.startFrame, slide.startFrame + slide.durationInFrames],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );
        const zoom = interpolate(progress, [0, 1], [1.0, 1.08]);

        return (
          <Sequence key={`bg-${i}`} from={slide.startFrame} durationInFrames={slide.durationInFrames}>
            <div
              style={{
                position: 'absolute',
                inset: 0,
                opacity: runOpacity(frame, slide, slide.backgroundImage ? 1 : 0.85),
                overflow: 'hidden',
              }}
            >
              {slide.backgroundVideo ? (
                <OffthreadVideo
                  src={staticFile(slide.backgroundVideo)}
                  startFrom={Math.round((slide.backgroundVideoStart || 0) * fps)}
                  muted
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    transform: `scale(${zoom})`,
                    filter: data.animatedBg ? 'contrast(1.12) saturate(1.12) brightness(0.8)' : undefined,
                  }}
                />
              ) : (
                // Screenshots are usually wider than 9:16. Show the whole thing as a
                // floating card over a blurred copy of itself instead of cropping it.
                <>
                  <Img
                    src={staticFile(slide.backgroundImage!)}
                    style={{
                      position: 'absolute',
                      inset: 0,
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      filter: 'blur(40px) brightness(0.45)',
                      transform: 'scale(1.2)',
                    }}
                  />
                  <div
                    style={{
                      position: 'absolute',
                      left: 60,
                      right: 60,
                      top: '12%',
                      height: '46%',
                      borderRadius: 28,
                      overflow: 'hidden',
                      boxShadow: '0 30px 80px rgba(0,0,0,0.55)',
                      transform: `scale(${zoom})`,
                    }}
                  >
                    <Img
                      src={staticFile(slide.backgroundImage!)}
                      style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'top' }}
                    />
                  </div>
                </>
              )}
            </div>
          </Sequence>
        );
      })}

      {/* Darkening overlay so white text reads on any footage */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: data.animatedBg
            ? 'linear-gradient(180deg, rgba(8,18,40,0.45) 0%, rgba(8,18,40,0.25) 45%, rgba(8,18,40,0.6) 100%)'
            : 'linear-gradient(180deg, rgba(0,0,0,0.08) 0%, rgba(0,0,0,0.22) 50%, rgba(0,0,0,0.08) 100%)',
        }}
      />
      {data.animatedBg && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.45) 100%)',
          }}
        />
      )}

      {/* Layer 3: captions — word-by-word chunks, or one phrase per slide */}
      {data.wordCaptions && data.captions && data.captions.length > 0 ? (
        <ChunkCaptions captions={data.captions} accent={brand.accent} position={hasShots ? 0.72 : 0.6} fontSize={86} />
      ) : (
        data.slides.map((slide, i) => {
          if (slide.section === 'CTA' || !slide.text) return null;
          return (
            <KineticText
              key={`text-${i}`}
              text={slide.text}
              subtext={slide.subtext}
              bullets={slide.bullets}
              entrance={slide.entrance}
              startFrame={slide.startFrame}
              durationInFrames={slide.durationInFrames}
              accentColor={brand.accent}
              textColor={brand.text}
              mutedColor={brand.textMuted}
              emphasis={slide.emphasis}
              band={slide.backgroundImage ? 'lower' : 'center'}
            />
          );
        })
      )}

      {/* Layer 4: end card */}
      {data.slides
        .filter((s) => s.section === 'CTA')
        .map((slide, i) => (
          <CTAEndCard
            key={`cta-${i}`}
            brand={brand}
            startFrame={slide.startFrame}
            durationInFrames={slide.durationInFrames}
          />
        ))}

      {data.showProgress && <ProgressBar accent={brand.accent} />}

      {data.audioFile && (
        <Sequence from={AUDIO_DELAY_FRAMES}>
          <Audio src={staticFile(data.audioFile)} volume={1} />
        </Sequence>
      )}
      {data.musicFile && <Audio src={staticFile(data.musicFile)} volume={data.musicVolume ?? 0.05} />}
    </div>
  );
};
