import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { enterWorkspace, guestToken, launchGuestDemo, workspaceMode } from "./api";

const token = "a".repeat(43);
const nextToken = "b".repeat(43);
function response(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status });
}

describe("guest mission entry", () => {
  beforeEach(() => sessionStorage.clear());
  afterEach(() => vi.unstubAllGlobals());

  it("preserves the current workspace when guest start fails", async () => {
    enterWorkspace();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(403, { detail: "Origin rejected" })));
    await expect(launchGuestDemo()).rejects.toThrow("Origin rejected");
    expect(workspaceMode()).toBe(true);
    expect(guestToken()).toBeNull();
  });

  it("preserves an existing guest when the service is temporarily unavailable", async () => {
    sessionStorage.setItem("marsense-guest-token", token);
    const fetcher = vi.fn().mockResolvedValue(response(503, {}));
    vi.stubGlobal("fetch", fetcher);
    await expect(launchGuestDemo()).rejects.toThrow("temporarily unavailable");
    expect(guestToken()).toBe(token);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("resumes a valid existing session without allocating another guest", async () => {
    sessionStorage.setItem("marsense-guest-token", token);
    const fetcher = vi.fn().mockResolvedValue(response(200, {}));
    vi.stubGlobal("fetch", fetcher);
    await launchGuestDemo();
    expect(guestToken()).toBe(token);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("replaces an expired session and starts EVA-01", async () => {
    sessionStorage.setItem("marsense-guest-token", token);
    sessionStorage.setItem("marsense-mission", "eva-02");
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(response(401, {}))
      .mockResolvedValueOnce(response(201, { token: nextToken })));
    await launchGuestDemo();
    expect(guestToken()).toBe(nextToken);
    expect(sessionStorage.getItem("marsense-mission")).toBe("eva-01");
  });

  it("rejects malformed successful responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(201, { token: "bad" })));
    await expect(launchGuestDemo()).rejects.toThrow("invalid session");
    expect(guestToken()).toBeNull();
  });
});
