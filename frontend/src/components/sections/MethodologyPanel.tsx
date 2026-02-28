import type React from "react";
import type { AlertLevel } from "@/lib/types";
import { LEVEL_COLOR, LEVEL_BG } from "@/lib/colors";
import { Collapsible } from "@/components/ui/Collapsible";

const METHODOLOGY = [
  {
    title: "Fuente de datos",
    text: "Atenciones de urgencia respiratoria, DEIS/MINSAL. Clasificación CIE-10. Cobertura nacional desde 2008.",
  },
  { title: "Cálculo de nivel", text: "Observado vs mediana misma semana epidemiológica 2017-2023." },
  { title: "Modelo predictivo", text: "LightGBM cuantílico. MAPE 1-2 sem: ±15-20%, 3-4 sem: ±25-35%." },
  { title: "Limitaciones", text: "Correlación estadística. No incorpora datos virológicos ni climáticos." },
];

const THRESHOLDS: { label: string; desc: string; level: AlertLevel }[] = [
  { label: "Verde", desc: "< +10%", level: "green" },
  { label: "Amarillo", desc: "+10-25%", level: "yellow" },
  { label: "Naranjo", desc: "+25-50%", level: "orange" },
  { label: "Rojo", desc: "> +50%", level: "red" },
];

export function MethodologyPanel() {
  return (
    <Collapsible title="Metodología y fuentes">
      <div className="grid grid-cols-2 gap-2.5 mb-3.5">
        {METHODOLOGY.map((item) => (
          <div key={item.title} className="p-3 rounded bg-(--background) border border-border-light">
            <div className="text-2xs font-semibold text-(--nhs-blue) mb-0.75">{item.title}</div>
            <p className="m-0 text-xs text-(--text2) leading-[1.6]">{item.text}</p>
          </div>
        ))}
      </div>
      <div className="text-2xs font-semibold text-text3 mb-1.5">Umbrales de nivel</div>
      <div className="grid grid-cols-4 gap-1">
        {THRESHOLDS.map((t) => (
          <div
            key={t.label}
            className="py-1.5 px-0 text-center rounded border border-(--th-fg)/13 bg-(--th-bg)"
            style={{ "--th-fg": LEVEL_COLOR[t.level], "--th-bg": LEVEL_BG[t.level] } as React.CSSProperties}
          >
            <div className="text-xs font-bold text-(--th-fg)">{t.label}</div>
            <div className="text-[9px] text-(--text2) mt-px">{t.desc}</div>
          </div>
        ))}
      </div>
    </Collapsible>
  );
}
