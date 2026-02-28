import { useState, useEffect, useCallback } from "react";

const PARAM = "region";

function readParam(): number | null {
  const v = new URLSearchParams(window.location.search).get(PARAM);
  if (v === null) return null;
  const n = parseInt(v, 10);
  return Number.isFinite(n) ? n : null;
}

function writeParam(code: number | null) {
  const url = new URL(window.location.href);
  if (code === null) {
    url.searchParams.delete(PARAM);
  } else {
    url.searchParams.set(PARAM, String(code));
  }
  window.history.pushState(null, "", url);
}

export function useRegionParam(): [number | null, (code: number | null) => void] {
  const [code, setCode] = useState<number | null>(readParam);

  const setRegion = useCallback((next: number | null) => {
    setCode(next);
    writeParam(next);
  }, []);

  // Sync state when user navigates with back/forward
  useEffect(() => {
    const onPop = () => setCode(readParam());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  return [code, setRegion];
}
