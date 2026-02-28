import { Activity } from "lucide-react";

export function AppHeader() {
  return (
    <header className="shrink-0 bg-blue-dark z-40" aria-label="Encabezado principal">
      <div className="flex items-center h-12 px-5 max-w-330 mx-auto gap-3.5">
        <div className="w-7 h-7 rounded bg-header-bg shrink-0 flex items-center justify-center">
          <Activity size={16} strokeWidth={2.5} className="text-white" />
        </div>
        <div className="min-w-0">
          <h1 className="text-sm font-semibold text-white leading-tight overflow-hidden text-ellipsis whitespace-nowrap m-0">
            Semáforo de Vigilancia Respiratoria
          </h1>
          <div className="text-3xs text-header-muted">Vigilancia epidemiológica · Datos DEIS/MINSAL</div>
        </div>
      </div>
    </header>
  );
}
