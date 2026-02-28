import { palette } from "./colors";

export const GRID = {
  stroke: palette.borderLight,
} as const;

export const X_AXIS = {
  tick: { fill: palette.text2, fontSize: 11 },
  axisLine: { stroke: palette.border },
  tickLine: false,
} as const;

export const Y_AXIS = {
  tick: { fill: palette.text2, fontSize: 11 },
  axisLine: false,
  tickLine: false,
} as const;

export const CHART_MARGIN = { top: 8, right: 16, left: 0, bottom: 0 } as const;

export const TOOLTIP_STYLE = {
  background: palette.surface,
  border: `1px solid ${palette.border}`,
  borderRadius: 4,
  fontSize: 12,
  color: palette.text1,
  padding: "8px 10px",
  boxShadow: "none",
} as const;
