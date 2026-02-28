import { LEVEL_COLOR } from "@/lib/colors";
import type { AlertLevel } from "@/lib/types";
import type { CSSProperties } from "react";

interface LevelDotProps {
  level: AlertLevel;
  size?: number;
}

export function LevelDot({ level, size = 7 }: LevelDotProps) {
  const color = LEVEL_COLOR[level];
  return (
    <span
      aria-hidden="true"
      className="rounded-full shrink-0 inline-block bg-(--dot-color) w-(--dot-size) h-(--dot-size)"
      style={{ "--dot-color": color, "--dot-size": `${size}px` } as CSSProperties}
    />
  );
}
