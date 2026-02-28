import { useMemo } from "react";
import { ResponsiveContainer, ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import type { ForecastData, WeekData } from "@/lib/types";
import { palette } from "@/lib/colors";
import { GRID, X_AXIS, Y_AXIS, CHART_MARGIN } from "@/lib/chart-theme";
import { buildForecastChart } from "@/lib/data-transforms";
import { formatNumber } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { SectionTitle } from "@/components/ui/SectionTitle";
import { Caption } from "@/components/ui/Caption";
import { ChartLegend } from "@/components/ui/ChartLegend";
import { ChartTooltip } from "@/components/ui/ChartTooltip";

const PROJECTION_LEGEND = [
  { color: palette.text1, label: "Observado", dashed: false },
  { color: palette.blue, label: "Proyectado", dashed: true },
];

export function ProjectionCard({ forecast, timeseries }: { forecast: ForecastData; timeseries: WeekData[] }) {
  const chartData = useMemo(() => buildForecastChart(forecast, timeseries), [forecast, timeseries]);

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-2 mb-0 flex-wrap">
        <div>
          <SectionTitle>Proyección a 4 semanas</SectionTitle>
          <Caption className="mb-3">
            LightGBM cuantílico · IC 95%{" "}
            <span className="text-3xs font-medium text-trend-up bg-warning-light py-0.5 px-1.5 rounded-[3px]">±15-35%</span>
          </Caption>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <ComposedChart data={chartData} margin={CHART_MARGIN}>
          <CartesianGrid {...GRID} vertical={false} />
          <XAxis
            dataKey="week"
            {...X_AXIS}
            tickFormatter={(v: number) => `SE ${v}`}
            interval={Math.max(0, Math.floor(chartData.length / 5) - 1)}
            padding={{ left: 4, right: 4 }}
          />
          <YAxis {...Y_AXIS} tickFormatter={(v: number) => formatNumber(v)} width={56} />
          <Tooltip content={<ChartTooltip excludeKeys={["range"]} />} />

          <Area
            type="monotone"
            dataKey="range"
            name="IC 95%"
            stroke="none"
            fill={`${palette.blue}22`}
            connectNulls
            activeDot={false}
            legendType="none"
          />

          <Line type="monotone" dataKey="observed" name="Observado" stroke={palette.text1} strokeWidth={2} dot={false} connectNulls />

          <Line
            type="monotone"
            dataKey="projected"
            name="Proyectado"
            stroke={palette.blue}
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={false}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>

      <ChartLegend items={PROJECTION_LEGEND} />
    </Card>
  );
}
