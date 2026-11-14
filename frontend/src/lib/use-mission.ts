"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { Snapshot } from "./types";

type MissionState = {
  missionId: string;
  snapshot: Snapshot | null;
  error: string | null;
  loading: boolean;
};

const emptyState = (missionId: string): MissionState => ({
  missionId,
  snapshot: null,
  error: null,
  loading: true,
});

export function useMission(missionId: string) {
  const [state, setState] = useState<MissionState>(() => emptyState(missionId));
  const activeMission = useRef<string | null>(missionId);
  const activeRequest = useRef<AbortController | null>(null);

  const load = useCallback(async (id: string, retry: boolean) => {
    // An action started under a previous EVA must not replace the new EVA.
    if (activeMission.current !== id) return false;

    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;

    if (retry) {
      setState((previous) => ({
        ...(previous.missionId === id ? previous : emptyState(id)),
        error: null,
        loading: true,
      }));
    }

    const isCurrent = () =>
      activeMission.current === id &&
      activeRequest.current === controller &&
      !controller.signal.aborted;

    try {
      const next = await api<Snapshot>(`/missions/${id}`, {
        signal: controller.signal,
      });

      if (!isCurrent()) return false;
      if (next.mission.id !== id) {
        throw new Error("The mission service returned an unexpected mission.");
      }

      setState({ missionId: id, snapshot: next, error: null, loading: false });
      return true;
    } catch (error) {
      if (!isCurrent()) return false;
      setState((previous) => ({
        missionId: id,
        snapshot: previous.missionId === id ? previous.snapshot : null,
        error:
          error instanceof Error ? error.message : "Mission service unavailable",
        loading: false,
      }));
      return false;
    }
  }, []);

  const refresh = useCallback(() => load(missionId, true), [load, missionId]);

  useEffect(() => {
    activeMission.current = missionId;
    void load(missionId, false);

    return () => {
      activeMission.current = null;
      activeRequest.current?.abort();
      activeRequest.current = null;
    };
  }, [load, missionId]);

  // Do not show a different EVA's snapshot or error while switching missions.
  const current = state.missionId === missionId ? state : emptyState(missionId);

  return { ...current, refresh };
}
