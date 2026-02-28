import type { AgeData } from "@/lib/types";
import { formatNumber } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { SectionTitle } from "@/components/ui/SectionTitle";
import { VariationBadge } from "@/components/ui/VariationBadge";

export function AgeGroupPanel({ ageGroups }: { ageGroups: AgeData[] }) {
  if (!ageGroups || ageGroups.length === 0) return null;

  return (
    <Card className="p-4">
      <SectionTitle>Grupos etarios</SectionTitle>
      <div className="flex flex-col gap-2.25">
        {ageGroups.map((ag) => {
          const barPct = Math.min(Math.abs(ag.change_pct), 100);

          return (
            <div key={ag.group}>
              <div className="flex justify-between items-baseline mb-1 gap-2">
                <span className="text-xs font-medium text-text1">{ag.group}</span>
                <VariationBadge value={ag.change_pct} level={ag.color} />
              </div>

              <div
                role="progressbar"
                aria-label={`${ag.group}: ${ag.change_pct.toFixed(1)}% variación`}
                aria-valuenow={barPct}
                aria-valuemin={0}
                aria-valuemax={100}
                className="h-1.25 bg-border-light rounded-[3px] overflow-hidden"
              >
                <div className="h-full bg-(--nhs-blue) rounded-[3px]" style={{ width: `${barPct}%` }} />
              </div>

              <div className="mt-0.75 text-3xs text-text3 font-features-['tnum']">
                {formatNumber(ag.total)} obs. · esperado {formatNumber(ag.baseline)}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
