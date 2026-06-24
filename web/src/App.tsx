import {
  Activity,
  AlertTriangle,
  Archive,
  Bot,
  CheckCircle2,
  Cloud,
  Database,
  FileSearch,
  FolderOpen,
  History,
  Layers3,
  Lock,
  Play,
  RefreshCw,
  RotateCcw,
  Search,
  Settings,
  ShieldCheck,
  Sparkles
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { api } from "./api";
import type {
  AIHealth,
  CapabilityPermission,
  DuplicateGroup,
  FileRecord,
  ModelTask,
  Operation,
  Overview,
  PermissionSnapshot,
  Plan
} from "./types";
import "./App.css";

type View =
  | "dashboard"
  | "library"
  | "ai"
  | "search"
  | "plans"
  | "permissions"
  | "activity"
  | "settings";
type ConfirmIntent = "execute" | "undo" | null;

const views: Array<{ id: View; label: string; icon: typeof Database }> = [
  { id: "dashboard", label: "总览", icon: Database },
  { id: "library", label: "资料库", icon: Archive },
  { id: "ai", label: "AI", icon: Bot },
  { id: "search", label: "搜索", icon: FileSearch },
  { id: "plans", label: "计划", icon: Layers3 },
  { id: "permissions", label: "权限", icon: ShieldCheck },
  { id: "activity", label: "活动", icon: History },
  { id: "settings", label: "设置", icon: Settings }
];

const emptyPermissions: PermissionSnapshot = {
  cloudEnvEnabled: false,
  permissions: []
};

const emptyOverview: Overview = {
  fileCount: 0,
  scanRoots: [],
  categoryCounts: [],
  extensionCounts: [],
  duplicateGroupCount: 0,
  latestPlan: null,
  ai: [],
  permissions: emptyPermissions
};

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [overview, setOverview] = useState<Overview>(emptyOverview);
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [operations, setOperations] = useState<Operation[]>([]);
  const [models, setModels] = useState<ModelTask[]>([]);
  const [permissions, setPermissions] = useState<PermissionSnapshot>(emptyPermissions);
  const [aiHealth, setAiHealth] = useState<AIHealth | null>(null);
  const [duplicates, setDuplicates] = useState<DuplicateGroup[]>([]);
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null);
  const [selectedPlanIds, setSelectedPlanIds] = useState<number[]>([]);
  const [scanPath, setScanPath] = useState("");
  const [targetRoot, setTargetRoot] = useState("");
  const [libraryQuery, setLibraryQuery] = useState("");
  const [libraryCategory, setLibraryCategory] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [cloudConsent, setCloudConsent] = useState(false);
  const [aiResult, setAiResult] = useState("选择一个资料库文件后，可以运行 AI 分类或生成命名建议。");
  const [notice, setNotice] = useState("本地工作台就绪");
  const [busy, setBusy] = useState(false);
  const [confirmIntent, setConfirmIntent] = useState<ConfirmIntent>(null);
  const [confirmText, setConfirmText] = useState("");
  const [undoOperationId, setUndoOperationId] = useState<number | null>(null);

  const selectedFile = useMemo(
    () => files.find((file) => file.id === selectedFileId) ?? files[0],
    [files, selectedFileId]
  );
  const latestPlan = plans[0] ?? overview.latestPlan;
  const pendingItems = latestPlan?.items.filter((item) => item.status === "pending") ?? [];

  useEffect(() => {
    refreshAll();
  }, []);

  async function refreshAll() {
    setBusy(true);
    try {
      const [overviewData, filesData, plansData, activityData, modelData, permissionData] =
        await Promise.all([
          api.overview(),
          api.files(),
          api.latestPlans(),
          api.activity(),
          api.models(),
          api.permissions()
        ]);
      setOverview(overviewData);
      setFiles(filesData.files);
      setPlans(plansData.plans);
      setOperations(activityData.operations);
      setModels(modelData.tasks);
      setPermissions(permissionData);
      setNotice("状态已刷新");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "刷新失败");
    } finally {
      setBusy(false);
    }
  }

  async function runScan() {
    if (!scanPath.trim()) return;
    setBusy(true);
    try {
      const result = await api.scan(scanPath.trim());
      setNotice(`扫描完成：${result.count} 个文件`);
      await refreshAll();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "扫描失败");
    } finally {
      setBusy(false);
    }
  }

  async function filterLibrary() {
    setBusy(true);
    try {
      const result = await api.files({
        query: libraryQuery,
        category: libraryCategory
      });
      setFiles(result.files);
      setNotice(`资料库显示 ${result.files.length} 个文件`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "筛选失败");
    } finally {
      setBusy(false);
    }
  }

  async function extractSelectedFile() {
    if (!selectedFile) return;
    setBusy(true);
    try {
      const result = await api.extract(selectedFile.id);
      setNotice(result.ok ? "摘要已保存" : result.error ?? "摘要提取受限");
      await filterLibrary();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "提取失败");
    } finally {
      setBusy(false);
    }
  }

  async function runAIHealth() {
    setBusy(true);
    try {
      const result = await api.aiHealth();
      setAiHealth(result);
      setPermissions(result.permissions);
      setNotice("模型服务检测完成");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "模型检测失败");
    } finally {
      setBusy(false);
    }
  }

  async function classifySelectedFile() {
    if (!selectedFile) return;
    setBusy(true);
    try {
      const result = await api.classify(selectedFile.id, cloudConsent);
      setAiResult(
        `分类：${result.category}\n建议名称：${result.suggestedName}\n置信度：${result.confidence.toFixed(2)}\n${result.reason}`
      );
      setNotice("AI 分类完成");
      await filterLibrary();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "AI 分类失败");
    } finally {
      setBusy(false);
    }
  }

  async function renameSelectedFile() {
    if (!selectedFile) return;
    setBusy(true);
    try {
      const result = await api.rename(selectedFile.id, cloudConsent);
      setAiResult(`建议名称：${result.suggestedName}\n${result.reason}`);
      setNotice("命名建议已生成");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "命名建议失败");
    } finally {
      setBusy(false);
    }
  }

  async function runKeywordSearch() {
    setBusy(true);
    try {
      const result = await api.search(searchQuery);
      setFiles(result.files);
      setView("library");
      setNotice(`搜索命中 ${result.files.length} 个文件`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "搜索失败");
    } finally {
      setBusy(false);
    }
  }

  async function loadDuplicates() {
    setBusy(true);
    try {
      const result = await api.duplicates();
      setDuplicates(result.groups);
      setNotice(`找到 ${result.groups.length} 组重复文件`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "重复文件检测失败");
    } finally {
      setBusy(false);
    }
  }

  async function createPlan() {
    if (!targetRoot.trim()) return;
    setBusy(true);
    try {
      const result = await api.createCategoryPlan(targetRoot.trim());
      setNotice(`计划 #${result.planId} 已生成`);
      await refreshAll();
      setView("plans");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "计划生成失败");
    } finally {
      setBusy(false);
    }
  }

  async function updatePermission(capability: string, enabled: boolean) {
    setBusy(true);
    try {
      const snapshot = await api.updatePermission(capability, enabled);
      setPermissions(snapshot);
      setNotice("权限已更新");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "权限更新失败");
    } finally {
      setBusy(false);
    }
  }

  function togglePlanItem(itemId: number) {
    setSelectedPlanIds((current) =>
      current.includes(itemId)
        ? current.filter((id) => id !== itemId)
        : [...current, itemId]
    );
  }

  async function confirmAction() {
    if (confirmIntent === "execute" && latestPlan) {
      setBusy(true);
      try {
        const ids = selectedPlanIds.length ? selectedPlanIds : pendingItems.map((item) => item.id);
        const result = await api.executePlan(latestPlan.id, ids, confirmText);
        setNotice(`执行完成：${result.results.filter((item) => item.status === "succeeded").length} 项成功`);
        setConfirmIntent(null);
        setConfirmText("");
        setSelectedPlanIds([]);
        await refreshAll();
      } catch (error) {
        setNotice(error instanceof Error ? error.message : "执行失败");
      } finally {
        setBusy(false);
      }
    }
    if (confirmIntent === "undo" && undoOperationId !== null) {
      setBusy(true);
      try {
        await api.undo(undoOperationId, confirmText);
        setNotice("撤销完成");
        setConfirmIntent(null);
        setConfirmText("");
        setUndoOperationId(null);
        await refreshAll();
      } catch (error) {
        setNotice(error instanceof Error ? error.message : "撤销失败");
      } finally {
        setBusy(false);
      }
    }
  }

  function beginUndo(operationId: number) {
    setUndoOperationId(operationId);
    setConfirmIntent("undo");
    setConfirmText("");
  }

  return (
    <div className="shell">
      <aside className="sidebar" aria-label="主导航">
        <div className="brand">
          <ShieldCheck size={26} />
          <div>
            <strong>DiskWise</strong>
            <span>本地文件工作台</span>
          </div>
        </div>
        <nav>
          {views.map((item) => {
            const Icon = item.icon;
            return (
              <button
                className={view === item.id ? "nav-item active" : "nav-item"}
                key={item.id}
                onClick={() => setView(item.id)}
                type="button"
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <span className="eyeline">127.0.0.1 only</span>
            <h1>{views.find((item) => item.id === view)?.label}</h1>
          </div>
          <div className="top-actions">
            <span className={busy ? "status busy" : "status"}>{notice}</span>
            <button className="icon-button" onClick={refreshAll} type="button" aria-label="刷新">
              <RefreshCw size={18} />
            </button>
          </div>
        </header>

        {view === "dashboard" && (
          <Dashboard
            overview={overview}
            permissions={permissions}
            scanPath={scanPath}
            setScanPath={setScanPath}
            runScan={runScan}
            targetRoot={targetRoot}
            setTargetRoot={setTargetRoot}
            createPlan={createPlan}
          />
        )}
        {view === "library" && (
          <Library
            files={files}
            selectedFile={selectedFile}
            selectedFileId={selectedFileId}
            setSelectedFileId={setSelectedFileId}
            query={libraryQuery}
            setQuery={setLibraryQuery}
            category={libraryCategory}
            setCategory={setLibraryCategory}
            categories={overview.categoryCounts.map((item) => item.category ?? "")}
            onFilter={filterLibrary}
            onExtract={extractSelectedFile}
          />
        )}
        {view === "ai" && (
          <AIView
            files={files}
            selectedFile={selectedFile}
            selectedFileId={selectedFileId}
            setSelectedFileId={setSelectedFileId}
            cloudConsent={cloudConsent}
            setCloudConsent={setCloudConsent}
            aiResult={aiResult}
            aiHealth={aiHealth}
            models={models}
            permissions={permissions}
            onHealth={runAIHealth}
            onClassify={classifySelectedFile}
            onRename={renameSelectedFile}
          />
        )}
        {view === "search" && (
          <SearchView
            query={searchQuery}
            setQuery={setSearchQuery}
            onKeyword={runKeywordSearch}
            onDuplicates={loadDuplicates}
            duplicates={duplicates}
          />
        )}
        {view === "plans" && (
          <PlansView
            plan={latestPlan}
            selectedPlanIds={selectedPlanIds}
            togglePlanItem={togglePlanItem}
            onExecute={() => {
              setConfirmIntent("execute");
              setConfirmText("");
            }}
          />
        )}
        {view === "permissions" && (
          <PermissionsView
            permissions={permissions.permissions}
            cloudEnvEnabled={permissions.cloudEnvEnabled}
            onToggle={updatePermission}
          />
        )}
        {view === "activity" && <ActivityView operations={operations} onUndo={beginUndo} />}
        {view === "settings" && <SettingsView models={models} />}
      </main>

      {confirmIntent && (
        <div className="modal-backdrop" role="presentation">
          <section className="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
            <div className="modal-icon">
              <AlertTriangle size={24} />
            </div>
            <h2 id="confirm-title">{confirmIntent === "execute" ? "确认执行计划" : "确认撤销操作"}</h2>
            <p>
              请输入 <strong>EXECUTE</strong> 后继续。DiskWise 会记录操作日志，并为可逆操作保留撤销数据。
            </p>
            <input
              autoFocus
              value={confirmText}
              onChange={(event) => setConfirmText(event.target.value)}
              placeholder="EXECUTE"
            />
            <div className="modal-actions">
              <button type="button" onClick={() => setConfirmIntent(null)}>
                取消
              </button>
              <button
                className="danger"
                disabled={confirmText !== "EXECUTE" || busy}
                onClick={confirmAction}
                type="button"
              >
                <Play size={16} />
                确认
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

function Dashboard({
  overview,
  permissions,
  scanPath,
  setScanPath,
  runScan,
  targetRoot,
  setTargetRoot,
  createPlan
}: {
  overview: Overview;
  permissions: PermissionSnapshot;
  scanPath: string;
  setScanPath: (value: string) => void;
  runScan: () => void;
  targetRoot: string;
  setTargetRoot: (value: string) => void;
  createPlan: () => void;
}) {
  return (
    <section className="dashboard-grid">
      <Metric label="已索引文件" value={overview.fileCount} icon={Database} />
      <Metric label="扫描目录" value={overview.scanRoots.length} icon={FolderOpen} />
      <Metric label="重复分组" value={overview.duplicateGroupCount} icon={Layers3} />
      <Metric label="AI 任务" value={overview.ai.filter((task) => task.enabled).length} icon={Bot} />

      <section className="panel span-2">
        <div className="panel-heading">
          <h2>扫描</h2>
          <span>只读索引</span>
        </div>
        <div className="path-row">
          <input value={scanPath} onChange={(event) => setScanPath(event.target.value)} placeholder="D:\\Downloads" />
          <button onClick={runScan} type="button">
            <FolderOpen size={16} />
            扫描
          </button>
        </div>
        <ul className="compact-list">
          {overview.scanRoots.length === 0 && <li>还没有授权扫描目录</li>}
          {overview.scanRoots.map((root) => (
            <li key={root.id}>
              <span>{root.path}</span>
              <small>{root.last_scanned_at ?? "尚未扫描"}</small>
            </li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>分类分布</h2>
        </div>
        <BarList items={overview.categoryCounts.map((item) => ({ label: item.category ?? "未分类", count: item.count }))} />
      </section>

      <section className="panel span-2">
        <div className="panel-heading">
          <h2>整理计划</h2>
          <span>{overview.latestPlan?.status ?? "暂无"}</span>
        </div>
        <div className="path-row">
          <input value={targetRoot} onChange={(event) => setTargetRoot(event.target.value)} placeholder="D:\\Organized" />
          <button onClick={createPlan} type="button">
            <Layers3 size={16} />
            生成
          </button>
        </div>
        <p className="muted">最新计划：{overview.latestPlan ? `${overview.latestPlan.items.length} 项` : "暂无"}</p>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>权限状态</h2>
        </div>
        <PermissionMiniList permissions={permissions.permissions} />
      </section>
    </section>
  );
}

function Metric({ label, value, icon: Icon }: { label: string; value: number; icon: typeof Database }) {
  return (
    <section className="metric">
      <Icon size={20} />
      <span>{label}</span>
      <strong>{value}</strong>
    </section>
  );
}

function BarList({ items }: { items: Array<{ label: string; count: number }> }) {
  const max = Math.max(...items.map((item) => item.count), 1);
  if (!items.length) return <p className="muted">暂无数据</p>;
  return (
    <div className="bar-list">
      {items.map((item) => (
        <div className="bar-row" key={item.label}>
          <span>{item.label}</span>
          <div>
            <i style={{ width: `${(item.count / max) * 100}%` }} />
          </div>
          <strong>{item.count}</strong>
        </div>
      ))}
    </div>
  );
}

function PermissionMiniList({ permissions }: { permissions: CapabilityPermission[] }) {
  if (!permissions.length) return <p className="muted">权限快照尚未加载</p>;
  return (
    <div className="mini-list">
      {permissions.slice(0, 5).map((permission) => (
        <div key={permission.capability}>
          <span>{permission.label}</span>
          <strong>{permission.effectiveEnabled ? "启用" : "关闭"}</strong>
        </div>
      ))}
    </div>
  );
}

function Library({
  files,
  selectedFile,
  selectedFileId,
  setSelectedFileId,
  query,
  setQuery,
  category,
  setCategory,
  categories,
  onFilter,
  onExtract
}: {
  files: FileRecord[];
  selectedFile: FileRecord | undefined;
  selectedFileId: number | null;
  setSelectedFileId: (id: number) => void;
  query: string;
  setQuery: (value: string) => void;
  category: string;
  setCategory: (value: string) => void;
  categories: string[];
  onFilter: () => void;
  onExtract: () => void;
}) {
  return (
    <section className="split">
      <div className="panel table-panel">
        <div className="toolbar">
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="文件名、分类、摘要" />
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">全部分类</option>
            {categories.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <button onClick={onFilter} type="button">
            <Search size={16} />
            筛选
          </button>
        </div>
        <FileTable files={files} selectedFileId={selectedFileId} onSelect={setSelectedFileId} />
      </div>
      <aside className="panel inspector">
        <div className="panel-heading">
          <h2>检查器</h2>
          {selectedFile?.exists ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
        </div>
        {selectedFile ? (
          <>
            <strong>{selectedFile.name}</strong>
            <dl>
              <dt>分类</dt>
              <dd>{selectedFile.category ?? "未分类"}</dd>
              <dt>大小</dt>
              <dd>{formatBytes(selectedFile.size)}</dd>
              <dt>路径</dt>
              <dd>{selectedFile.path}</dd>
            </dl>
            <button onClick={onExtract} type="button">
              <FileSearch size={16} />
              提取摘要
            </button>
            <p className="preview">{selectedFile.contentPreview ?? "暂无摘要"}</p>
          </>
        ) : (
          <p className="muted">选择一个文件查看详情</p>
        )}
      </aside>
    </section>
  );
}

function FileTable({
  files,
  selectedFileId,
  onSelect
}: {
  files: FileRecord[];
  selectedFileId: number | null;
  onSelect: (id: number) => void;
}) {
  return (
    <table>
      <thead>
        <tr>
          <th>文件</th>
          <th>分类</th>
          <th>大小</th>
          <th>状态</th>
        </tr>
      </thead>
      <tbody>
        {files.length === 0 && (
          <tr>
            <td colSpan={4}>暂无文件</td>
          </tr>
        )}
        {files.map((file) => (
          <tr className={selectedFileId === file.id ? "selected" : ""} key={file.id} onClick={() => onSelect(file.id)}>
            <td>
              <strong>{file.name}</strong>
              <small>{file.path}</small>
            </td>
            <td>{file.category ?? "未分类"}</td>
            <td>{formatBytes(file.size)}</td>
            <td>{file.exists ? "存在" : "失联"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function AIView({
  files,
  selectedFile,
  selectedFileId,
  setSelectedFileId,
  cloudConsent,
  setCloudConsent,
  aiResult,
  aiHealth,
  models,
  permissions,
  onHealth,
  onClassify,
  onRename
}: {
  files: FileRecord[];
  selectedFile: FileRecord | undefined;
  selectedFileId: number | null;
  setSelectedFileId: (id: number) => void;
  cloudConsent: boolean;
  setCloudConsent: (value: boolean) => void;
  aiResult: string;
  aiHealth: AIHealth | null;
  models: ModelTask[];
  permissions: PermissionSnapshot;
  onHealth: () => void;
  onClassify: () => void;
  onRename: () => void;
}) {
  const cloudPermission = permissions.permissions.find((item) => item.capability === "cloud_ai");
  return (
    <section className="split">
      <div className="panel table-panel">
        <div className="panel-heading">
          <h2>AI 任务</h2>
          <span>{cloudPermission?.effectiveEnabled ? "云端已授权" : "本地优先"}</span>
        </div>
        <div className="toolbar">
          <select value={selectedFileId ?? ""} onChange={(event) => setSelectedFileId(Number(event.target.value))}>
            <option value="">选择文件</option>
            {files.map((file) => (
              <option key={file.id} value={file.id}>
                {file.name}
              </option>
            ))}
          </select>
          <button disabled={!selectedFile} onClick={onClassify} type="button">
            <Sparkles size={16} />
            AI 分类
          </button>
          <button disabled={!selectedFile} onClick={onRename} type="button">
            <Bot size={16} />
            命名建议
          </button>
          <button onClick={onHealth} type="button">
            <RefreshCw size={16} />
            检测模型
          </button>
        </div>
        <label className="inline-check">
          <input checked={cloudConsent} onChange={(event) => setCloudConsent(event.target.checked)} type="checkbox" />
          本次允许云端 AI
        </label>
        <pre className="result-box">{aiResult}</pre>
      </div>
      <aside className="panel inspector">
        <div className="panel-heading">
          <h2>模型状态</h2>
          <Cloud size={18} />
        </div>
        <div className="mini-list">
          {models.map((model) => (
            <div key={model.task}>
              <span>{model.label}</span>
              <strong>{model.enabled ? model.modelName ?? "未选择" : "关闭"}</strong>
            </div>
          ))}
        </div>
        {aiHealth && (
          <div className="health-list">
            {aiHealth.providers.map((provider) => (
              <p key={provider.provider}>
                <strong>{provider.provider}</strong>
                <span>{provider.healthy ? "可用" : "不可用"} - {provider.message}</span>
              </p>
            ))}
          </div>
        )}
      </aside>
    </section>
  );
}

function SearchView({
  query,
  setQuery,
  onKeyword,
  onDuplicates,
  duplicates
}: {
  query: string;
  setQuery: (value: string) => void;
  onKeyword: () => void;
  onDuplicates: () => void;
  duplicates: DuplicateGroup[];
}) {
  return (
    <section className="panel stack">
      <div className="search-modes">
        <div>
          <h2>关键词</h2>
          <div className="path-row">
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="找上学期 SQL 实验报告" />
            <button onClick={onKeyword} type="button">
              <Search size={16} />
              搜索
            </button>
          </div>
        </div>
        <div>
          <h2>重复文件</h2>
          <button onClick={onDuplicates} type="button">
            <Layers3 size={16} />
            检测重复文件
          </button>
        </div>
        <div className="disabled-mode">
          <h2>语义搜索</h2>
          <p>等待向量索引</p>
        </div>
      </div>
      <div className="duplicate-list">
        {duplicates.length === 0 && <p className="muted">暂无重复文件分组</p>}
        {duplicates.map((group) => (
          <section className="duplicate-group" key={group.hash}>
            <header>
              <strong>{group.records.length} 个文件</strong>
              <span>{formatBytes(group.wastedBytes)} 可清理</span>
            </header>
            {group.records.map((record) => (
              <div className="duplicate-file" key={record.id}>
                <span>{record.name}</span>
                <small>{record.path}</small>
              </div>
            ))}
          </section>
        ))}
      </div>
    </section>
  );
}

function PlansView({
  plan,
  selectedPlanIds,
  togglePlanItem,
  onExecute
}: {
  plan: Plan | null | undefined;
  selectedPlanIds: number[];
  togglePlanItem: (id: number) => void;
  onExecute: () => void;
}) {
  if (!plan) return <section className="panel empty-state">暂无整理计划</section>;
  const pending = plan.items.filter((item) => item.status === "pending");
  return (
    <section className="panel table-panel">
      <div className="panel-heading">
        <div>
          <h2>{plan.title}</h2>
          <span>#{plan.id} - {plan.status}</span>
        </div>
        <button disabled={pending.length === 0} onClick={onExecute} type="button">
          <Play size={16} />
          执行所选
        </button>
      </div>
      <table>
        <thead>
          <tr>
            <th>选择</th>
            <th>动作</th>
            <th>原路径</th>
            <th>目标路径</th>
            <th>风险</th>
          </tr>
        </thead>
        <tbody>
          {plan.items.map((item) => (
            <tr key={item.id}>
              <td>
                <input
                  checked={selectedPlanIds.includes(item.id)}
                  disabled={item.status !== "pending"}
                  onChange={() => togglePlanItem(item.id)}
                  type="checkbox"
                />
              </td>
              <td>{item.action}</td>
              <td>{item.sourcePath}</td>
              <td>{item.targetPath}</td>
              <td>
                {!item.sourceExists && <span className="badge warn">源失联</span>}
                {item.targetExists && <span className="badge soft">冲突改名</span>}
                {item.status !== "pending" && <span className="badge">{item.status}</span>}
                {item.sourceExists && !item.targetExists && item.status === "pending" && <span className="badge ok">可执行</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function PermissionsView({
  permissions,
  cloudEnvEnabled,
  onToggle
}: {
  permissions: CapabilityPermission[];
  cloudEnvEnabled: boolean;
  onToggle: (capability: string, enabled: boolean) => void;
}) {
  return (
    <section className="panel permission-grid">
      <div className="panel-heading">
        <div>
          <h2>本地授权中心</h2>
          <span>云端环境变量：{cloudEnvEnabled ? "已启用" : "未启用"}</span>
        </div>
      </div>
      {permissions.map((permission) => (
        <article className="permission-row" key={permission.capability}>
          <div>
            <strong>{permission.label}</strong>
            <p>{permission.description}</p>
            <span className={permission.effectiveEnabled ? "badge ok" : "badge warn"}>{permission.reason}</span>
            {permission.requiresConfirmation && <span className="badge soft">需要 EXECUTE</span>}
          </div>
          <label className="switch">
            <input
              checked={permission.enabled}
              disabled={permission.locked}
              onChange={(event) => onToggle(permission.capability, event.target.checked)}
              type="checkbox"
            />
            <span>{permission.locked ? <Lock size={14} /> : permission.enabled ? "启用" : "关闭"}</span>
          </label>
        </article>
      ))}
    </section>
  );
}

function ActivityView({ operations, onUndo }: { operations: Operation[]; onUndo: (id: number) => void }) {
  return (
    <section className="panel table-panel">
      <table>
        <thead>
          <tr>
            <th>时间</th>
            <th>动作</th>
            <th>来源</th>
            <th>目标</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {operations.length === 0 && (
            <tr>
              <td colSpan={6}>暂无操作日志</td>
            </tr>
          )}
          {operations.map((operation) => (
            <tr key={operation.id}>
              <td>{operation.createdAt}</td>
              <td>{operation.action}</td>
              <td>{operation.sourcePath}</td>
              <td>{operation.targetPath ?? ""}</td>
              <td>{operation.status}</td>
              <td>
                <button disabled={!operation.canUndo} onClick={() => onUndo(operation.id)} type="button">
                  <RotateCcw size={16} />
                  撤销
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function SettingsView({ models }: { models: ModelTask[] }) {
  return (
    <section className="panel settings-list">
      {models.map((model) => (
        <article key={model.task}>
          <div>
            <strong>{model.label}</strong>
            <span>{model.provider}</span>
          </div>
          <p>{model.modelName ?? "未选择模型"}</p>
          <span className={model.enabled ? "badge ok" : "badge"}>{model.enabled ? "启用" : "关闭"}</span>
        </article>
      ))}
      {models.length === 0 && <p className="muted">暂无模型配置</p>}
    </section>
  );
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  if (value < 1024 * 1024 * 1024) return `${(value / 1024 / 1024).toFixed(1)} MB`;
  return `${(value / 1024 / 1024 / 1024).toFixed(1)} GB`;
}
