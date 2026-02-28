import { useMemo } from "react";
import { ResponsiveContainer, ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from "recharts";
import { palette } from "@/lib/colors";
import { GRID, X_AXIS, Y_AXIS, CHART_MARGIN } from "@/lib/chart-theme";
import { Collapsible } from "@/components/ui/Collapsible";
import { ChartLegend } from "@/components/ui/ChartLegend";
import { ChartTooltip } from "@/components/ui/ChartTooltip";
import type { WeekData } from "@/lib/types";

const CAUSE_KEYS = [
  { pattern: /bronq/i, key: "bronq", label: "Bronquitis", color: palette.chart2 },
  { pattern: /otra/i, key: "otra", label: "Otra resp.", color: palette.chart3 },
  { pattern: /neum/i, key: "neum", label: "Neumonía", color: palette.chart1 },
] as const;

interface CompositionRow {
  se: number;
  date_range: string;
  bronq: number | null;
  otra: number | null;
  neum: number | null;
}

function buildChartData(timeseries: WeekData[]): CompositionRow[] {
  return timeseries.map((w) => {
    const row: CompositionRow = { se: w.week, date_range: w.date_range, bronq: null, otra: null, neum: null };
    for (const { pattern, key } of CAUSE_KEYS) {
      const cause = w.by_cause.find((c) => pattern.test(c.name));
      if (cause) {
        row[key] = Math.round(cause.z_score * 100) / 100;
      }
    }
    return row;
  });
}

const formatZScore = (v: number) => v.toFixed(2);

export function CompositionPanel({ timeseries }: { timeseries: WeekData[] }) {
  const data = useMemo(() => buildChartData(timeseries), [timeseries]);

  return (
    <Collapsible title="Composición por causa - Sobre umbral estadístico">
      <ResponsiveContainer width="100%" height={180}>
        <ComposedChart data={data} margin={CHART_MARGIN}>
          <CartesianGrid {...GRID} />
          <XAxis dataKey="se" {...X_AXIS} padding={{ left: 4, right: 4 }} />
          <YAxis {...Y_AXIS} />
          <Tooltip content={<ChartTooltip formatValue={formatZScore} />} />
          <Line type="monotone" dataKey="bronq" stroke={palette.chart2} strokeWidth={1.5} dot={false} name="Bronquitis" connectNulls />
          <Line type="monotone" dataKey="otra" stroke={palette.chart3} strokeWidth={1.5} dot={false} name="Otra resp." connectNulls />
          <Line type="monotone" dataKey="neum" stroke={palette.chart1} strokeWidth={1.5} dot={false} name="Neumonía" connectNulls />
          <ReferenceLine y={2} stroke={palette.red} strokeDasharray="4 3" strokeWidth={1} />
        </ComposedChart>
      </ResponsiveContainer>
      <ChartLegend
        items={[
          { color: palette.chart2, label: "Bronquitis" },
          { color: palette.chart3, label: "Otra resp." },
          { color: palette.chart1, label: "Neumonía" },
          { color: palette.red, label: "Umbral", dashed: true },
        ]}
      />
    </Collapsible>
  );
}
