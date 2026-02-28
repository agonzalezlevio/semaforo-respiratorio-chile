import { useMemo } from "react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import type { WeekData } from "@/lib/types";
import { palette } from "@/lib/colors";
import { GRID, X_AXIS, Y_AXIS, CHART_MARGIN } from "@/lib/chart-theme";
import { buildTimeSeriesChart } from "@/lib/data-transforms";
import { formatNumber } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { SectionTitle } from "@/components/ui/SectionTitle";
import { Caption } from "@/components/ui/Caption";
import { ChartLegend } from "@/components/ui/ChartLegend";
import { ChartTooltip } from "@/components/ui/ChartTooltip";

export function WeeklyTrendCard({ timeseries }: { timeseries: WeekData[] }) {
  const chartData = useMemo(() => buildTimeSeriesChart(timeseries), [timeseries]);

  const years = useMemo(() => {
    const set = new Set(timeseries.map((t) => t.year));
    return Array.from(set).sort((a, b) => a - b);
  }, [timeseries]);

  const lastYear = years[years.length - 2] ?? null;
  const currentYear = years[years.length - 1] ?? null;

  const lineData = useMemo(() => {
    const byWeek = new Map<number, Record<string, unknown>>();

    for (const point of chartData) {
      const key = point.week;
      if (!byWeek.has(key)) byWeek.set(key, { week: key });
      const row = byWeek.get(key)!;
      row.median = point.median;
      (row as Record<string, unknown>)[String(point.year)] = point.observed;
      if (point.year === currentYear) row.date_range = point.date_range;
    }

    return Array.from(byWeek.values()).sort((a, b) => (a.week as number) - (b.week as number));
  }, [chartData, currentYear]);

  let captionText: string;
  if (lastYear && currentYear) {
    captionText = `${lastYear}, ${currentYear} vs mediana histórica`;
  } else if (currentYear) {
    captionText = `${currentYear} vs mediana histórica`;
  } else {
    captionText = "vs mediana histórica";
  }

  const legendItems = useMemo(
    () => [
      { color: palette.border, label: "Mediana", dashed: true },
      ...(lastYear ? [{ color: palette.text3, label: String(lastYear), dashed: false }] : []),
      ...(currentYear ? [{ color: palette.blue, label: String(currentYear), dashed: false }] : []),
    ],
    [lastYear, currentYear],
  );

  return (
    <Card className="p-5">
      <SectionTitle>Tendencia semanal de urgencias</SectionTitle>
      <Caption className="mb-3">{captionText}</Caption>

      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={lineData} margin={CHART_MARGIN}>
          <CartesianGrid {...GRID} vertical={false} />
          <XAxis
            dataKey="week"
            {...X_AXIS}
            tickFormatter={(v: number) => `SE ${v}`}
            interval={Math.floor(lineData.length / 6)}
            padding={{ left: 4, right: 4 }}
          />
          <YAxis {...Y_AXIS} tickFormatter={(v: number) => formatNumber(v)} width={56} />
          <Tooltip content={<ChartTooltip />} />

          <Line
            type="monotone"
            dataKey="median"
            name="Mediana"
            stroke={palette.border}
            strokeWidth={1.5}
            strokeDasharray="4 3"
            dot={false}
            connectNulls
          />

          {lastYear && (
            <Line
              type="monotone"
              dataKey={String(lastYear)}
              name={String(lastYear)}
              stroke={palette.text3}
              strokeWidth={1.5}
              dot={false}
              connectNulls
            />
          )}

          {currentYear && (
            <Line
              type="monotone"
              dataKey={String(currentYear)}
              name={String(currentYear)}
              stroke={palette.blue}
              strokeWidth={2.5}
              dot={false}
              connectNulls
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      <ChartLegend items={legendItems} />
    </Card>
  );
}
