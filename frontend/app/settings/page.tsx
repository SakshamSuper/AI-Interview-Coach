"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Settings, Server, Database, Brain, Cpu, Shield,
  Activity, CheckCircle2, XCircle, AlertTriangle,
  RefreshCw, Search, ChevronDown, ChevronUp, Zap,
  BookOpen, Layers, Clock,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

const API = process.env.NEXT_PUBLIC_API_URL || "/api/py";

// ─── Types ────────────────────────────────────────────────────────────────────

interface HealthData {
  status: string;
  app_name: string;
  environment: string;
  database: string;
  llm_provider: string;
  vector_store: string;
  knowledge_base_ready: boolean;
  version: string;
}

interface KBData {
  is_indexed: boolean;
  index_directory: string;
  total_chunks: number;
  dimension: number | null;
  topics: string[];
  documents: string[];
}

interface MLData {
  has_data: boolean;
  model_architecture?: string;
  disclaimer?: string;
  readiness_label?: string | null;
  readiness_score?: number | null;
}

interface AnalyticsData {
  completed_interviews?: number;
  average_overall_score?: number;
}

interface UserData {
  name?: string;
  email?: string;
  target_role?: string;
}

interface KBSource {
  topic?: string;
  score?: number;
  content_preview?: string;
}

interface KBQueryResult {
  query: string;
  confidence_score: number;
  has_grounding: boolean;
  context_text: string;
  sources: KBSource[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function fetchJSON<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API}${path}`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span className={`inline-block w-2 h-2 rounded-full mr-1.5 ${ok ? "bg-emerald-400" : "bg-red-400"}`} />
  );
}

function SectionHeader({ icon: Icon, title, subtitle }: {
  icon: React.ElementType;
  title: string;
  subtitle: string;
}) {
  return (
    <div className="flex items-start gap-2 mb-1">
      <Icon className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
      <div>
        <h2 className="text-sm font-bold text-slate-800">{title}</h2>
        <p className="text-[11px] text-slate-400">{subtitle}</p>
      </div>
    </div>
  );
}

function Row({ label, value, badge }: {
  label: string;
  value?: React.ReactNode;
  badge?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-200 last:border-0">
      <span className="text-xs text-slate-500">{label}</span>
      <div className="flex items-center gap-2">
        {badge}
        {value && <span className="text-xs font-semibold text-slate-800 text-right max-w-[200px] truncate">{value}</span>}
      </div>
    </div>
  );
}

// ─── Sub-panels ───────────────────────────────────────────────────────────────

function HealthBanner({ health, lastRefresh, onRefresh }: {
  health: HealthData | null;
  lastRefresh: Date | null;
  onRefresh: () => void;
}) {
  const isHealthy = health?.status === "healthy";
  const isDbOk = health?.database === "connected";
  const isKbReady = health?.knowledge_base_ready ?? false;

  if (!health) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-500/5 p-4 flex items-center gap-3">
        <XCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
        <div className="flex-1">
          <p className="text-sm font-semibold text-red-600">Backend Unreachable</p>
          <p className="text-xs text-slate-400">FastAPI is not responding on port 8000.</p>
        </div>
        <Button variant="outline" size="sm" onClick={onRefresh}>
          <RefreshCw className="w-3.5 h-3.5" /> Retry
        </Button>
      </div>
    );
  }

  return (
    <div className={`rounded-xl border p-4 ${isHealthy ? "border-emerald-500/25 bg-emerald-50" : "border-amber-500/25 bg-amber-50"}`}>
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {isHealthy
            ? <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            : <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
          }
          <div>
            <p className="text-sm font-bold text-slate-900">
              {health.app_name} <span className="text-slate-400 font-normal">v{health.version}</span>
            </p>
            <p className="text-xs text-slate-500 capitalize">{health.environment} &middot; {health.status}</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1"><StatusDot ok={isDbOk} /><span className="text-slate-500">Database</span></span>
            <span className="flex items-center gap-1"><StatusDot ok={isKbReady} /><span className="text-slate-500">FAISS</span></span>
            <span className="flex items-center gap-1"><StatusDot ok={isHealthy} /><span className="text-slate-500">API</span></span>
          </div>
          <Button variant="ghost" size="sm" onClick={onRefresh} className="text-slate-500 hover:text-slate-800">
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>
      {lastRefresh && (
        <p className="text-[10px] text-slate-500 mt-2 flex items-center gap-1">
          <Clock className="w-3 h-3" />
          Last refreshed: {lastRefresh.toLocaleTimeString()}
        </p>
      )}
    </div>
  );
}

function LLMPanel({ health }: { health: HealthData | null }) {
  const provider = health?.llm_provider ?? "unknown";
  return (
    <Card>
      <CardHeader>
        <SectionHeader icon={Cpu} title="AI & LLM Configuration" subtitle="Generative AI model orchestration" />
      </CardHeader>
      <CardContent className="space-y-0">
        <Row label="Configured Provider" value={provider.toUpperCase()} badge={<Badge variant="info" size="sm">{provider}</Badge>} />
        <Row label="Active Runtime Client" badge={<Badge variant="warning" size="sm">LocalMockLLMClient</Badge>} value="Hermetic offline fallback" />
        <Row label="Offline Reason" value="No GROQ_API_KEY / OPENAI_API_KEY set" />
        <Row label="Embedding Model" value="sentence-transformers/all-MiniLM-L6-v2" />
        <Row label="Embedding Dimensions" badge={<Badge variant="default" size="sm">384-dim</Badge>} />
        <Row label="RAG Similarity Threshold" badge={<Badge variant="warning" size="sm">0.25 (Calibrated)</Badge>} />
        <Row label="Mock Mode" badge={<Badge variant="danger" size="sm">ACTIVE</Badge>} value="Deterministic canned responses" />
      </CardContent>
    </Card>
  );
}

function RAGPanel({ kb }: { kb: KBData | null }) {
  const [expanded, setExpanded] = useState(false);
  if (!kb) return (
    <Card>
      <CardHeader><SectionHeader icon={BookOpen} title="RAG Knowledge Base" subtitle="FAISS vector index" /></CardHeader>
      <CardContent><p className="text-xs text-slate-400">Loading…</p></CardContent>
    </Card>
  );

  return (
    <Card>
      <CardHeader>
        <SectionHeader icon={BookOpen} title="RAG Knowledge Base" subtitle="FAISS vector index telemetry" />
      </CardHeader>
      <CardContent className="space-y-0">
        <Row label="Index Status" badge={kb.is_indexed ? <Badge variant="success" size="sm">Indexed</Badge> : <Badge variant="danger" size="sm">Not Indexed</Badge>} />
        <Row label="Total Chunks" badge={<Badge variant="info" size="sm">{kb.total_chunks} chunks</Badge>} />
        <Row label="Vector Dimensions" badge={<Badge variant="default" size="sm">{kb.dimension ?? 384}-dim</Badge>} />
        <Row label="Index Path" value={kb.index_directory} />
        <Row label="Similarity Search" value="Inner Product (Normalized Cosine)" />
        <div className="pt-2">
          <button
            onClick={() => setExpanded(v => !v)}
            className="flex items-center gap-1 text-[11px] text-blue-600 hover:text-blue-500 transition-colors"
          >
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            {kb.topics.length} domains indexed
          </button>
          {expanded && (
            <div className="mt-2 grid grid-cols-1 gap-1">
              {kb.topics.map((t) => (
                <div key={t} className="flex items-center gap-2 rounded bg-slate-50 px-2.5 py-1.5">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600 flex-shrink-0" />
                  <span className="text-xs text-slate-700">{t}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function MLPanel({ ml }: { ml: MLData | null }) {
  if (!ml) return (
    <Card>
      <CardHeader><SectionHeader icon={Brain} title="ML Readiness Classifier" subtitle="Scikit-Learn inference pipeline" /></CardHeader>
      <CardContent><p className="text-xs text-slate-400">Loading…</p></CardContent>
    </Card>
  );

  const arch = ml.model_architecture ?? "Unknown";
  const label = ml.readiness_label;

  function readinessColor(l: string | null | undefined) {
    if (!l) return "text-slate-500";
    const lower = l.toLowerCase();
    if (lower.includes("ready") && !lower.includes("almost")) return "text-emerald-600";
    if (lower.includes("almost") || lower.includes("borderline")) return "text-amber-600";
    return "text-red-600";
  }

  return (
    <Card>
      <CardHeader>
        <SectionHeader icon={Brain} title="ML Readiness Classifier" subtitle="Scikit-Learn inference pipeline" />
      </CardHeader>
      <CardContent className="space-y-0">
        <Row label="Model Architecture" badge={<Badge variant="purple" size="sm">{arch}</Badge>} />
        <Row label="Artifact Filename" value="interview_readiness_rf.joblib" />
        <Row label="Filename vs Runtime" badge={<Badge variant="warning" size="sm">Mismatch — LR won CV</Badge>} />
        <Row label="Training Accuracy" badge={<Badge variant="success" size="sm">97.92%</Badge>} />
        <Row label="Macro F1 (5-fold CV)" badge={<Badge variant="success" size="sm">96.16%</Badge>} />
        <Row label="Feature Columns" badge={<Badge variant="info" size="sm">12 features</Badge>} />
        <Row label="Training Dataset" value="Synthetic (disclosed)" />
        {ml.has_data && label && (
          <div className="pt-3 mt-1 border-t border-slate-200">
            <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-1">Current Prediction (User 1)</p>
            <p className={`text-sm font-bold ${readinessColor(label)}`}>{label}</p>
            {ml.readiness_score != null && (
              <p className="text-xs text-slate-500 font-mono">{ml.readiness_score.toFixed(1)}% readiness score</p>
            )}
          </div>
        )}
        {ml.disclaimer && (
          <p className="text-[10px] text-slate-500 mt-3 leading-relaxed border-t border-slate-200 pt-2">
            {ml.disclaimer}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function DatabasePanel({ health, analytics, user }: {
  health: HealthData | null;
  analytics: AnalyticsData | null;
  user: UserData | null;
}) {
  const isConnected = health?.database === "connected";
  return (
    <Card>
      <CardHeader>
        <SectionHeader icon={Database} title="Database & Storage" subtitle="SQLite persistence layer" />
      </CardHeader>
      <CardContent className="space-y-0">
        <Row label="Connection" badge={isConnected ? <Badge variant="success" size="sm">Connected</Badge> : <Badge variant="danger" size="sm">Error</Badge>} />
        <Row label="Engine" value="SQLite + SQLAlchemy 2.0" />
        <Row label="Path" value="data/interview_coach.db" />
        <Row label="Tables" badge={<Badge variant="info" size="sm">10 tables</Badge>} />
        {analytics && (
          <>
            <Row label="Completed Sessions" badge={<Badge variant="default" size="sm">{analytics.completed_interviews ?? 0}</Badge>} />
            <Row label="Avg Overall Score" badge={<Badge variant="info" size="sm">{analytics.average_overall_score?.toFixed(1) ?? "—"}</Badge>} />
          </>
        )}
        {user && (
          <div className="pt-3 mt-1 border-t border-slate-200">
            <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-1">Active Candidate (User 1)</p>
            <Row label="Name" value={user.name} />
            <Row label="Target Role" value={user.target_role ?? "—"} />
            <Row label="Email" value={user.email ?? "—"} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ServicesPanel({ health }: { health: HealthData | null }) {
  const services = [
    { name: "FastAPI REST API", port: 8000, ok: !!health },
    { name: "Next.js Frontend", port: 3000, ok: true },
    { name: "Streamlit Fallback", port: 8501, ok: null as boolean | null },
    { name: "FAISS Vector Store", port: null as number | null, ok: health?.knowledge_base_ready ?? false },
    { name: "SQLite Database", port: null as number | null, ok: health?.database === "connected" },
  ];

  return (
    <Card>
      <CardHeader>
        <SectionHeader icon={Server} title="Service Topology" subtitle="Active microservice ports & health" />
      </CardHeader>
      <CardContent>
        <div className="space-y-0">
          {services.map((s) => (
            <div key={s.name} className="flex items-center justify-between py-2 border-b border-slate-200 last:border-0">
              <div className="flex items-center gap-2">
                {s.ok === null
                  ? <span className="inline-block w-2 h-2 rounded-full bg-slate-300 mr-0.5" />
                  : <StatusDot ok={s.ok} />
                }
                <span className="text-xs text-slate-700">{s.name}</span>
              </div>
              <div className="flex items-center gap-2">
                {s.port && <span className="text-[10px] font-mono text-slate-400">:{s.port}</span>}
                <Badge variant={s.ok === null ? "default" : s.ok ? "success" : "danger"} size="sm">
                  {s.ok === null ? "Unknown" : s.ok ? "Active" : "Down"}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function RAGSandbox() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<KBQueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [topK, setTopK] = useState(3);

  const handleQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API}/knowledge-base/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), top_k: topK, threshold: 0.25 }),
      });
      if (!res.ok) {
        setError(`Backend error: ${res.status}`);
      } else {
        setResult(await res.json());
      }
    } catch {
      setError("Network error — is FastAPI running on port 8000?");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleQuery(); }
  };

  return (
    <Card>
      <CardHeader>
        <SectionHeader icon={Search} title="RAG Query Sandbox" subtitle="Live FAISS vector search — test grounded retrieval" />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="e.g. How do you design a distributed cache?"
            className="flex-1 bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-800 placeholder:text-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
          />
          <select
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="bg-white border border-slate-300 rounded-lg px-2 py-2 text-xs text-slate-700 focus:outline-none"
          >
            <option value={1}>Top 1</option>
            <option value={2}>Top 2</option>
            <option value={3}>Top 3</option>
            <option value={4}>Top 4</option>
          </select>
          <Button variant="primary" size="sm" onClick={handleQuery} disabled={loading || !query.trim()}>
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
            {loading ? "Searching…" : "Search"}
          </Button>
        </div>

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-3">
            <p className="text-xs text-red-600">{error}</p>
          </div>
        )}

        {result && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              {result.has_grounding ? <Badge variant="success" size="sm">Grounded</Badge> : <Badge variant="warning" size="sm">Low confidence</Badge>}
              <span className="text-xs text-slate-500 font-mono">confidence: {(result.confidence_score * 100).toFixed(1)}%</span>
              <span className="text-xs text-slate-400">{result.sources.length} sources</span>
            </div>
            {result.sources.length > 0 && (
              <div className="space-y-2">
                {result.sources.map((src, i) => (
                  <div key={i} className="rounded-lg bg-slate-50 border border-slate-300/40 p-3">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <Layers className="w-3 h-3 text-blue-600" />
                        <span className="text-[11px] font-bold text-blue-500">{src.topic ?? "Unknown"}</span>
                      </div>
                      {src.score != null && (
                        <span className="text-[10px] font-mono text-slate-400">score: {(src.score * 100).toFixed(1)}%</span>
                      )}
                    </div>
                    {src.content_preview && (
                      <p className="text-[11px] text-slate-500 leading-relaxed line-clamp-3">{src.content_preview}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
            {result.context_text && (
              <details>
                <summary className="text-[11px] text-blue-600 cursor-pointer hover:text-blue-500 select-none">
                  View full grounded context ({result.context_text.length} chars)
                </summary>
                <pre className="mt-2 text-[10px] text-slate-500 bg-slate-50 rounded p-3 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                  {result.context_text}
                </pre>
              </details>
            )}
          </div>
        )}

        {!result && !loading && !error && (
          <p className="text-[11px] text-slate-500 text-center py-2">
            Enter a technical interview question to test RAG retrieval from the FAISS index.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [kb, setKb] = useState<KBData | null>(null);
  const [ml, setMl] = useState<MLData | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [user, setUser] = useState<UserData | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    const [h, k, m, a, u] = await Promise.all([
      fetchJSON<HealthData>("/health"),
      fetchJSON<KBData>("/knowledge-base"),
      fetchJSON<MLData>("/ml/readiness?user_id=1"),
      fetchJSON<AnalyticsData>("/analytics/1"),
      fetchJSON<UserData>("/users/1"),
    ]);
    setHealth(h);
    setKb(k);
    setMl(m);
    setAnalytics(a);
    setUser(u);
    setLastRefresh(new Date());
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30_000);
    return () => clearInterval(interval);
  }, [refresh]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900 flex items-center gap-2">
            <Settings className="w-6 h-6 text-blue-600" />
            Settings &amp; System Status
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Live telemetry — AI providers, vector store, ML classifier, database, and RAG sandbox.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {loading && <RefreshCw className="w-4 h-4 text-slate-400 animate-spin" />}
          <Button variant="outline" size="sm" onClick={refresh} disabled={loading}>
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </Button>
        </div>
      </div>

      {/* System Health Banner */}
      <HealthBanner health={health} lastRefresh={lastRefresh} onRefresh={refresh} />

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LLMPanel health={health} />
        <RAGPanel kb={kb} />
        <MLPanel ml={ml} />
        <DatabasePanel health={health} analytics={analytics} user={user} />
        <div className="lg:col-span-2">
          <ServicesPanel health={health} />
        </div>
      </div>

      {/* RAG Query Sandbox */}
      <RAGSandbox />

      {/* System info footer */}
      <div className="rounded-xl border border-slate-200 bg-white/30 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Shield className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">System Info</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          {[
            { label: "Backend", value: "FastAPI + Uvicorn" },
            { label: "Primary Frontend", value: "Next.js 16.3.4" },
            { label: "Python", value: "3.14.x" },
            { label: "Node.js", value: "v24.x" },
            { label: "ORM", value: "SQLAlchemy 2.0" },
            { label: "Vector DB", value: "FAISS (CPU, Inner Product)" },
            { label: "Agent Framework", value: "LangGraph + LangChain" },
            { label: "CV Pipeline", value: "MediaPipe + OpenCV" },
          ].map(({ label, value }) => (
            <div key={label} className="space-y-0.5">
              <p className="text-slate-400">{label}</p>
              <p className="font-semibold text-slate-700">{value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}