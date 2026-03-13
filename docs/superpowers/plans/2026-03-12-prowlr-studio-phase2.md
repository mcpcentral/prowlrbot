# Prowlr-Studio Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the Agent Workspace (4 stub tabs → real), implement 4 missing layout modes, rebuild Chat/Channels/Settings/Monitors/Cron pages in Studio, add Canvas annotation/export, and add the 5 ProwlrBot workflow node types.

**Architecture:** Frontend-heavy. The Python backend SSE stream (`/api/studio/agents/{id}/stream`) and autonomy API already exist. Studio backend NestJS adds a `/api/prowlrbot/*` proxy service. Most work is React/TypeScript in `prowrl-studio/frontend/src/`.

**Tech Stack:** React 19 / TypeScript / Tailwind / Radix/shadcn / xterm.js / ReactFlow / Zustand (frontend); NestJS / Bun (studio backend); FastAPI (prowlrbot backend at :8088)

**Repos:**
- Studio: `/home/anon/dev/prowrl-studio/`
- ProwlrBot: `/home/anon/dev/prowlrbot/`

**Spec:** `docs/superpowers/specs/2026-03-11-prowlr-studio-design.md` (sections 4, 6, 7)

**Phase 1 delivered:** Screen, Terminal, Code, Reasoning, Tools, Cost, Logs, Chat tabs. Tile + Stack layout modes. CollaborationCanvas (approve/reject only). AgentHub. ProwlrBot JWT auth. Rebranding + security fixes.

**Phase 2 delivers:**
1. 4 remaining workspace tabs: Browser, Files, Memory, Config
2. 4 remaining layout modes: Float, Split, PiP, Focus
3. 5 console pages rebuilt in Studio: Chat, Channels, Settings, Monitors, Cron
4. Canvas annotation, redirect, merge, export
5. 5 ProwlrBot ReactFlow workflow node types

---

## Chunk 1: Workspace Tab — Browser View

The Browser tab shows the agent's Playwright browser. SSE `browser_screenshot` events carry `{ url, png_base64, width, height }`. "Take Control" posts to `/api/studio/agents/{id}/autonomy` with `level: "watch"`.

### Task 1.1: BrowserTab component

**Files:**
- Create: `frontend/src/components/workspace/tabs/BrowserTab.tsx`
- Modify: `frontend/src/pages/AgentWorkspacePage.tsx` (remove PlaceholderTab for Browser)

- [x] **Step 1: Create BrowserTab**

```tsx
// frontend/src/components/workspace/tabs/BrowserTab.tsx
import { useState, useEffect, useRef } from 'react';
import { useAgentWorkspaceStore } from '@/store/agentWorkspaceStore';
import { Monitor, MousePointer, Globe } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { apiClient } from '@/api/client';

interface BrowserTabProps {
  agentId: string;
}

export function BrowserTab({ agentId }: BrowserTabProps) {
  const events = useAgentWorkspaceStore((s) => s.agentEvents[agentId] ?? []);
  const [inControl, setInControl] = useState(false);
  const [prevAutonomy, setPrevAutonomy] = useState<string>('autonomous');
  const imgRef = useRef<HTMLImageElement>(null);

  // Latest screenshot event
  const latestScreenshot = [...events]
    .reverse()
    .find((e) => e.type === 'browser_screenshot') as
    | { type: string; url?: string; png_base64?: string; width?: number; height?: number }
    | undefined;

  const latestAction = [...events]
    .reverse()
    .find((e) => e.type === 'browser_action') as
    | { type: string; action?: string; selector?: string; value?: string }
    | undefined;

  const handleTakeControl = async () => {
    try {
      const resp = await apiClient.get<{ level: string }>(
        `/api/studio/agents/${agentId}/autonomy`
      );
      setPrevAutonomy(resp.data?.level ?? 'autonomous');
      await apiClient.put(`/api/studio/agents/${agentId}/autonomy`, { level: 'watch' });
      setInControl(true);
    } catch {
      // Optimistic: still enter control mode UI
      setInControl(true);
    }
  };

  const handleRelease = async () => {
    try {
      await apiClient.put(`/api/studio/agents/${agentId}/autonomy`, {
        level: prevAutonomy,
      });
    } finally {
      setInControl(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-4 py-2 border-b border-gray-800 shrink-0">
        <Globe className="w-4 h-4 text-gray-400" />
        <span className="text-sm text-gray-400 flex-1 truncate font-mono">
          {latestScreenshot?.url ?? 'No browser activity yet'}
        </span>
        {inControl ? (
          <Button size="sm" variant="destructive" onClick={handleRelease}>
            Release Control
          </Button>
        ) : (
          <Button
            size="sm"
            variant="outline"
            className="gap-1.5"
            onClick={handleTakeControl}
            disabled={!latestScreenshot}
          >
            <MousePointer className="w-3.5 h-3.5" />
            Take Control
          </Button>
        )}
        {inControl && (
          <Badge variant="destructive" className="text-xs">
            YOU HAVE CONTROL
          </Badge>
        )}
      </div>

      {/* Screenshot display */}
      <div className="flex-1 overflow-hidden relative flex items-center justify-center bg-gray-900">
        {latestScreenshot?.png_base64 ? (
          <img
            ref={imgRef}
            src={`data:image/png;base64,${latestScreenshot.png_base64}`}
            alt="Agent browser"
            className="max-w-full max-h-full object-contain"
            style={{ imageRendering: 'crisp-edges' }}
          />
        ) : (
          <div className="flex flex-col items-center gap-3 text-gray-600">
            <Monitor className="w-12 h-12" />
            <p className="text-sm">Waiting for browser activity...</p>
          </div>
        )}
      </div>

      {/* Latest action */}
      {latestAction && (
        <div className="px-4 py-2 border-t border-gray-800 shrink-0">
          <span className="text-xs text-gray-500 font-mono">
            {latestAction.action}
            {latestAction.selector ? ` → ${latestAction.selector}` : ''}
            {latestAction.value ? ` = "${latestAction.value}"` : ''}
          </span>
        </div>
      )}
    </div>
  );
}
```

- [x] **Step 2: Wire into AgentWorkspacePage**

In `frontend/src/pages/AgentWorkspacePage.tsx`, replace:
```tsx
      return <PlaceholderTab name="Browser View" />;
```
with:
```tsx
      return <BrowserTab agentId={agentId} />;
```
And add import: `import { BrowserTab } from '@/components/workspace/tabs/BrowserTab';`

- [x] **Step 3: Commit**

```bash
git add frontend/src/components/workspace/tabs/BrowserTab.tsx frontend/src/pages/AgentWorkspacePage.tsx
git commit -m "feat(workspace): Browser tab with screenshot stream and Take Control"
```

---

### Task 1.2: FilesTab component

**Files:**
- Create: `frontend/src/components/workspace/tabs/FilesTab.tsx`
- Modify: `frontend/src/pages/AgentWorkspacePage.tsx`

- [x] **Step 1: Create FilesTab**

The Files tab shows a live file tree built from `file_change` SSE events. Files can be downloaded.

```tsx
// frontend/src/components/workspace/tabs/FilesTab.tsx
import { useMemo, useState } from 'react';
import { useAgentWorkspaceStore } from '@/store/agentWorkspaceStore';
import { Folder, File, Download, FolderOpen } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface FileEntry {
  path: string;
  op: 'create' | 'modify' | 'delete';
  content?: string;
  diff?: string;
  timestamp: number;
}

interface TreeNode {
  name: string;
  path: string;
  isDir: boolean;
  children: Record<string, TreeNode>;
  op?: 'create' | 'modify' | 'delete';
}

function buildTree(files: FileEntry[]): TreeNode {
  const root: TreeNode = { name: '/', path: '', isDir: true, children: {} };
  for (const f of files) {
    if (f.op === 'delete') continue;
    const parts = f.path.split('/').filter(Boolean);
    let node = root;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (!node.children[part]) {
        node.children[part] = {
          name: part,
          path: parts.slice(0, i + 1).join('/'),
          isDir: i < parts.length - 1,
          children: {},
        };
      }
      if (i === parts.length - 1) {
        node.children[part].op = f.op;
      }
      node = node.children[part];
    }
  }
  return root;
}

const OP_COLORS: Record<string, string> = {
  create: 'text-green-400',
  modify: 'text-yellow-400',
};

function TreeNodeView({
  node,
  depth = 0,
  onDownload,
}: {
  node: TreeNode;
  depth?: number;
  onDownload: (path: string, content?: string) => void;
}) {
  const [open, setOpen] = useState(depth < 2);
  const children = Object.values(node.children).sort(
    (a, b) => (b.isDir ? 1 : 0) - (a.isDir ? 1 : 0) || a.name.localeCompare(b.name)
  );

  return (
    <div>
      <div
        className="flex items-center gap-1.5 px-2 py-0.5 hover:bg-gray-800 cursor-pointer rounded group"
        style={{ paddingLeft: `${8 + depth * 16}px` }}
        onClick={() => node.isDir ? setOpen(!open) : undefined}
      >
        {node.isDir ? (
          open ? <FolderOpen className="w-3.5 h-3.5 text-yellow-400 shrink-0" /> : <Folder className="w-3.5 h-3.5 text-yellow-400 shrink-0" />
        ) : (
          <File className={`w-3.5 h-3.5 shrink-0 ${OP_COLORS[node.op ?? ''] ?? 'text-gray-400'}`} />
        )}
        <span className={`text-xs font-mono ${OP_COLORS[node.op ?? ''] ?? 'text-gray-300'}`}>
          {node.name}
        </span>
        {node.op && (
          <Badge variant="outline" className={`text-[10px] ml-auto ${OP_COLORS[node.op]} border-current`}>
            {node.op}
          </Badge>
        )}
        {!node.isDir && (
          <button
            className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={(e) => { e.stopPropagation(); onDownload(node.path); }}
          >
            <Download className="w-3 h-3 text-gray-400 hover:text-white" />
          </button>
        )}
      </div>
      {node.isDir && open && children.map((child) => (
        <TreeNodeView key={child.path} node={child} depth={depth + 1} onDownload={onDownload} />
      ))}
    </div>
  );
}

export function FilesTab({ agentId }: { agentId: string }) {
  const events = useAgentWorkspaceStore((s) => s.agentEvents[agentId] ?? []);

  const fileEvents: FileEntry[] = useMemo(() => {
    const seen = new Map<string, FileEntry>();
    for (const e of events) {
      if (e.type === 'file_change' && e.path) {
        seen.set(e.path, {
          path: e.path,
          op: e.op ?? 'modify',
          content: e.content,
          diff: e.diff,
          timestamp: Date.now(),
        });
      }
    }
    return Array.from(seen.values());
  }, [events]);

  const tree = useMemo(() => buildTree(fileEvents), [fileEvents]);

  const handleDownload = (path: string) => {
    const entry = fileEvents.find((f) => f.path === path);
    if (!entry?.content) return;
    const blob = new Blob([entry.content], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = path.split('/').pop() ?? path;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const totalFiles = fileEvents.filter((f) => f.op !== 'delete').length;

  return (
    <div className="flex flex-col h-full bg-gray-950">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-800 shrink-0">
        <Folder className="w-4 h-4 text-yellow-400" />
        <span className="text-sm text-gray-300 font-medium">Agent Workspace</span>
        <Badge variant="secondary" className="text-xs ml-auto">
          {totalFiles} file{totalFiles !== 1 ? 's' : ''}
        </Badge>
      </div>
      <div className="flex-1 overflow-y-auto py-1">
        {totalFiles === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-gray-600">
            <Folder className="w-10 h-10" />
            <p className="text-sm">No files yet</p>
          </div>
        ) : (
          Object.values(tree.children).map((child) => (
            <TreeNodeView key={child.path} node={child} onDownload={handleDownload} />
          ))
        )}
      </div>
    </div>
  );
}
```

- [x] **Step 2: Wire into AgentWorkspacePage**

Replace `<PlaceholderTab name="File Explorer" />` with `<FilesTab agentId={agentId} />` and add the import.

- [x] **Step 3: Commit**

```bash
git add frontend/src/components/workspace/tabs/FilesTab.tsx frontend/src/pages/AgentWorkspacePage.tsx
git commit -m "feat(workspace): Files tab with live file tree from SSE file_change events"
```

---

### Task 1.3: MemoryTab component

**Files:**
- Create: `frontend/src/components/workspace/tabs/MemoryTab.tsx`
- Modify: `frontend/src/pages/AgentWorkspacePage.tsx`

- [x] **Step 1: Create MemoryTab**

```tsx
// frontend/src/components/workspace/tabs/MemoryTab.tsx
import { useMemo, useState } from 'react';
import { useAgentWorkspaceStore } from '@/store/agentWorkspaceStore';
import { Brain, Trash2, Plus, Search } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';

interface MemoryEntry {
  id: string;
  op: 'add' | 'remove' | 'compact';
  entry: string;
  timestamp: number;
}

export function MemoryTab({ agentId }: { agentId: string }) {
  const events = useAgentWorkspaceStore((s) => s.agentEvents[agentId] ?? []);
  const [search, setSearch] = useState('');

  const entries: MemoryEntry[] = useMemo(() => {
    const active = new Map<string, MemoryEntry>();
    let idx = 0;
    for (const e of events) {
      if (e.type !== 'memory_update') continue;
      const id = e.entry?.id ?? String(idx++);
      if (e.op === 'remove') {
        active.delete(id);
      } else if (e.op === 'compact') {
        active.clear();
        if (e.entry) {
          active.set(id, { id, op: 'add', entry: e.entry?.content ?? String(e.entry), timestamp: Date.now() });
        }
      } else {
        active.set(id, {
          id,
          op: e.op ?? 'add',
          entry: e.entry?.content ?? String(e.entry ?? ''),
          timestamp: Date.now(),
        });
      }
    }
    return Array.from(active.values());
  }, [events]);

  const filtered = search
    ? entries.filter((e) => e.entry.toLowerCase().includes(search.toLowerCase()))
    : entries;

  return (
    <div className="flex flex-col h-full bg-gray-950">
      <div className="flex items-center gap-3 px-4 py-2 border-b border-gray-800 shrink-0">
        <Brain className="w-4 h-4 text-purple-400" />
        <span className="text-sm text-gray-300 font-medium">Memory</span>
        <Badge variant="secondary" className="text-xs">
          {entries.length} entries
        </Badge>
        <div className="flex-1 ml-2">
          <Input
            placeholder="Search memory..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-7 text-xs bg-gray-900 border-gray-700"
            prefix={<Search className="w-3 h-3" />}
          />
        </div>
      </div>
      <div className="flex-1 overflow-y-auto divide-y divide-gray-800">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-gray-600">
            <Brain className="w-10 h-10" />
            <p className="text-sm">{search ? 'No matches' : 'No memory entries yet'}</p>
          </div>
        ) : (
          filtered.map((e) => (
            <div key={e.id} className="px-4 py-2.5 flex items-start gap-3 hover:bg-gray-900">
              <span className="shrink-0 mt-0.5">
                {e.op === 'remove' ? (
                  <Trash2 className="w-3.5 h-3.5 text-red-400" />
                ) : (
                  <Plus className="w-3.5 h-3.5 text-green-400" />
                )}
              </span>
              <p className="text-xs text-gray-300 font-mono leading-relaxed flex-1">{e.entry}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
```

- [x] **Step 2: Wire into AgentWorkspacePage**

Replace `<PlaceholderTab name="Memory Inspector" />` with `<MemoryTab agentId={agentId} />`.

- [x] **Step 3: Commit**

```bash
git add frontend/src/components/workspace/tabs/MemoryTab.tsx frontend/src/pages/AgentWorkspacePage.tsx
git commit -m "feat(workspace): Memory tab with live CRUD from SSE memory_update events"
```

---

### Task 1.4: ConfigTab component

**Files:**
- Create: `frontend/src/components/workspace/tabs/ConfigTab.tsx`
- Modify: `frontend/src/pages/AgentWorkspacePage.tsx`

- [x] **Step 1: Create ConfigTab**

Config tab shows agent settings editable live. Fetches from `/api/studio/agents/{id}`, PATCHes changes.

```tsx
// frontend/src/components/workspace/tabs/ConfigTab.tsx
import { useState, useEffect } from 'react';
import { useAgentWorkspaceStore } from '@/store/agentWorkspaceStore';
import { Settings, Save, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { apiClient } from '@/api/client';
import { toast } from '@/components/ui/use-toast';

interface AgentConfig {
  model?: string;
  provider?: string;
  autonomy?: string;
  max_steps?: number;
  temperature?: number;
}

const AUTONOMY_LEVELS = ['watch', 'guide', 'delegate', 'autonomous'] as const;

export function ConfigTab({ agentId }: { agentId: string }) {
  const events = useAgentWorkspaceStore((s) => s.agentEvents[agentId] ?? []);
  const [config, setConfig] = useState<AgentConfig>({});
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);

  // Load initial config
  useEffect(() => {
    apiClient
      .get<AgentConfig>(`/api/studio/agents/${agentId}`)
      .then((r) => setConfig(r.data ?? {}))
      .catch(() => {});
  }, [agentId]);

  // Live config_change events update the display
  useEffect(() => {
    const latest = [...events].reverse().find((e) => e.type === 'config_change');
    if (latest?.field && latest.new_value !== undefined) {
      setConfig((prev) => ({ ...prev, [latest.field]: latest.new_value }));
    }
  }, [events]);

  const update = (field: keyof AgentConfig, value: string | number) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
    setDirty(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiClient.patch(`/api/studio/agents/${agentId}`, config);
      toast({ title: 'Config saved', description: 'Agent configuration updated.' });
      setDirty(false);
    } catch {
      toast({ title: 'Save failed', variant: 'destructive' });
    } finally {
      setSaving(false);
    }
  };

  const handleRefresh = () => {
    apiClient
      .get<AgentConfig>(`/api/studio/agents/${agentId}`)
      .then((r) => { setConfig(r.data ?? {}); setDirty(false); })
      .catch(() => {});
  };

  return (
    <div className="flex flex-col h-full bg-gray-950">
      <div className="flex items-center gap-3 px-4 py-2 border-b border-gray-800 shrink-0">
        <Settings className="w-4 h-4 text-gray-400" />
        <span className="text-sm text-gray-300 font-medium">Agent Config</span>
        <div className="ml-auto flex gap-2">
          <Button size="sm" variant="ghost" onClick={handleRefresh}>
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
          <Button size="sm" disabled={!dirty || saving} onClick={handleSave}>
            <Save className="w-3.5 h-3.5 mr-1.5" />
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="space-y-1.5">
          <label className="text-xs text-gray-400 font-medium">Model</label>
          <Input
            value={config.model ?? ''}
            onChange={(e) => update('model', e.target.value)}
            className="bg-gray-900 border-gray-700 text-sm h-8"
            placeholder="e.g. claude-sonnet-4-6"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-xs text-gray-400 font-medium">Provider</label>
          <Input
            value={config.provider ?? ''}
            onChange={(e) => update('provider', e.target.value)}
            className="bg-gray-900 border-gray-700 text-sm h-8"
            placeholder="e.g. anthropic"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-xs text-gray-400 font-medium">Autonomy Level</label>
          <Select value={config.autonomy ?? 'autonomous'} onValueChange={(v) => update('autonomy', v)}>
            <SelectTrigger className="bg-gray-900 border-gray-700 h-8 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {AUTONOMY_LEVELS.map((l) => (
                <SelectItem key={l} value={l} className="capitalize">{l}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs text-gray-400 font-medium">Max Steps</label>
          <Input
            type="number"
            value={config.max_steps ?? ''}
            onChange={(e) => update('max_steps', parseInt(e.target.value) || 0)}
            className="bg-gray-900 border-gray-700 text-sm h-8"
            placeholder="e.g. 50"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-xs text-gray-400 font-medium">Temperature</label>
          <Input
            type="number"
            step="0.1"
            min="0"
            max="2"
            value={config.temperature ?? ''}
            onChange={(e) => update('temperature', parseFloat(e.target.value) || 0)}
            className="bg-gray-900 border-gray-700 text-sm h-8"
            placeholder="e.g. 0.7"
          />
        </div>
      </div>
    </div>
  );
}
```

- [x] **Step 2: Wire into AgentWorkspacePage**

Replace `<PlaceholderTab name="Agent Configuration" />` with `<ConfigTab agentId={agentId} />`.

- [x] **Step 3: Commit**

```bash
git add frontend/src/components/workspace/tabs/ConfigTab.tsx frontend/src/pages/AgentWorkspacePage.tsx
git commit -m "feat(workspace): Config tab with live PATCH to prowlrbot agent config"
```

---

## Chunk 2: Layout Modes — Float, Split, PiP, Focus

Phase 1 renders Tile (grid) and Stack (tabs). Phase 2 adds Float (draggable windows), Split (main+sidebar), PiP (main+mini floats), Focus+Timeline.

### Task 2.1: FloatLayout component

**Files:**
- Create: `frontend/src/components/workspace/layouts/FloatLayout.tsx`
- Modify: `frontend/src/pages/AgentWorkspacePage.tsx`

- [x] **Step 1: Create FloatLayout**

```tsx
// frontend/src/components/workspace/layouts/FloatLayout.tsx
import { useState, useRef, useCallback } from 'react';
import { X, Minus } from 'lucide-react';

interface FloatWindow {
  agentId: string;
  x: number;
  y: number;
  width: number;
  height: number;
  minimized: boolean;
  zIndex: number;
}

interface FloatLayoutProps {
  agentIds: string[];
  renderAgent: (agentId: string) => React.ReactNode;
}

export function FloatLayout({ agentIds, renderAgent }: FloatLayoutProps) {
  const [windows, setWindows] = useState<Record<string, FloatWindow>>(() =>
    Object.fromEntries(
      agentIds.map((id, i) => [
        id,
        { agentId: id, x: 40 + i * 30, y: 40 + i * 30, width: 640, height: 480, minimized: false, zIndex: i },
      ])
    )
  );
  const [topZ, setTopZ] = useState(agentIds.length);
  const dragging = useRef<{ id: string; startX: number; startY: number; origX: number; origY: number } | null>(null);

  const bringToFront = useCallback((id: string) => {
    setTopZ((z) => z + 1);
    setWindows((prev) => ({ ...prev, [id]: { ...prev[id], zIndex: topZ + 1 } }));
  }, [topZ]);

  const onMouseDown = (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    bringToFront(id);
    dragging.current = { id, startX: e.clientX, startY: e.clientY, origX: windows[id].x, origY: windows[id].y };
    const onMove = (me: MouseEvent) => {
      if (!dragging.current) return;
      const dx = me.clientX - dragging.current.startX;
      const dy = me.clientY - dragging.current.startY;
      setWindows((prev) => ({
        ...prev,
        [dragging.current!.id]: {
          ...prev[dragging.current!.id],
          x: Math.max(0, dragging.current!.origX + dx),
          y: Math.max(0, dragging.current!.origY + dy),
        },
      }));
    };
    const onUp = () => {
      dragging.current = null;
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };

  return (
    <div className="relative w-full h-full overflow-hidden bg-gray-950">
      {Object.values(windows).map((w) => (
        <div
          key={w.agentId}
          className="absolute rounded-lg border border-gray-700 shadow-2xl overflow-hidden flex flex-col"
          style={{ left: w.x, top: w.y, width: w.width, height: w.minimized ? 36 : w.height, zIndex: w.zIndex }}
          onMouseDown={() => bringToFront(w.agentId)}
        >
          {/* Title bar */}
          <div
            className="flex items-center gap-2 px-3 h-9 bg-gray-800 cursor-move shrink-0 select-none"
            onMouseDown={(e) => onMouseDown(w.agentId, e)}
          >
            <span className="text-xs text-gray-300 font-mono flex-1 truncate">{w.agentId}</span>
            <button
              className="text-gray-400 hover:text-white"
              onClick={() => setWindows((p) => ({ ...p, [w.agentId]: { ...p[w.agentId], minimized: !p[w.agentId].minimized } }))}
            >
              <Minus className="w-3.5 h-3.5" />
            </button>
          </div>
          {!w.minimized && (
            <div className="flex-1 overflow-hidden">{renderAgent(w.agentId)}</div>
          )}
        </div>
      ))}
    </div>
  );
}
```

- [x] **Step 2: Wire into AgentWorkspacePage**

Add to the layout dispatch in `AgentWorkspacePage.tsx`:
```tsx
import { FloatLayout } from '@/components/workspace/layouts/FloatLayout';

// In the render switch, after 'stack' case:
if (layoutMode === 'float') {
  return (
    <FloatLayout
      agentIds={activeAgents}
      renderAgent={(id) => <AgentPanel agentId={id} />}
    />
  );
}
```

- [x] **Step 3: Commit**

```bash
git add frontend/src/components/workspace/layouts/FloatLayout.tsx frontend/src/pages/AgentWorkspacePage.tsx
git commit -m "feat(workspace): Float layout — draggable, resizable, z-stacked agent windows"
```

---

### Task 2.2: SplitLayout, PiPLayout, FocusLayout

**Files:**
- Create: `frontend/src/components/workspace/layouts/SplitLayout.tsx`
- Create: `frontend/src/components/workspace/layouts/PiPLayout.tsx`
- Create: `frontend/src/components/workspace/layouts/FocusLayout.tsx`
- Modify: `frontend/src/pages/AgentWorkspacePage.tsx`

- [x] **Step 1: Create SplitLayout**

One main agent full-height left, others stacked in a narrow right sidebar.

```tsx
// frontend/src/components/workspace/layouts/SplitLayout.tsx
import { useState } from 'react';

interface SplitLayoutProps {
  agentIds: string[];
  renderAgent: (agentId: string) => React.ReactNode;
}

export function SplitLayout({ agentIds, renderAgent }: SplitLayoutProps) {
  const [primary, setPrimary] = useState(agentIds[0]);
  const others = agentIds.filter((id) => id !== primary);

  return (
    <div className="flex h-full w-full gap-0">
      {/* Main */}
      <div className="flex-1 overflow-hidden">{renderAgent(primary)}</div>
      {/* Sidebar */}
      {others.length > 0 && (
        <div className="w-64 shrink-0 border-l border-gray-800 flex flex-col divide-y divide-gray-800">
          {others.map((id) => (
            <div
              key={id}
              className="flex-1 overflow-hidden cursor-pointer relative group"
              onClick={() => setPrimary(id)}
            >
              {renderAgent(id)}
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <span className="text-xs text-white font-medium">Make Primary</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [x] **Step 2: Create PiPLayout**

Main agent full-screen, others as small floating overlays in corners.

```tsx
// frontend/src/components/workspace/layouts/PiPLayout.tsx
import { useState } from 'react';

interface PiPLayoutProps {
  agentIds: string[];
  renderAgent: (agentId: string) => React.ReactNode;
}

const PIP_POSITIONS = [
  { bottom: 16, right: 16 },
  { bottom: 16, left: 16 },
  { top: 56, right: 16 },
  { top: 56, left: 16 },
];

export function PiPLayout({ agentIds, renderAgent }: PiPLayoutProps) {
  const [primary, setPrimary] = useState(agentIds[0]);
  const pips = agentIds.filter((id) => id !== primary);

  return (
    <div className="relative w-full h-full">
      {/* Full background main */}
      <div className="absolute inset-0">{renderAgent(primary)}</div>
      {/* PiP overlays */}
      {pips.map((id, i) => {
        const pos = PIP_POSITIONS[i % PIP_POSITIONS.length];
        return (
          <div
            key={id}
            className="absolute w-56 h-36 rounded-lg border border-gray-600 shadow-2xl overflow-hidden cursor-pointer group"
            style={pos}
            onClick={() => setPrimary(id)}
          >
            {renderAgent(id)}
            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <span className="text-xs text-white font-medium">Swap</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

- [x] **Step 3: Create FocusLayout**

Full-screen single agent with a scrubber timeline at the bottom showing event history.

```tsx
// frontend/src/components/workspace/layouts/FocusLayout.tsx
import { useState } from 'react';
import { useAgentWorkspaceStore } from '@/store/agentWorkspaceStore';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface FocusLayoutProps {
  agentIds: string[];
  renderAgent: (agentId: string) => React.ReactNode;
}

export function FocusLayout({ agentIds, renderAgent }: FocusLayoutProps) {
  const [idx, setIdx] = useState(0);
  const agentId = agentIds[idx] ?? agentIds[0];
  const events = useAgentWorkspaceStore((s) => s.agentEvents[agentId] ?? []);

  return (
    <div className="flex flex-col h-full">
      {/* Agent selector */}
      {agentIds.length > 1 && (
        <div className="flex items-center justify-center gap-4 px-4 py-1.5 border-b border-gray-800 shrink-0 bg-gray-900">
          <button disabled={idx === 0} onClick={() => setIdx((i) => i - 1)}>
            <ChevronLeft className="w-4 h-4 text-gray-400" />
          </button>
          <span className="text-sm text-gray-300 font-mono">{agentId}</span>
          <span className="text-xs text-gray-600">{idx + 1}/{agentIds.length}</span>
          <button disabled={idx === agentIds.length - 1} onClick={() => setIdx((i) => i + 1)}>
            <ChevronRight className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      )}

      {/* Full agent view */}
      <div className="flex-1 overflow-hidden">{renderAgent(agentId)}</div>

      {/* Timeline scrubber */}
      <div className="shrink-0 border-t border-gray-800 bg-gray-900 px-4 py-2">
        <div className="flex items-center gap-1 overflow-x-auto">
          {events.slice(-40).map((e, i) => (
            <div
              key={i}
              title={e.type}
              className={`w-2 h-2 rounded-full shrink-0 ${
                e.type === 'thought' ? 'bg-purple-500' :
                e.type === 'tool_call' ? 'bg-blue-500' :
                e.type === 'browser_screenshot' ? 'bg-green-500' :
                e.type === 'cost_update' ? 'bg-yellow-500' :
                'bg-gray-600'
              }`}
            />
          ))}
          {events.length > 40 && (
            <span className="text-xs text-gray-600 ml-1">+{events.length - 40}</span>
          )}
        </div>
        <p className="text-[10px] text-gray-600 mt-1">{events.length} events</p>
      </div>
    </div>
  );
}
```

- [x] **Step 4: Wire all three into AgentWorkspacePage**

Add imports and layout dispatch cases for `'split'`, `'pip'`, `'focus'` in `AgentWorkspacePage.tsx`.

- [x] **Step 5: Commit**

```bash
git add frontend/src/components/workspace/layouts/ frontend/src/pages/AgentWorkspacePage.tsx
git commit -m "feat(workspace): Split, PiP, and Focus+Timeline layout modes (all 6 layouts complete)"
```

---

## Chunk 3: Rebuild Console Pages in Studio

Five pages from ProwlrBot's old React console get rebuilt using Studio's Tailwind + shadcn design system. Each page fetches from the ProwlrBot FastAPI backend at `:8088` via the Studio proxy (`/api/prowlrbot/*`).

### Task 3.1: Studio proxy service (NestJS)

**Files:**
- Create: `backend/src/prowlrbot/prowlrbot.module.ts`
- Create: `backend/src/prowlrbot/prowlrbot.controller.ts`
- Modify: `backend/src/app.module.ts`

- [x] **Step 1: Create prowlrbot proxy controller**

```typescript
// backend/src/prowlrbot/prowlrbot.controller.ts
import { All, Controller, Req, Res } from '@nestjs/common';
import { Request, Response } from 'express';
import axios from 'axios';

const PROWLRBOT_URL = process.env.PROWLRBOT_API_URL ?? 'http://localhost:8088';

@Controller('prowlrbot')
export class ProwlrBotController {
  @All('*')
  async proxy(@Req() req: Request, @Res() res: Response) {
    const path = req.params[0] ?? '';
    const url = `${PROWLRBOT_URL}/${path}`;
    try {
      const response = await axios({
        method: req.method as any,
        url,
        params: req.query,
        data: req.body,
        headers: {
          'Content-Type': req.headers['content-type'] ?? 'application/json',
          Authorization: req.headers['authorization'] ?? '',
        },
        responseType: 'json',
        timeout: 15000,
      });
      res.status(response.status).json(response.data);
    } catch (err: any) {
      const status = err.response?.status ?? 502;
      res.status(status).json(err.response?.data ?? { error: 'Proxy error' });
    }
  }
}
```

```typescript
// backend/src/prowlrbot/prowlrbot.module.ts
import { Module } from '@nestjs/common';
import { ProwlrBotController } from './prowlrbot.controller';

@Module({ controllers: [ProwlrBotController] })
export class ProwlrBotModule {}
```

- [x] **Step 2: Register in app.module.ts**

Import and add `ProwlrBotModule` to the `imports` array in `backend/src/app.module.ts`.

- [x] **Step 3: Commit**

```bash
git add backend/src/prowlrbot/
git commit -m "feat(backend): /prowlrbot/* proxy routes to ProwlrBot FastAPI at :8088"
```

---

### Task 3.2: ChatPage

**Files:**
- Create: `frontend/src/pages/ChatPage.tsx`
- Modify: `frontend/src/App.tsx` (add route)

- [x] **Step 1: Create ChatPage**

Chat page mirrors ProwlrBot console's chat — session list sidebar, message thread, input bar. Uses `GET /prowlrbot/chats`, `GET /prowlrbot/chats/{id}/messages`, `POST /prowlrbot/chats/{id}/message`.

```tsx
// frontend/src/pages/ChatPage.tsx
import { useState, useEffect, useRef } from 'react';
import { Send, Plus, MessageSquare, Bot, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { apiClient } from '@/api/client';
import { cn } from '@/lib/utils';

interface ChatSession { id: string; name: string; created_at: string; message_count: number; }
interface ChatMessage { id: string; role: 'user' | 'assistant'; content: string; created_at: string; }

export function ChatPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiClient.get<ChatSession[]>('/prowlrbot/chats').then((r) => {
      setSessions(r.data ?? []);
      if (r.data?.length) setActiveId(r.data[0].id);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!activeId) return;
    apiClient.get<ChatMessage[]>(`/prowlrbot/chats/${activeId}/messages`)
      .then((r) => setMessages(r.data ?? []))
      .catch(() => {});
  }, [activeId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || !activeId) return;
    const text = input.trim();
    setInput('');
    setSending(true);
    setMessages((prev) => [...prev, { id: Date.now().toString(), role: 'user', content: text, created_at: new Date().toISOString() }]);
    try {
      const r = await apiClient.post<ChatMessage>(`/prowlrbot/chats/${activeId}/message`, { content: text });
      if (r.data) setMessages((prev) => [...prev, r.data]);
    } catch {
      setMessages((prev) => [...prev, { id: 'err', role: 'assistant', content: 'Error sending message.', created_at: new Date().toISOString() }]);
    } finally {
      setSending(false);
    }
  };

  const handleNew = async () => {
    try {
      const r = await apiClient.post<ChatSession>('/prowlrbot/chats', { name: `Chat ${sessions.length + 1}` });
      if (r.data) { setSessions((p) => [r.data, ...p]); setActiveId(r.data.id); setMessages([]); }
    } catch {}
  };

  return (
    <div className="flex h-full bg-gray-950">
      {/* Session sidebar */}
      <div className="w-56 shrink-0 border-r border-gray-800 flex flex-col">
        <div className="p-3 border-b border-gray-800">
          <Button size="sm" className="w-full gap-1.5" onClick={handleNew}>
            <Plus className="w-3.5 h-3.5" /> New Chat
          </Button>
        </div>
        <ScrollArea className="flex-1">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveId(s.id)}
              className={cn(
                'w-full text-left px-3 py-2.5 flex items-center gap-2 hover:bg-gray-800 transition-colors',
                activeId === s.id && 'bg-gray-800'
              )}
            >
              <MessageSquare className="w-3.5 h-3.5 text-gray-500 shrink-0" />
              <span className="text-xs text-gray-300 truncate">{s.name}</span>
            </button>
          ))}
        </ScrollArea>
      </div>

      {/* Thread */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4 max-w-3xl mx-auto">
            {messages.map((m) => (
              <div key={m.id} className={cn('flex gap-3', m.role === 'user' && 'flex-row-reverse')}>
                <div className={cn('w-7 h-7 rounded-full flex items-center justify-center shrink-0', m.role === 'assistant' ? 'bg-purple-600' : 'bg-gray-700')}>
                  {m.role === 'assistant' ? <Bot className="w-4 h-4 text-white" /> : <User className="w-4 h-4 text-white" />}
                </div>
                <div className={cn('rounded-lg px-3 py-2 max-w-[80%] text-sm', m.role === 'assistant' ? 'bg-gray-800 text-gray-200' : 'bg-purple-700 text-white')}>
                  {m.content}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        </ScrollArea>
        <div className="p-4 border-t border-gray-800 flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Message the agent..."
            className="bg-gray-900 border-gray-700"
            disabled={!activeId}
          />
          <Button onClick={handleSend} disabled={!input.trim() || sending || !activeId}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
```

- [x] **Step 2: Add route in App.tsx**

```tsx
import { ChatPage } from '@/pages/ChatPage';
// In the router:
<Route path="/chat" element={<ChatPage />} />
```

- [x] **Step 3: Commit**

```bash
git add frontend/src/pages/ChatPage.tsx frontend/src/App.tsx
git commit -m "feat(pages): Chat page — session list + message thread + ProwlrBot backend"
```

---

### Task 3.3: ChannelsPage

**Files:**
- Create: `frontend/src/pages/ChannelsPage.tsx`
- Modify: `frontend/src/App.tsx`

- [x] **Step 1: Create ChannelsPage**

CRUD for channels. Fetches `GET /prowlrbot/channels`, toggles enable/disable, shows status badges. Each channel card has type, status (connected/disconnected), edit button.

```tsx
// frontend/src/pages/ChannelsPage.tsx
import { useState, useEffect } from 'react';
import { Radio, MessageCircle, Bot, Terminal, Webhook, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { apiClient } from '@/api/client';
import { toast } from '@/components/ui/use-toast';

interface Channel {
  id: string;
  type: string;
  name: string;
  enabled: boolean;
  status: 'connected' | 'disconnected' | 'error';
  config?: Record<string, string>;
}

const CHANNEL_ICONS: Record<string, React.ElementType> = {
  discord: MessageCircle,
  telegram: MessageCircle,
  console: Terminal,
  dingtalk: Radio,
  feishu: Radio,
  qq: MessageCircle,
};

const STATUS_COLORS: Record<string, string> = {
  connected: 'bg-green-500',
  disconnected: 'bg-gray-500',
  error: 'bg-red-500',
};

export function ChannelsPage() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get<Channel[]>('/prowlrbot/channels')
      .then((r) => setChannels(r.data ?? []))
      .finally(() => setLoading(false));
  }, []);

  const toggle = async (id: string, enabled: boolean) => {
    setChannels((prev) => prev.map((c) => c.id === id ? { ...c, enabled } : c));
    try {
      await apiClient.patch(`/prowlrbot/channels/${id}`, { enabled });
    } catch {
      setChannels((prev) => prev.map((c) => c.id === id ? { ...c, enabled: !enabled } : c));
      toast({ title: 'Failed to update channel', variant: 'destructive' });
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-white">Channels</h1>
          <p className="text-sm text-gray-400 mt-0.5">Manage how ProwlrBot communicates</p>
        </div>
        <Button size="sm" className="gap-1.5">
          <Plus className="w-3.5 h-3.5" /> Add Channel
        </Button>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <div key={i} className="h-28 bg-gray-800 rounded-lg animate-pulse" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {channels.map((ch) => {
            const Icon = CHANNEL_ICONS[ch.type] ?? Webhook;
            return (
              <div key={ch.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-gray-800 flex items-center justify-center">
                    <Icon className="w-4 h-4 text-gray-300" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{ch.name}</p>
                    <p className="text-xs text-gray-500 capitalize">{ch.type}</p>
                  </div>
                  <div className={`w-2 h-2 rounded-full ${STATUS_COLORS[ch.status]}`} />
                </div>
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="text-xs capitalize text-gray-400 border-gray-700">
                    {ch.status}
                  </Badge>
                  <Switch checked={ch.enabled} onCheckedChange={(v) => toggle(ch.id, v)} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
```

- [x] **Step 2: Add route**

```tsx
import { ChannelsPage } from '@/pages/ChannelsPage';
<Route path="/channels" element={<ChannelsPage />} />
```

- [x] **Step 3: Commit**

```bash
git add frontend/src/pages/ChannelsPage.tsx frontend/src/App.tsx
git commit -m "feat(pages): Channels page — type cards with status badges and enable toggle"
```

---

### Task 3.4: MonitorsPage

**Files:**
- Create: `frontend/src/pages/MonitorsPage.tsx`
- Modify: `frontend/src/App.tsx`

- [x] **Step 1: Create MonitorsPage**

Lists web/API monitors. Shows URL, type, interval, last status, last checked. Toggle enabled. Uses `GET/POST/PATCH/DELETE /prowlrbot/monitors`.

```tsx
// frontend/src/pages/MonitorsPage.tsx
import { useState, useEffect } from 'react';
import { Globe, Activity, Plus, Trash2, Play, Pause } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { apiClient } from '@/api/client';
import { toast } from '@/components/ui/use-toast';
import { formatDistanceToNow } from 'date-fns';

interface Monitor {
  id: string;
  name: string;
  url: string;
  type: 'web' | 'api' | 'rss';
  interval_minutes: number;
  enabled: boolean;
  last_status?: 'ok' | 'changed' | 'error';
  last_checked_at?: string;
}

const STATUS_BADGE: Record<string, { color: string; label: string }> = {
  ok: { color: 'bg-green-500/20 text-green-400 border-green-800', label: 'OK' },
  changed: { color: 'bg-yellow-500/20 text-yellow-400 border-yellow-800', label: 'Changed' },
  error: { color: 'bg-red-500/20 text-red-400 border-red-800', label: 'Error' },
};

export function MonitorsPage() {
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get<Monitor[]>('/prowlrbot/monitors')
      .then((r) => setMonitors(r.data ?? []))
      .finally(() => setLoading(false));
  }, []);

  const toggle = async (id: string, enabled: boolean) => {
    setMonitors((prev) => prev.map((m) => m.id === id ? { ...m, enabled } : m));
    await apiClient.patch(`/prowlrbot/monitors/${id}`, { enabled }).catch(() => {
      setMonitors((prev) => prev.map((m) => m.id === id ? { ...m, enabled: !enabled } : m));
    });
  };

  const deleteMonitor = async (id: string) => {
    setMonitors((prev) => prev.filter((m) => m.id !== id));
    await apiClient.delete(`/prowlrbot/monitors/${id}`).catch(() => {
      toast({ title: 'Failed to delete monitor', variant: 'destructive' });
    });
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-white">Monitors</h1>
          <p className="text-sm text-gray-400 mt-0.5">Web and API change detection</p>
        </div>
        <Button size="sm" className="gap-1.5">
          <Plus className="w-3.5 h-3.5" /> Add Monitor
        </Button>
      </div>

      <div className="space-y-2">
        {loading ? (
          [1, 2, 3].map((i) => <div key={i} className="h-16 bg-gray-800 rounded-lg animate-pulse" />)
        ) : monitors.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-600">
            <Globe className="w-12 h-12 mb-3" />
            <p>No monitors yet. Add one to start watching URLs.</p>
          </div>
        ) : (
          monitors.map((m) => {
            const status = m.last_status ? STATUS_BADGE[m.last_status] : null;
            return (
              <div key={m.id} className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 flex items-center gap-4">
                <Globe className="w-4 h-4 text-gray-500 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-white truncate">{m.name}</p>
                    {status && (
                      <Badge variant="outline" className={`text-xs ${status.color}`}>{status.label}</Badge>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 truncate">{m.url}</p>
                </div>
                <span className="text-xs text-gray-600 shrink-0">
                  every {m.interval_minutes}m
                </span>
                {m.last_checked_at && (
                  <span className="text-xs text-gray-600 shrink-0">
                    {formatDistanceToNow(new Date(m.last_checked_at), { addSuffix: true })}
                  </span>
                )}
                <Switch checked={m.enabled} onCheckedChange={(v) => toggle(m.id, v)} />
                <button onClick={() => deleteMonitor(m.id)} className="text-gray-600 hover:text-red-400 transition-colors">
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
```

- [x] **Step 2: Add route**

```tsx
import { MonitorsPage } from '@/pages/MonitorsPage';
<Route path="/monitors" element={<MonitorsPage />} />
```

- [x] **Step 3: Commit**

```bash
git add frontend/src/pages/MonitorsPage.tsx frontend/src/App.tsx
git commit -m "feat(pages): Monitors page with status badges, toggle, delete"
```

---

### Task 3.5: CronPage

**Files:**
- Create: `frontend/src/pages/CronPage.tsx`
- Modify: `frontend/src/App.tsx`

- [x] **Step 1: Create CronPage**

Lists scheduled cron jobs. Shows name, expression, next run, last run, status. Uses `GET/POST/PATCH/DELETE /prowlrbot/crons`.

```tsx
// frontend/src/pages/CronPage.tsx
import { useState, useEffect } from 'react';
import { Clock, Plus, Trash2, CheckCircle, XCircle, Timer } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { apiClient } from '@/api/client';
import { formatDistanceToNow } from 'date-fns';

interface CronJob {
  id: string;
  name: string;
  expression: string;
  enabled: boolean;
  last_run_at?: string;
  last_run_status?: 'success' | 'error';
  next_run_at?: string;
  task?: string;
}

export function CronPage() {
  const [jobs, setJobs] = useState<CronJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get<CronJob[]>('/prowlrbot/crons')
      .then((r) => setJobs(r.data ?? []))
      .finally(() => setLoading(false));
  }, []);

  const toggle = async (id: string, enabled: boolean) => {
    setJobs((prev) => prev.map((j) => j.id === id ? { ...j, enabled } : j));
    await apiClient.patch(`/prowlrbot/crons/${id}`, { enabled }).catch(() => {
      setJobs((prev) => prev.map((j) => j.id === id ? { ...j, enabled: !enabled } : j));
    });
  };

  const deleteJob = async (id: string) => {
    setJobs((prev) => prev.filter((j) => j.id !== id));
    await apiClient.delete(`/prowlrbot/crons/${id}`).catch(() => {});
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-white">Scheduled Jobs</h1>
          <p className="text-sm text-gray-400 mt-0.5">APScheduler cron + interval jobs</p>
        </div>
        <Button size="sm" className="gap-1.5">
          <Plus className="w-3.5 h-3.5" /> Add Job
        </Button>
      </div>

      <div className="space-y-2">
        {loading ? (
          [1, 2, 3].map((i) => <div key={i} className="h-16 bg-gray-800 rounded-lg animate-pulse" />)
        ) : jobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-600">
            <Clock className="w-12 h-12 mb-3" />
            <p>No scheduled jobs. Add one to automate tasks.</p>
          </div>
        ) : (
          jobs.map((j) => (
            <div key={j.id} className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 flex items-center gap-4">
              <Clock className="w-4 h-4 text-gray-500 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-white">{j.name}</p>
                  {j.last_run_status === 'success' ? (
                    <CheckCircle className="w-3.5 h-3.5 text-green-400" />
                  ) : j.last_run_status === 'error' ? (
                    <XCircle className="w-3.5 h-3.5 text-red-400" />
                  ) : null}
                </div>
                <p className="text-xs text-gray-500 font-mono">{j.expression}</p>
              </div>
              {j.next_run_at && (
                <div className="text-right shrink-0">
                  <p className="text-xs text-gray-400 flex items-center gap-1">
                    <Timer className="w-3 h-3" />
                    {formatDistanceToNow(new Date(j.next_run_at), { addSuffix: true })}
                  </p>
                </div>
              )}
              {j.last_run_at && (
                <span className="text-xs text-gray-600 shrink-0">
                  last {formatDistanceToNow(new Date(j.last_run_at), { addSuffix: true })}
                </span>
              )}
              <Switch checked={j.enabled} onCheckedChange={(v) => toggle(j.id, v)} />
              <button onClick={() => deleteJob(j.id)} className="text-gray-600 hover:text-red-400 transition-colors">
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
```

- [x] **Step 2: Add route, commit**

```tsx
import { CronPage } from '@/pages/CronPage';
<Route path="/crons" element={<CronPage />} />
```

```bash
git add frontend/src/pages/CronPage.tsx frontend/src/App.tsx
git commit -m "feat(pages): Cron page — scheduled jobs with expression, next/last run, toggle"
```

---

### Task 3.6: SettingsPage

**Files:**
- Create: `frontend/src/pages/SettingsPage.tsx`
- Modify: `frontend/src/App.tsx`

- [x] **Step 1: Create SettingsPage**

Tabbed settings page: Models (provider selector, model config), Environment (env vars CRUD), About (version info). Uses `GET/PUT /prowlrbot/config`, `GET/POST/DELETE /prowlrbot/envs`.

```tsx
// frontend/src/pages/SettingsPage.tsx
import { useState, useEffect } from 'react';
import { Cpu, Key, Info, Save, Plus, Trash2, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { apiClient } from '@/api/client';
import { toast } from '@/components/ui/use-toast';

interface EnvVar { key: string; value: string; }
interface ModelConfig { provider: string; model: string; api_key?: string; base_url?: string; }

export function SettingsPage() {
  const [modelConfig, setModelConfig] = useState<ModelConfig>({ provider: '', model: '' });
  const [envVars, setEnvVars] = useState<EnvVar[]>([]);
  const [showKeys, setShowKeys] = useState<Set<string>>(new Set());
  const [version, setVersion] = useState<string>('');

  useEffect(() => {
    apiClient.get<{ model: ModelConfig; version: string }>('/prowlrbot/config')
      .then((r) => { if (r.data?.model) setModelConfig(r.data.model); if (r.data?.version) setVersion(r.data.version); })
      .catch(() => {});
    apiClient.get<Record<string, string>>('/prowlrbot/envs')
      .then((r) => { if (r.data) setEnvVars(Object.entries(r.data).map(([key, value]) => ({ key, value }))); })
      .catch(() => {});
  }, []);

  const saveModel = async () => {
    try {
      await apiClient.put('/prowlrbot/config', { model: modelConfig });
      toast({ title: 'Model config saved' });
    } catch {
      toast({ title: 'Save failed', variant: 'destructive' });
    }
  };

  const addEnv = () => setEnvVars((p) => [...p, { key: '', value: '' }]);
  const updateEnv = (i: number, field: 'key' | 'value', val: string) =>
    setEnvVars((p) => p.map((e, idx) => idx === i ? { ...e, [field]: val } : e));
  const deleteEnv = async (i: number) => {
    const entry = envVars[i];
    setEnvVars((p) => p.filter((_, idx) => idx !== i));
    if (entry.key) await apiClient.delete(`/prowlrbot/envs/${entry.key}`).catch(() => {});
  };
  const saveEnvs = async () => {
    try {
      const data = Object.fromEntries(envVars.filter((e) => e.key).map((e) => [e.key, e.value]));
      await apiClient.post('/prowlrbot/envs/bulk', data);
      toast({ title: 'Environment variables saved' });
    } catch {
      toast({ title: 'Save failed', variant: 'destructive' });
    }
  };
  const toggleShow = (key: string) => setShowKeys((p) => { const n = new Set(p); n.has(key) ? n.delete(key) : n.add(key); return n; });

  return (
    <div className="p-6 max-w-3xl">
      <h1 className="text-xl font-semibold text-white mb-6">Settings</h1>
      <Tabs defaultValue="models">
        <TabsList className="bg-gray-900 border border-gray-800">
          <TabsTrigger value="models" className="gap-1.5"><Cpu className="w-3.5 h-3.5" /> Models</TabsTrigger>
          <TabsTrigger value="env" className="gap-1.5"><Key className="w-3.5 h-3.5" /> Environment</TabsTrigger>
          <TabsTrigger value="about" className="gap-1.5"><Info className="w-3.5 h-3.5" /> About</TabsTrigger>
        </TabsList>

        <TabsContent value="models" className="mt-6 space-y-4">
          {(['provider', 'model', 'api_key', 'base_url'] as const).map((field) => (
            <div key={field} className="space-y-1.5">
              <label className="text-xs text-gray-400 font-medium capitalize">{field.replace('_', ' ')}</label>
              <Input
                value={modelConfig[field] ?? ''}
                onChange={(e) => setModelConfig((p) => ({ ...p, [field]: e.target.value }))}
                type={field === 'api_key' ? 'password' : 'text'}
                className="bg-gray-900 border-gray-700"
                placeholder={field === 'api_key' ? 'sk-...' : field === 'base_url' ? 'https://api.anthropic.com' : ''}
              />
            </div>
          ))}
          <Button onClick={saveModel} className="gap-1.5">
            <Save className="w-3.5 h-3.5" /> Save Model Config
          </Button>
        </TabsContent>

        <TabsContent value="env" className="mt-6 space-y-3">
          {envVars.map((e, i) => (
            <div key={i} className="flex gap-2 items-center">
              <Input value={e.key} onChange={(ev) => updateEnv(i, 'key', ev.target.value)} placeholder="KEY" className="bg-gray-900 border-gray-700 font-mono text-sm w-48" />
              <Input
                value={e.value}
                onChange={(ev) => updateEnv(i, 'value', ev.target.value)}
                type={showKeys.has(e.key) ? 'text' : 'password'}
                placeholder="value"
                className="bg-gray-900 border-gray-700 font-mono text-sm flex-1"
              />
              <button onClick={() => toggleShow(e.key)} className="text-gray-500 hover:text-white">
                {showKeys.has(e.key) ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
              <button onClick={() => deleteEnv(i)} className="text-gray-500 hover:text-red-400">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
          <div className="flex gap-2 pt-2">
            <Button size="sm" variant="outline" onClick={addEnv} className="gap-1.5">
              <Plus className="w-3.5 h-3.5" /> Add Variable
            </Button>
            <Button size="sm" onClick={saveEnvs} className="gap-1.5">
              <Save className="w-3.5 h-3.5" /> Save All
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="about" className="mt-6 space-y-3">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-2">
            <div className="flex justify-between text-sm"><span className="text-gray-400">ProwlrBot Version</span><span className="text-white font-mono">{version || '—'}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-400">Studio</span><span className="text-white font-mono">Phase 2</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-400">Backend</span><span className="text-white font-mono">:8088</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-400">Studio Backend</span><span className="text-white font-mono">:3211</span></div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

- [x] **Step 2: Add route, commit**

```tsx
import { SettingsPage } from '@/pages/SettingsPage';
<Route path="/settings" element={<SettingsPage />} />
```

```bash
git add frontend/src/pages/SettingsPage.tsx frontend/src/App.tsx
git commit -m "feat(pages): Settings page — model config, env vars, about (replaces console)"
```

---

### Task 3.7: Update sidebar navigation

**Files:**
- Modify: whichever sidebar/nav component exists in Studio (check `frontend/src/components/` or `frontend/src/App.tsx`)

- [x] **Step 1: Find sidebar component**

Run `grep -r "AgentHub\|Workspace\|/workspace" frontend/src/ --include="*.tsx" -l` to find the nav.

- [x] **Step 2: Add nav entries for Chat, Channels, Monitors, Crons, Settings**

Add links to `/chat`, `/channels`, `/monitors`, `/crons`, `/settings` in the sidebar nav, grouping them under a "ProwlrBot" section heading, below the existing Studio sections.

- [x] **Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat(nav): add Chat, Channels, Monitors, Crons, Settings to sidebar"
```

---

## Chunk 4: Canvas Annotation, Export, and Agent Redirect

Phase 1 Canvas only has approve/reject. Phase 2 adds annotations, agent redirect, merge-to-summary, and export.

### Task 4.1: Canvas annotation and export

**Files:**
- Modify: `frontend/src/pages/CollaborationCanvasPage.tsx`

- [x] **Step 1: Read current CollaborationCanvasPage.tsx**

Read the full file to understand current structure before editing.

- [x] **Step 2: Add annotation panel, merge button, export**

Extend the existing finding cards with:
- **Annotation field**: `<textarea>` per card, persisted to local state (and `PATCH /api/studio/canvas/findings/{id}/annotation` when saved)
- **Redirect to agent button**: `<Button>Investigate further</Button>` — opens a dialog to select an agent, then POSTs `{ task: finding.content }` to `/api/studio/agents/{agentId}/run`
- **Merge button** (in header): selects multiple findings and merges them into a single summary card. Summary is created locally.
- **Export button** (in header): downloads `canvas-export-{date}.json` with all findings and their statuses/annotations

- [x] **Step 3: Commit**

```bash
git add frontend/src/pages/CollaborationCanvasPage.tsx
git commit -m "feat(canvas): annotation per finding, agent redirect, merge, JSON export"
```

---

## Chunk 5: ProwlrBot Workflow Node Types

Five new ReactFlow node types for the workflow builder that wrap ProwlrBot capabilities.

### Task 5.1: ProwlrBot workflow nodes

**Files:**
- Create: `frontend/src/features/workflow-builder/nodes/prowlrbot/ProwlrbotAgentNode.tsx`
- Create: `frontend/src/features/workflow-builder/nodes/prowlrbot/ChannelTriggerNode.tsx`
- Create: `frontend/src/features/workflow-builder/nodes/prowlrbot/MonitorTriggerNode.tsx`
- Create: `frontend/src/features/workflow-builder/nodes/prowlrbot/RoarMessageNode.tsx`
- Create: `frontend/src/features/workflow-builder/nodes/prowlrbot/HubTaskNode.tsx`
- Modify: workflow builder node registry (wherever existing nodes are registered)

- [x] **Step 1: Read existing node structure**

Read one existing node file (e.g. an `AI` or `Core` node) to understand the props interface, handle positions, and styling conventions before creating new ones.

- [x] **Step 2: Create ProwlrbotAgentNode**

```tsx
// ProwlrbotAgentNode.tsx
// Wraps a ProwlrBot agent as a workflow node.
// Inputs: agent_id (string), query (string), autonomy (string?), timeout_s (number?)
// Outputs: response (string), artifacts (File[]), cost (CostSummary), run_id (string)
// Color: purple border (matches Agent Hub purple theme)
// Icon: Bot from lucide
```

- [x] **Step 3: Create ChannelTriggerNode**

```tsx
// Entry point node. Triggers workflow from channel message.
// Config: channel (string), filter (regex?)
// Outputs: message, sender, channel_id, metadata
// Color: blue border. Icon: Radio/MessageCircle
```

- [x] **Step 4: Create MonitorTriggerNode**

```tsx
// Entry point node. Triggers from monitor alert.
// Config: monitor_id (string), severity (string[]?)
// Outputs: alert, diff, url
// Color: orange border. Icon: AlertTriangle
```

- [x] **Step 5: Create RoarMessageNode**

```tsx
// Send/receive ROAR protocol messages between agents.
// Config: target_agent (string), message (string), protocol (string?)
// Outputs: response (string), status (string)
// Color: teal border. Icon: Zap
```

- [x] **Step 6: Create HubTaskNode**

```tsx
// Create/claim/complete ProwlrHub tasks.
// Config: action (create/claim/complete/fail), task_id?, description?
// Outputs: task_id, status, assigned_to?
// Color: green border. Icon: CheckSquare
```

- [x] **Step 7: Register all 5 nodes in the node registry**

Find the file that maps node type strings to components (e.g. `nodeTypes` object). Add:
```ts
'prowlrbot.agent': ProwlrbotAgentNode,
'prowlrbot.channel-trigger': ChannelTriggerNode,
'prowlrbot.monitor-trigger': MonitorTriggerNode,
'prowlrbot.roar-message': RoarMessageNode,
'prowlrbot.hub-task': HubTaskNode,
```

- [x] **Step 8: Add to component palette**

Find the component picker/library panel. Add a "ProwlrBot" section with these 5 nodes, descriptions matching the spec.

- [x] **Step 9: Commit**

```bash
git add frontend/src/features/workflow-builder/nodes/prowlrbot/
git commit -m "feat(workflow): 5 ProwlrBot node types — Agent, ChannelTrigger, MonitorTrigger, RoarMessage, HubTask"
```

---

## Chunk 6: Integration Tests and Verification

### Task 6.1: Run all tests and verify

- [x] **Step 1: Run ProwlrBot tests**

```bash
cd /home/anon/dev/prowlrbot && pytest -x -q 2>&1 | tail -20
```

Expect: all existing tests pass. No regressions from proxy module or nav changes.

- [x] **Step 2: Run Studio TypeScript check**

```bash
cd /home/anon/dev/prowrl-studio && npx tsc --noEmit
```

Expect: zero type errors.

- [x] **Step 3: Build Studio frontend**

```bash
cd /home/anon/dev/prowrl-studio && bun run build 2>&1 | tail -10
```

Expect: successful build with no errors.

- [x] **Step 4: Smoke test workspace tabs**

Run Studio and verify each of the 12 tabs renders without crashing. BrowserTab, FilesTab, MemoryTab, ConfigTab should show their empty states (not the old PlaceholderTab).

- [x] **Step 5: Smoke test layout modes**

Verify all 6 layout mode buttons in the workspace toolbar work: tile, stack, float, split, pip, focus.

- [x] **Step 6: Final commit + push**

```bash
cd /home/anon/dev/prowrl-studio && git push origin main
cd /home/anon/dev/prowlrbot && git push origin main
```

---

## Summary

| Chunk | Scope | Key files |
|-------|-------|-----------|
| 1 | 4 workspace tabs (Browser, Files, Memory, Config) | `tabs/BrowserTab.tsx`, `FilesTab.tsx`, `MemoryTab.tsx`, `ConfigTab.tsx` |
| 2 | 4 layout modes (Float, Split, PiP, Focus) | `layouts/FloatLayout.tsx`, `SplitLayout.tsx`, `PiPLayout.tsx`, `FocusLayout.tsx` |
| 3 | 5 console pages + NestJS proxy | `ChatPage.tsx`, `ChannelsPage.tsx`, `MonitorsPage.tsx`, `CronPage.tsx`, `SettingsPage.tsx`, `prowlrbot.controller.ts` |
| 4 | Canvas annotation + export | `CollaborationCanvasPage.tsx` |
| 5 | 5 ProwlrBot workflow nodes | `nodes/prowlrbot/*.tsx` |
| 6 | Tests + build verification | — |
