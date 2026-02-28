import type { CauseData } from "@/lib/types";
import { formatNumber } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { SectionTitle } from "@/components/ui/SectionTitle";
import { Caption } from "@/components/ui/Caption";
import { VariationBadge } from "@/components/ui/VariationBadge";

function MiniBar({ value, max }: { value: number; max: number }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div aria-hidden="true" className="w-6 h-1.5 bg-border-light rounded-[2px] overflow-hidden shrink-0">
      <div className="h-full bg-(--nhs-blue) rounded-[2px] transition-[width] duration-300 ease-in-out" style={{ width: `${pct}%` }} />
    </div>
  );
}

export function CausesTable({ causes }: { causes: CauseData[] }) {
  if (!causes || causes.length === 0) {
    return (
      <Card className="p-4">
        <SectionTitle>Causas de consulta respiratoria</SectionTitle>
        <Caption>Sin datos de causas disponibles.</Caption>
      </Card>
    );
  }

  let maxObs = 1;
  for (const c of causes) if (c.total > maxObs) maxObs = c.total;

  return (
    <Card className="p-0 overflow-hidden h-full flex flex-col">
      <div className="px-4 pt-4">
        <SectionTitle>Causas de consulta respiratoria</SectionTitle>
      </div>

      <div className="overflow-x-auto [-webkit-overflow-scrolling:touch] flex-1">
        <table role="table" aria-label="Urgencias respiratorias por causa diagnóstica" className="w-full border-collapse min-w-105">
          <thead>
            <tr>
              <th
                scope="col"
                className="py-1.5 px-2.5 text-2xs font-semibold text-text3 tracking-[0.4px] uppercase border-b-2 border-(--border) whitespace-nowrap bg-surface text-left pl-4"
              >
                Causa
              </th>
              <th
                scope="col"
                className="py-1.5 px-2.5 text-2xs font-semibold text-text3 tracking-[0.4px] uppercase border-b-2 border-(--border) whitespace-nowrap bg-surface text-right"
              >
                Obs.
              </th>
              <th
                scope="col"
                className="py-1.5 px-2.5 text-2xs font-semibold text-text3 tracking-[0.4px] uppercase border-b-2 border-(--border) whitespace-nowrap bg-surface text-right"
              >
                Esperado
              </th>
              <th
                scope="col"
                className="py-1.5 px-2.5 text-2xs font-semibold text-text3 tracking-[0.4px] uppercase border-b-2 border-(--border) whitespace-nowrap bg-surface text-right"
              >
                O/E
              </th>
              <th
                scope="col"
                className="py-1.5 px-2.5 text-2xs font-semibold text-text3 tracking-[0.4px] uppercase border-b-2 border-(--border) whitespace-nowrap bg-surface text-right pr-4"
              >
                Var.
              </th>
            </tr>
          </thead>
          <tbody>
            {causes.map((cause) => (
              <tr key={cause.name} className="bg-surface even:bg-surface-alt">
                <td className="py-2 px-2.5 text-xs text-text1 align-middle border-b border-border-light whitespace-nowrap text-left pl-4">
                  <div className="flex items-center gap-2">
                    <MiniBar value={cause.total} max={maxObs} />
                    <span className="font-medium text-text1 whitespace-normal wrap-break-word min-w-0">{cause.name}</span>
                  </div>
                </td>
                <td className="py-2 px-2.5 text-xs text-text1 align-middle border-b border-border-light whitespace-nowrap text-right font-features-['tnum'] font-semibold">
                  {formatNumber(cause.total)}
                </td>
                <td className="py-2 px-2.5 text-xs text-text3 align-middle border-b border-border-light whitespace-nowrap text-right font-features-['tnum']">
                  {formatNumber(cause.baseline)}
                </td>
                <td className="py-2 px-2.5 text-xs text-text1 align-middle border-b border-border-light whitespace-nowrap text-right">
                  <span className="text-3xs text-(--text2) bg-(--background) py-0.5 px-1 rounded-[3px] font-features-['tnum']">
                    {cause.oe.toFixed(2)}
                  </span>
                </td>
                <td className="py-2 px-2.5 text-xs text-text1 align-middle border-b border-border-light whitespace-nowrap text-right pr-4">
                  <VariationBadge value={cause.change_pct} level={cause.color} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="py-2 px-4 pb-3 text-3xs text-text3 border-t border-border-light">
        Fuente: DEIS/MINSAL · CIE-10 · Mediana referencia 2017-2023
      </div>
    </Card>
  );
}
