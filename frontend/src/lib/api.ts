const DEMO_KEY = "marsense-guest-token";
const WORKSPACE_KEY = "marsense-personal-workspace";
const DEMO_VIEWS = new Set(["/mission", "/astronaut", "/evidence", "/memory", "/comparison"]);

export function guestToken(): string | null {
  return typeof window === "undefined" ? null : sessionStorage.getItem(DEMO_KEY);
}

export function clearGuestDemo() {
  sessionStorage.removeItem(DEMO_KEY);
}

export function workspaceMode() {
  return typeof window !== "undefined" && sessionStorage.getItem(WORKSPACE_KEY) === "1";
}

export function clearWorkspaceMode() {
  sessionStorage.removeItem(WORKSPACE_KEY);
}

export function enterWorkspace() {
  clearGuestDemo();
  sessionStorage.setItem(WORKSPACE_KEY, "1");
  sessionStorage.setItem("marsense-mission", "eva-01");
}

export async function launchGuestDemo() {
  const previous = guestToken();
  if (previous) {
    const response = await fetch("/api/public-demo/auth/session", {
      headers: { "X-Marsense-Demo": previous }, cache: "no-store",
    });
    if (response.ok) {
      clearWorkspaceMode();
      return;
    }
    if (response.status !== 401) {
      throw new Error("Your mission is temporarily unavailable. Retry to resume it.");
    }
    clearGuestDemo();
  }
  const result = await api<{ token: string }>("/public-demo/start", jsonRequest({}));
  if (typeof result.token !== "string" || result.token.length !== 43) {
    throw new Error("The mission service returned an invalid session. Please retry.");
  }
  clearWorkspaceMode();
  sessionStorage.setItem(DEMO_KEY, result.token);
  sessionStorage.setItem("marsense-mission", "eva-01");
}

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const token = guestToken();
  const useGuest = token && typeof window !== "undefined" &&
    DEMO_VIEWS.has(window.location.pathname.replace(/\/$/, "")) &&
    !path.startsWith("/public-demo/") &&
    (path.startsWith("/missions/") || path.startsWith("/evidence/") ||
      path.startsWith("/observations/") || path === "/auth/session" ||
      path === "/auth/logout" || path === "/showcase/reset");
  const useWorkspace = !useGuest && workspaceMode() &&
    DEMO_VIEWS.has(window.location.pathname.replace(/\/$/, "")) &&
    (path.startsWith("/missions/") || path.startsWith("/evidence/") ||
      path.startsWith("/observations/") || path === "/auth/session" || path === "/auth/logout");
  const prefix = useGuest ? "/public-demo" : useWorkspace ?
    (path.startsWith("/auth/") ? "/workspaces" : "/workspaces/data") : "";
  const headers = useGuest ? new Headers(options?.headers) : undefined;
  if (headers && token) headers.set("X-Marsense-Demo", token);
  const response = await fetch(`/api${prefix}${path}`, {
    ...options,
    ...(headers ? { headers } : {}),
    cache: "no-store",
  });
  if (!response.ok) {
    const content = (await response.json().catch(() => null)) as {
      detail?: unknown;
    } | null;
    throw new Error(
      typeof content?.detail === "string"
        ? content.detail
        : "The mission service is unavailable. Saved evidence remains on the backend. Retry when connected.",
    );
  }
  return response.json() as Promise<T>;
}
export const jsonRequest = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});
export function label(value: string): string {
  return value
    .toLowerCase()
    .replaceAll("_", " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
