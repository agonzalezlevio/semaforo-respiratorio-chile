import type { ReactNode } from "react";

export function SectionTitle({ children }: { children: ReactNode }) {
  return <h2 className="text-[17px] font-semibold text-text1 leading-[1.3] mt-0 mb-3.5">{children}</h2>;
}
