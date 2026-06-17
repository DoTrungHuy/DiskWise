export type FileRecord = {
  id: number;
  path: string;
  name: string;
  extension: string;
  size: number;
  modifiedAt: number;
  category: string | null;
  contentPreview: string | null;
  quickHash: string | null;
  fullHash: string | null;
  status: string;
  exists: boolean;
};

export type CountItem = {
  category?: string;
  extension?: string;
  count: number;
};

export type PlanItem = {
  id: number;
  planId: number;
  fileId: number;
  action: string;
  sourcePath: string;
  targetPath: string;
  sourceExists: boolean;
  targetExists: boolean;
  suggestedName: string | null;
  category: string | null;
  reason: string | null;
  status: string;
};

export type Plan = {
  id: number;
  title: string;
  status: string;
  items: PlanItem[];
};

export type Operation = {
  id: number;
  planItemId: number | null;
  action: string;
  sourcePath: string;
  targetPath: string | null;
  undoData: string | null;
  status: string;
  createdAt: string;
  canUndo: boolean;
};

export type ModelTask = {
  task: string;
  label: string;
  provider: string;
  modelName: string | null;
  enabled: boolean;
  cloudEnabled: boolean;
};

export type Overview = {
  fileCount: number;
  scanRoots: Array<{ id: number; path: string; last_scanned_at?: string | null }>;
  categoryCounts: CountItem[];
  extensionCounts: CountItem[];
  duplicateGroupCount: number;
  latestPlan: Plan | null;
  ai: ModelTask[];
};

export type DuplicateGroup = {
  hash: string;
  records: FileRecord[];
  wastedBytes: number;
};

export type ExecutionResult = {
  item_id: number;
  operation_id: number | null;
  status: string;
  message: string;
  target_path: string | null;
};
