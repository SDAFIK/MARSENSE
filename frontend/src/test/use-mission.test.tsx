import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useMission } from "@/lib/use-mission";

type PendingRequest = {
  signal?: AbortSignal | null;
  resolve: (response: Response) => void;
};

function deferredFetch() {
  const requests: PendingRequest[] = [];
  const mock = vi.fn((_input: RequestInfo | URL, init?: RequestInit) =>
    new Promise<Response>((resolve) => {
      requests.push({ signal: init?.signal, resolve });
    }),
  );
  vi.stubGlobal("fetch", mock);
  return { requests, mock };
}

function missionResponse(id: string) {
  return new Response(JSON.stringify({ mission: { id } }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("Mission request isolation", () => {
  it("ignores a previous mission response even when the server ignores cancellation", async () => {
    const { requests } = deferredFetch();
    const { result, rerender } = renderHook(
      ({ id }) => useMission(id),
      { initialProps: { id: "eva-01" } },
    );

    await waitFor(() => expect(requests).toHaveLength(1));
    rerender({ id: "eva-02" });
    await waitFor(() => expect(requests).toHaveLength(2));
    expect(requests[0].signal?.aborted).toBe(true);

    await act(async () => requests[1].resolve(missionResponse("eva-02")));
    await waitFor(() =>
      expect(result.current.snapshot?.mission.id).toBe("eva-02"),
    );

    await act(async () => requests[0].resolve(missionResponse("eva-01")));
    expect(result.current.snapshot?.mission.id).toBe("eva-02");
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("does not allow a stale manual refresh to overwrite a newer mission", async () => {
    const { requests } = deferredFetch();
    const { result, rerender } = renderHook(
      ({ id }) => useMission(id),
      { initialProps: { id: "eva-01" } },
    );

    await waitFor(() => expect(requests).toHaveLength(1));
    await act(async () => requests[0].resolve(missionResponse("eva-01")));
    const oldRefresh = result.current.refresh;

    act(() => { void oldRefresh(); });
    await waitFor(() => expect(requests).toHaveLength(2));
    rerender({ id: "eva-02" });
    await waitFor(() => expect(requests).toHaveLength(3));
    await act(async () => requests[2].resolve(missionResponse("eva-02")));
    await act(async () => requests[1].resolve(missionResponse("eva-01")));

    expect(requests[1].signal?.aborted).toBe(true);
    expect(result.current.snapshot?.mission.id).toBe("eva-02");

    await act(async () => { expect(await oldRefresh()).toBe(false); });
    expect(requests).toHaveLength(3);
    expect(result.current.snapshot?.mission.id).toBe("eva-02");
  });

  it("retains the last known state after a failed refresh and clears the error on retry", async () => {
    const { requests } = deferredFetch();
    const { result } = renderHook(() => useMission("eva-01"));

    await waitFor(() => expect(requests).toHaveLength(1));
    await act(async () => requests[0].resolve(missionResponse("eva-01")));

    act(() => { void result.current.refresh(); });
    await waitFor(() => expect(requests).toHaveLength(2));
    await act(async () =>
      requests[1].resolve(new Response(JSON.stringify({ detail: "Offline" }), {
        status: 503,
        headers: { "Content-Type": "application/json" },
      })),
    );
    expect(result.current.snapshot?.mission.id).toBe("eva-01");
    expect(result.current.error).toBe("Offline");
    expect(result.current.loading).toBe(false);

    act(() => { void result.current.refresh(); });
    await waitFor(() => expect(requests).toHaveLength(3));
    await act(async () => requests[2].resolve(missionResponse("eva-01")));
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });
});
