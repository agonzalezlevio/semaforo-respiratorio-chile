import { useState, useEffect } from "react";
import { fetchAlertData, fetchForecast } from "../lib/api";
import type { AlertData, ForecastData } from "../lib/types";

export function useAlertData(regionCode: number | null = null) {
  const [alertData, setAlertData] = useState<AlertData | null>(null);
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stale = false;

    setLoading(true);
    setError(null);
    setForecast(null);

    fetchAlertData(regionCode ?? undefined)
      .then((alert) => {
        if (!stale) setAlertData(alert);
      })
      .catch((err) => {
        if (!stale) setError(err.message);
      })
      .finally(() => {
        if (!stale) setLoading(false);
      });

    if (regionCode === null) {
      fetchForecast()
        .then((data) => {
          if (!stale) setForecast(data);
        })
        .catch(() => null);
    }

    return () => {
      stale = true;
    };
  }, [regionCode]);

  return { alertData, forecast, loading, error };
}
