import type { WeekData, RegionIndex } from "@/lib/types";
import { CausesTable } from "@/components/sections/CausesTable";
import { AgeGroupPanel } from "@/components/sections/AgeGroupPanel";
import { RegionLevelSummary } from "@/components/sections/RegionLevelSummary";

interface CausesSectionProps {
  current: WeekData;
  regionIndex: RegionIndex | null;
}

export function CausesSection({ current, regionIndex }: CausesSectionProps) {
  return (
    <section aria-label="Desglose por causa y grupo etario">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 items-stretch">
        <CausesTable causes={current.by_cause} />

        <div className="flex flex-col gap-3">
          <AgeGroupPanel ageGroups={current.by_age} />
          {regionIndex && <RegionLevelSummary regionIndex={regionIndex} />}
        </div>
      </div>
    </section>
  );
}
