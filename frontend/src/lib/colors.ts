import type { AlertLevel } from "./types";

// NHS Digital / USWDS / IEC 60601-1-8 inspired design tokens
export const palette = {
  // Surfaces
  surface: "#FFFFFF",
  border: "#D8DDE0",
  borderLight: "#E8EDEE",

  // Typography
  text1: "#212B32",
  text2: "#4C6272",
  text3: "#5F6D78",

  // Brand
  blue: "#005EB8",

  // Chart series
  chart1: "#6366F1",
  chart2: "#06B6D4",
  chart3: "#F59E0B",

  // Semaphore - IEC 60601-1-8 alarm semantics
  green: "#007F3B",
  greenBg: "#F0F7F3",
  yellow: "#FFB81C",
  yellowBg: "#FFF9E6",
  orange: "#ED8B00",
  orangeBg: "#FFF4E5",
  red: "#D5281B",
  redBg: "#FDF2F1",
} as const;

export const LEVEL_COLOR: Record<AlertLevel, string> = {
  green: palette.green,
  yellow: palette.yellow,
  orange: palette.orange,
  red: palette.red,
};

export const LEVEL_BG: Record<AlertLevel, string> = {
  green: palette.greenBg,
  yellow: palette.yellowBg,
  orange: palette.orangeBg,
  red: palette.redBg,
};

/** Accessible text-safe versions of level colors (4.5:1+ on white). */
export const LEVEL_TEXT_COLOR: Record<AlertLevel, string> = {
  green: "#007F3B",
  yellow: "#8B6914",
  orange: "#9A4E00",
  red: "#D5281B",
};

/** Text color for use ON a level-colored background. */
export const LEVEL_ON_COLOR: Record<AlertLevel, string> = {
  green: "#FFFFFF",
  yellow: "#212B32",
  orange: "#212B32",
  red: "#FFFFFF",
};

export const alertName: Record<AlertLevel, string> = {
  green: "Verde",
  yellow: "Amarillo",
  orange: "Naranjo",
  red: "Rojo",
};
