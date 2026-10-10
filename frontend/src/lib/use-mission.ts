"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { Snapshot } from "./types";

export function useMission(missionId: string) {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const refresh = useCallback(async () => {
    try {
      const next = await api<Snapshot>(`/missions/${missionId}`);
      setSnapshot(next);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Mission service unavailable",
      );
    } finally {
      setLoading(false);
    }
  }, [missionId]);
  useEffect(() => {
    let active = true;
    api<Snapshot>(`/missions/${missionId}`)
      .then((next) => {
        if (active) {
          setSnapshot(next);
          setError(null);
        }
      })
      .catch((err) => {
        if (active)
          setError(
            err instanceof Error ? err.message : "Mission service unavailable",
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [missionId]);
  return {
    snapshot: snapshot?.mission.id === missionId ? snapshot : null,
    error,
    loading: loading || (!error && snapshot?.mission.id !== missionId),
    refresh,
  };
}
