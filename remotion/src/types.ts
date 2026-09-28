export type TextEntrance = 'fade' | 'slide-up' | 'slide-left' | 'scale-pop' | 'typewriter';

export interface KineticSlide {
  section: string;
  text: string;
  subtext?: string;
  bullets?: string[];
  entrance: TextEntrance;
  startFrame: number;
  durationInFrames: number;
  /** Stock clip under this slide, path relative to remotion/public */
  backgroundVideo?: string;
  backgroundVideoStart?: number;
  /** Screenshot under this slide (site / repo demos), path relative to remotion/public */
  backgroundImage?: string;
  emphasis?: string[];
}

export interface BrandTheme {
  name: string;
  primary: string;
  accent: string;
  bg: string;
  text: string;
  textMuted: string;
  gradientColors: string[];
  cta?: string;
  ctaUrl?: string;
  ctaSubtext?: string;
}

export interface CaptionChunk {
  start: number;
  end: number;
  words: { text: string; ws: number; we: number }[];
}

export interface KineticVideoData {
  title: string;
  slug: string;
  fps: number;
  width: number;
  height: number;
  totalDurationInFrames: number;
  audioFile: string;
  musicFile?: string;
  musicVolume?: number;
  slides: KineticSlide[];
  brand: BrandTheme;
  /** Word-by-word chunk captions instead of one phrase per slide */
  wordCaptions?: boolean;
  captions?: CaptionChunk[];
  /** Animated gradient + drifting glow instead of a static gradient */
  animatedBg?: boolean;
  /** Thin progress bar along the bottom */
  showProgress?: boolean;
}

export const DEFAULT_THEME: BrandTheme = {
  name: 'Shorts Kit',
  primary: '#1F2937',
  accent: '#F59E0B',
  bg: '#111827',
  text: '#FFFFFF',
  textMuted: '#D1D5DB',
  gradientColors: ['#111827', '#1F2937', '#374151'],
};
