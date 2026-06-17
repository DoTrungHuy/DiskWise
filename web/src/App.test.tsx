import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const file = {
  id: 1,
  path: "D:\\Downloads\\database-lab.txt",
  name: "database-lab.txt",
  extension: ".txt",
  size: 24,
  modifiedAt: 1,
  category: "文档",
  contentPreview: null,
  quickHash: null,
  fullHash: null,
  status: "active",
  exists: true
};

const plan = {
  id: 7,
  title: "按分类整理文件",
  status: "draft",
  items: [
    {
      id: 11,
      planId: 7,
      fileId: 1,
      action: "move",
      sourcePath: "D:\\Downloads\\database-lab.txt",
      targetPath: "D:\\Organized\\文档\\database-lab.txt",
      sourceExists: true,
      targetExists: false,
      suggestedName: "database-lab.txt",
      category: "文档",
      reason: "根据分类移动",
      status: "pending"
    }
  ]
};

function json(body: unknown, ok = true, status = 200) {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(body)
  } as Response);
}

function installFetchMock() {
  let scanned = false;
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.startsWith("/api/overview")) {
      return json({
        fileCount: scanned ? 1 : 0,
        scanRoots: scanned ? [{ id: 1, path: "D:\\Downloads", last_scanned_at: "now" }] : [],
        categoryCounts: scanned ? [{ category: "文档", count: 1 }] : [],
        extensionCounts: scanned ? [{ extension: ".txt", count: 1 }] : [],
        duplicateGroupCount: scanned ? 1 : 0,
        latestPlan: plan,
        ai: [{ task: "classification", label: "文件分类", provider: "ollama", modelName: "gemma4:e2b", enabled: true, cloudEnabled: false }]
      });
    }
    if (url.startsWith("/api/files")) {
      return json({ files: scanned ? [file] : [] });
    }
    if (url.startsWith("/api/plans/latest")) {
      return json({ plans: [plan] });
    }
    if (url.startsWith("/api/activity")) {
      return json({ operations: [] });
    }
    if (url.startsWith("/api/settings/models")) {
      return json({ tasks: [] });
    }
    if (url.startsWith("/api/scan") && init?.method === "POST") {
      scanned = true;
      return json({ count: 1, path: "D:\\Downloads" });
    }
    if (url.startsWith("/api/duplicates")) {
      return json({
        groups: [{ hash: "abc", records: [file, { ...file, id: 2, name: "copy.txt" }], wastedBytes: 24 }]
      });
    }
    return json({ detail: "not found" }, false, 404);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("DiskWise web workbench", () => {
  beforeEach(() => {
    installFetchMock();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders the dashboard empty state", async () => {
    render(<App />);

    expect(await screen.findByText("Indexed files")).toBeInTheDocument();
    expect(screen.getByText("还没有授权扫描目录")).toBeInTheDocument();
  });

  it("shows scanned files in the library", async () => {
    const user = userEvent.setup();
    render(<App />);

    await screen.findByText("Indexed files");
    await user.type(screen.getAllByRole("textbox")[0], "D:\\Downloads");
    await user.click(screen.getByRole("button", { name: "扫描" }));
    await user.click(screen.getByRole("button", { name: /Library/i }));

    expect((await screen.findAllByText("database-lab.txt")).length).toBeGreaterThan(0);
  });

  it("shows duplicate groups from the search mode", async () => {
    const user = userEvent.setup();
    render(<App />);

    await screen.findByText("Indexed files");
    await user.click(screen.getByRole("button", { name: /Search/i }));
    await user.click(screen.getByRole("button", { name: "检测重复文件" }));

    expect(await screen.findByText("2 files")).toBeInTheDocument();
    expect(screen.getByText("copy.txt")).toBeInTheDocument();
  });

  it("blocks plan execution without the confirmation word", async () => {
    const user = userEvent.setup();
    render(<App />);

    await screen.findByText("Indexed files");
    await user.click(screen.getByRole("button", { name: /Plans/i }));
    await user.click(screen.getByRole("button", { name: "执行所选" }));

    const confirm = await screen.findByRole("button", { name: "确认" });
    expect(confirm).toBeDisabled();
  });
});
