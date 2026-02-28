export function formatNumber(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "-";
  return Math.round(n).toLocaleString("es-CL");
}

export function formatPct(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "-";
  const sign = n > 0 ? "+" : "";
  return `${sign}${n.toFixed(1)}%`;
}
