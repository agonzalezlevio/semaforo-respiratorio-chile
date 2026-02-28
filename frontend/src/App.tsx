import { useState, useEffect } from "react";
import { useAlertData } from "@/hooks/useAlertData";
import { useRegionParam } from "@/hooks/useRegionParam";
import { fetchRegionIndex } from "@/lib/api";
import type { RegionIndex } from "@/lib/types";
import { AppHeader } from "@/components/layout/AppHeader";
import { Dashboard } from "@/components/layout/Dashboard";
import { RegionPicker } from "@/components/layout/RegionPicker";
import { ScrollArea } from "@/components/ui/ScrollArea";

export function App() {
  const [regionCode, setRegionCode] = useRegionParam();
  const [regionIndex, setRegionIndex] = useState<RegionIndex | null>(null);
  const { alertData, forecast, loading, error } = useAlertData(regionCode);

  useEffect(() => {
    fetchRegionIndex()
      .then(setRegionIndex)
      .catch(() => null);
  }, []);

  let regionName: string | null = null;
  if (regionCode !== null && regionIndex) {
    regionName = regionIndex.regions.find((r) => r.code === regionCode)?.name ?? null;
  }

  if (loading) {
    return (
      <div className="min-h-dvh bg-(--background) flex items-center justify-center">
        <div className="text-center" role="status" aria-live="polite">
          <div className="w-10 h-10 border-4 border-border-light border-t-(--nhs-blue) rounded-full mx-auto mb-4 animate-spin" aria-hidden="true" />
          <p className="text-[13px] text-(--text2) m-0">Cargando datos…</p>
        </div>
      </div>
    );
  }

  if (error || !alertData) {
    return (
      <div className="min-h-dvh bg-(--background) flex items-center justify-center">
        <div role="alert" className="bg-error-light border border-destructive/25 rounded p-8 text-center max-w-100">
          <p className="font-bold text-destructive mb-2 text-[15px] m-0">Error cargando datos</p>
          <p className="text-[13px] text-(--text2) m-0">{error ?? "No se pudieron cargar los datos."}</p>
        </div>
      </div>
    );
  }

  const { current, timeseries, referenceYears } = alertData;

  return (
    <div className="h-dvh flex flex-col bg-(--background) text-text1 overflow-hidden">
      <a href="#main-content" className="skip-link">
        Saltar al contenido
      </a>

      <AppHeader />

      {regionIndex && (
        <div className="shrink-0 border-b border-(--border) bg-surface">
          <RegionPicker regionIndex={regionIndex} selectedCode={regionCode} onRegionChange={setRegionCode} />
        </div>
      )}

      <ScrollArea className="flex-1 min-h-0">
        <main id="main-content" className="px-5 pt-4 pb-10 max-w-330 mx-auto">
          <Dashboard
            current={current}
            timeseries={timeseries}
            forecast={forecast}
            regionName={regionName}
            referenceYears={referenceYears}
            regionIndex={regionIndex}
          />
        </main>
      </ScrollArea>
    </div>
  );
}
