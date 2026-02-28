import type React from "react";
import type { ForecastData } from "@/lib/types";
import { LEVEL_COLOR, LEVEL_ON_COLOR, LEVEL_BG, alertName } from "@/lib/colors";
import { formatNumber } from "@/lib/format";

import { Card } from "@/components/ui/Card";
import { SectionTitle } from "@/components/ui/SectionTitle";

interface ForecastCardsProps {
  forecast: ForecastData | null;
}

export function ForecastCards({ forecast }: ForecastCardsProps) {
  if (!forecast || forecast.status !== "ok") return null;

  return (
    <section aria-label="Pronóstico por semana epidemiológica">
      <Card className="p-5">
        <SectionTitle>Pronóstico por semana</SectionTitle>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-1.5 md:gap-2.5">
          {forecast.horizons.map((h) => {
            const fg = LEVEL_COLOR[h.color];
            const onFg = LEVEL_ON_COLOR[h.color];
            const bg = LEVEL_BG[h.color];
            const name = alertName[h.color];

            return (
              <div
                key={h.horizon}
                className="p-2 md:p-3.5 rounded text-center border border-(--fc-fg)/15 bg-(--fc-bg)"
                style={{ "--fc-fg": fg, "--fc-bg": bg, "--fc-on": onFg } as React.CSSProperties}
              >
                <div className="text-3xs md:text-2xs mb-1.5 text-(--text2)">
                  SE {h.week} · {h.date_range}
                </div>

                <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-2xs font-semibold text-(--fc-on) bg-(--fc-fg)">
                  <span className="w-1.5 h-1.5 rounded-full bg-current/40" />
                  {name}
                </div>

                <div className="text-[9px] md:text-2xs mt-1.5 text-text3 font-features-['tnum']">
                  {formatNumber(h.lo95)} - {formatNumber(h.hi95)}
                </div>

                <div className="hidden md:block text-[9px] text-text3">urgencias est.</div>
              </div>
            );
          })}
        </div>
      </Card>
    </section>
  );
}
