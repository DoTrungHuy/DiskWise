import type {
  AIClassifyResponse,
  AIHealth,
  AIRenameResponse,
  DuplicateGroup,
  ExecutionResult,
  FileRecord,
  ModelTask,
  Operation,
  Overview,
  PermissionSnapshot,
  Plan
} from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    ...init
  });
  if (!response.ok) {
    let message = `请求失败：${response.status}`;
    try {
      const body = await response.json();
      message = body.detail ?? message;
    } catch {
      // Keep the HTTP status fallback.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export const api = {
  overview: () => request<Overview>("/api/overview"),
  files: (params: { query?: string; category?: string; extension?: string } = {}) => {
    const search = new URLSearchParams();
    if (params.query) search.set("query", params.query);
    if (params.category) search.set("category", params.category);
    if (params.extension) search.set("extension", params.extension);
    return request<{ files: FileRecord[] }>(`/api/files?${search.toString()}`);
  },
  scan: (path: string) =>
    request<{ count: number; path: string }>("/api/scan", {
      method: "POST",
      body: JSON.stringify({ path })
    }),
  extract: (fileId: number) =>
    request<{
      ok: boolean;
      content_preview: string;
      error: string | null;
    }>(`/api/files/${fileId}/extract`, { method: "POST" }),
  search: (query: string) =>
    request<{ files: FileRecord[] }>(
      `/api/search?${new URLSearchParams({ query }).toString()}`
    ),
  duplicates: () => request<{ groups: DuplicateGroup[] }>("/api/duplicates"),
  createCategoryPlan: (targetRoot: string) =>
    request<{ planId: number; suggestions: unknown[] }>("/api/plans/category", {
      method: "POST",
      body: JSON.stringify({ targetRoot })
    }),
  latestPlans: () => request<{ plans: Plan[] }>("/api/plans/latest"),
  executePlan: (planId: number, selectedItemIds: number[], confirmation: string) =>
    request<{ results: ExecutionResult[] }>(`/api/plans/${planId}/execute`, {
      method: "POST",
      body: JSON.stringify({ selectedItemIds, confirmation })
    }),
  activity: () => request<{ operations: Operation[] }>("/api/activity"),
  undo: (operationId: number, confirmation: string) =>
    request<{ result: ExecutionResult }>(`/api/activity/${operationId}/undo`, {
      method: "POST",
      body: JSON.stringify({ confirmation })
    }),
  models: () => request<{ tasks: ModelTask[] }>("/api/settings/models"),
  permissions: () => request<PermissionSnapshot>("/api/permissions"),
  updatePermission: (capability: string, enabled: boolean) =>
    request<PermissionSnapshot>(`/api/permissions/${capability}`, {
      method: "PATCH",
      body: JSON.stringify({ enabled })
    }),
  aiHealth: () => request<AIHealth>("/api/ai/health"),
  classify: (fileId: number, cloudConsent = false) =>
    request<AIClassifyResponse>("/api/ai/classify", {
      method: "POST",
      body: JSON.stringify({ fileId, cloudConsent })
    }),
  rename: (fileId: number, cloudConsent = false) =>
    request<AIRenameResponse>("/api/ai/rename", {
      method: "POST",
      body: JSON.stringify({ fileId, cloudConsent })
    })
};
