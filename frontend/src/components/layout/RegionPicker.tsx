import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { RegionIndex, RegionInfo } from "@/lib/types";
import { LevelDot } from "@/components/ui/LevelDot";
import { VariationBadge } from "@/components/ui/VariationBadge";

interface RegionPickerProps {
  regionIndex: RegionIndex;
  selectedCode: number | null;
  onRegionChange: (code: number | null) => void;
}

function ScrollEdgeButton({ direction, visible, onClick }: { direction: -1 | 1; visible: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      aria-label={direction < 0 ? "Anterior" : "Siguiente"}
      tabIndex={-1}
      data-dir={direction < 0 ? "left" : "right"}
      data-visible={visible || undefined}
      className="absolute top-0 bottom-0 z-3 w-7 border-none cursor-pointer p-0 flex items-center justify-center text-base font-bold text-(--text2) bg-surface transition-opacity duration-150
                 opacity-0 pointer-events-none data-visible:opacity-100 data-visible:pointer-events-auto
                 data-[dir=left]:left-0 data-[dir=right]:right-0"
    >
      {direction < 0 ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
    </button>
  );
}

export function RegionPicker({ regionIndex, selectedCode, onRegionChange }: RegionPickerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const regionMap = useMemo(() => {
    const map = new Map<number, RegionInfo>();
    for (const r of regionIndex.regions) map.set(r.code, r);
    return map;
  }, [regionIndex.regions]);

  const sorted = useMemo(
    () => [...regionIndex.regions].sort((a: RegionInfo, b: RegionInfo) => a.name.localeCompare(b.name, "es")),
    [regionIndex.regions],
  );

  const chips = useMemo<Array<{ code: number | null; label: string }>>(
    () => [{ code: null, label: "Nacional" }, ...sorted.map((r) => ({ code: r.code, label: r.name }))],
    [sorted],
  );

  const selectedIndex = useMemo(() => chips.findIndex((c) => c.code === selectedCode), [chips, selectedCode]);

  const updateScrollState = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    setCanScrollLeft(el.scrollLeft > 2);
    setCanScrollRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 2);
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    updateScrollState();
    el.addEventListener("scroll", updateScrollState, { passive: true });
    const ro = new ResizeObserver(updateScrollState);
    ro.observe(el);
    return () => {
      el.removeEventListener("scroll", updateScrollState);
      ro.disconnect();
    };
  }, [updateScrollState]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const chip = el.querySelectorAll<HTMLButtonElement>('[role="tab"]')[selectedIndex];
    if (chip) chip.scrollIntoView({ block: "nearest", inline: "nearest" });
  }, [selectedIndex]);

  const scroll = (direction: -1 | 1) => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollBy({ left: direction * 160, behavior: "smooth" });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    const total = chips.length;
    if (e.key === "ArrowRight") {
      e.preventDefault();
      onRegionChange(chips[(selectedIndex + 1) % total].code);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      onRegionChange(chips[(selectedIndex - 1 + total) % total].code);
    }
  };

  return (
    <nav aria-label="Seleccionar región" className="relative">
      <div className="relative overflow-hidden">
        <ScrollEdgeButton direction={-1} visible={canScrollLeft} onClick={() => scroll(-1)} />

        <div
          ref={scrollRef}
          role="tablist"
          aria-label="Regiones"
          onKeyDown={handleKeyDown}
          className="scrollbar-hide flex gap-1.5 overflow-x-auto px-9 py-2"
        >
          {chips.map((chip) => {
            const isSelected = chip.code === selectedCode;
            const info = chip.code !== null ? (regionMap.get(chip.code) ?? null) : null;

            return (
              <button
                key={chip.code ?? "nacional"}
                role="tab"
                aria-selected={isSelected}
                tabIndex={isSelected ? 0 : -1}
                onClick={() => onRegionChange(chip.code)}
                className="inline-flex items-center gap-1.25 shrink-0 py-1.25 px-2.5 min-h-8 rounded text-xs cursor-pointer whitespace-nowrap leading-[1.3] transition-[border-color,background,color] duration-100
                border border-(--border) bg-surface text-text1 font-normal
                aria-selected:border-[1.5px] aria-selected:border-(--nhs-blue) aria-selected:bg-blue-light aria-selected:text-(--nhs-blue) aria-selected:font-semibold"
              >
                {info && <LevelDot level={info.color} size={7} />}
                {chip.label}
                {info && info.change_pct !== null && <VariationBadge value={info.change_pct} level={info.color} />}
              </button>
            );
          })}
        </div>

        <ScrollEdgeButton direction={1} visible={canScrollRight} onClick={() => scroll(1)} />
      </div>
    </nav>
  );
}
