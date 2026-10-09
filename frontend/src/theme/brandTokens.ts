/**
 * Lotus Fin — Core Brand Design Tokens
 * Single Source of Truth for Brand Colors, Gradients & Typography.
 * Follows Brand Guideline specifications from docs/frontend/05_BRAND_GUIDELINE.md
 */

export const LOTUS_BRAND_COLORS = {
  // 1. Brand Colors (Màu chủ đạo)
  blueDeep: "#1E63B7",     // Primary Brand Anchor: R: 30, G: 99, B: 183
  blueLight: "#6EC1F6",    // Transition tone / Highlight: R: 110, G: 193, B: 246
  teal: "#39C6B7",         // Balance & Tagline: R: 57, G: 198, B: 183
  mintGreen: "#2FB29A",    // Growth & Financial Health: R: 47, G: 178, B: 154
  pinkAccent: "#FF8FB1",   // Lotus Blossom Accent / AI Highlights: R: 255, G: 143, B: 177
  pinkLight: "#FFDDE7",    // Soft Rose Accent: R: 255, G: 221, B: 231

  // 2. Neutral & Support (Màu phụ)
  textPrimary: "#2E3A59",   // High-contrast primary text: R: 46, G: 58, B: 89
  textSecondary: "#8FA1B3", // Subtitles, captions, placeholders: R: 143, G: 161, B: 179
  backgroundLight: "#E8F2FB", // Light tinted surface background: R: 232, G: 242, B: 251

  // 3. UI Semantic Tokens
  surface: "#FFFFFF",
  borderLight: "#E4E7EC",
  borderSubtle: "#F2F4F7",
  success: "#12B76A",
  warning: "#F79009",
  error: "#F04438",
  info: "#1E63B7",
} as const;

export const LOTUS_GRADIENTS = {
  // Primary gradient (Key Visual / Hero / Logo): Deep Blue -> Light Blue -> Mint Green
  primary: "linear-gradient(90deg, #1E63B7 0%, #6EC1F6 50%, #2FB29A 100%)",
  // Primary angled gradient
  primary135: "linear-gradient(135deg, #1E63B7 0%, #6EC1F6 50%, #2FB29A 100%)",
  // Accent gradient: Soft Rose -> Pink Accent
  accent: "linear-gradient(90deg, #FFDDE7 0%, #FF8FB1 100%)",
  // Overlay gradient for soft layout depth
  overlay: "linear-gradient(180deg, rgba(232, 242, 251, 0.7) 0%, rgba(255, 255, 255, 0) 100%)",
} as const;

export const LOTUS_ASSETS = {
  logo: "/brand/logo.jpg",
  favicon: "/brand/favicon.jpg",
  wordmark: "/brand/text.jpg",
  paletteGuideline: "/brand/brand-guideline.jpg",
} as const;

