"use client";

import React, { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import {
  Search,
  Database,
  FileText,
  Layers,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ChevronDown,
  ChevronUp,
  BookOpen,
  Cpu,
  ArrowRight,
  Sparkles,
  RefreshCw,
  Tag,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";

// ─── API Types (mirrors backend Pydantic schemas exactly) ─────────────────────

interface KBSource {
  source: string;
  topic: string;
  chunk_id: string;
  score: number;
}

interface KBQueryResponse {
  query: string;
  confidence_score: number;
  has_grounding: boolean;
  context_text: string;
  sources: KBSource[];
}

interface KBStatusResponse {
  is_indexed: boolean;
  index_directory: string;
  total_chunks: number;
  dimension: number | null;
  topics: string[];
  documents: string[];
}

// ─── API layer ────────────────────────────────────────────────────────────────

async function fetchKBStatus(): Promise<KBStatusResponse> {
  const res = await fetch("/api/py/knowledge-base");
  if (!res.ok) throw new Error(`Status check failed: ${res.status}`);
  return res.json();
}

async function queryKB(
  query: string,
  topK: number,
  threshold: number,
  topicFilter?: string
): Promise<KBQueryResponse> {
  const body: Record<string, unknown> = { query, top_k: topK, threshold };
  if (topicFilter) body.topic_filter = topicFilter;

  const res = await fetch("/api/py/knowledge-base/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Query failed." }));
    const detail = Array.isArray(err.detail)
      ? err.detail.map((d: { msg: string }) => d.msg).join("; ")
      : err.detail || `Error ${res.status}`;
    throw new Error(detail);
  }

  return res.json();
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function scoreColor(score: number): string {
  if (score >= 0.45) return "text-emerald-600";
  if (score >= 0.30) return "text-amber-600";
  return "text-slate-500";
}

function scoreVariant(score: number): "success" | "warning" | "default" {
  if (score >= 0.45) return "success";
  if (score >= 0.30) return "warning";
  return "default";
}

function progressColor(score: number): "emerald" | "amber" | "blue" {
  if (score >= 0.45) return "emerald";
  if (score >= 0.30) return "amber";
  return "blue";
}

function topicIcon(topic: string): React.ReactNode {
  const t = topic.toLowerCase();
  if (t.includes("python")) return <span className="text-[10px] font-bold text-blue-600">PY</span>;
  if (t.includes("data struct")) return <span className="text-[10px] font-bold text-purple-400">DSA</span>;
  if (t.includes("sql")) return <span className="text-[10px] font-bold text-amber-600">SQL</span>;
  if (t.includes("machine")) return <span className="text-[10px] font-bold text-emerald-600">ML</span>;
  if (t.includes("genai") || t.includes("rag")) return <span className="text-[10px] font-bold text-blue-600">AI</span>;
  if (t.includes("system")) return <span className="text-[10px] font-bold text-rose-400">SD</span>;
  if (t.includes("cloud") || t.includes("devops")) return <span className="text-[10px] font-bold text-sky-400">☁</span>;
  return <span className="text-[10px] font-bold text-slate-500">?</span>;
}

const EXAMPLE_QUERIES: { topic: string; query: string }[] = [
  { topic: "System Design", query: "How do you design a distributed caching system?" },
  { topic: "GenAI & RAG", query: "What is retrieval augmented generation and how does it reduce hallucinations?" },
  { topic: "DSA", query: "How does binary search work and what is its time complexity?" },
  { topic: "Python & OOP", query: "What is the difference between a class method and a static method?" },
  { topic: "Machine Learning", query: "How does gradient descent work in neural network training?" },
  { topic: "SQL & DBMS", query: "What is the difference between INNER JOIN and LEFT JOIN?" },
];

// ─── RAG Process Explainer ────────────────────────────────────────────────────

function RagExplainer() {
  const [expanded, setExpanded] = useState(false);
  const steps = [
    { label: "Question", sub: "Your technical query" },
    { label: "Embedding", sub: "all-MiniLM-L6-v2 → 384-dim vector" },
    { label: "FAISS Search", sub: "Cosine similarity over 31 indexed chunks" },
    { label: "Retrieval", sub: "Top-K chunks above threshold returned" },
    { label: "Context", sub: "Grounded source passages with scores" },
  ];

  return (
    <Card>
      <button
        className="w-full text-left"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <CardHeader>
          <div>
            <CardTitle>How It Works</CardTitle>
            <p className="text-xs text-slate-500 mt-0.5">Semantic retrieval from technical knowledge base</p>
          </div>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-slate-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-500" />
          )}
        </CardHeader>
      </button>

      {expanded && (
        <CardContent>
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-0">
            {steps.map((step, i) => (
              <React.Fragment key={step.label}>
                <div className="flex flex-col items-center text-center min-w-[80px]">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-1.5">
                    <span className="text-xs font-bold text-blue-600">{i + 1}</span>
                  </div>
                  <div className="text-xs font-semibold text-slate-800">{step.label}</div>
                  <div className="text-[10px] text-slate-400 mt-0.5 leading-tight max-w-[90px]">{step.sub}</div>
                </div>
                {i < steps.length - 1 && (
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500 flex-shrink-0 mx-2 mt-0 sm:-mt-5 rotate-90 sm:rotate-0" />
                )}
              </React.Fragment>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            {[
              { label: "Vector Dims", value: "384" },
              { label: "Similarity", value: "Cosine" },
              { label: "Index Type", value: "FAISS IP" },
              { label: "Threshold", value: "0.25" },
            ].map((m) => (
              <div key={m.label} className="rounded-lg bg-slate-50 border border-slate-300/40 px-3 py-2">
                <div className="text-xs font-bold text-slate-800">{m.value}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">{m.label}</div>
              </div>
            ))}
          </div>
          <p className="text-[11px] text-slate-400 mt-3 leading-relaxed">
            Note: this endpoint returns grounded retrieval context only. LLM-generated answers are produced
            inside the interview session pipeline — not exposed as a standalone API endpoint.
          </p>
        </CardContent>
      )}
    </Card>
  );
}

// ─── Source Result Card ───────────────────────────────────────────────────────

function SourceCard({ source, index, contextText }: { source: KBSource; index: number; contextText: string }) {
  const [expanded, setExpanded] = useState(false);

  // Extract just this source's passage from the combined context_text
  const sourceMarker = `[Source ${index}:`;
  const start = contextText.indexOf(sourceMarker);
  const nextMarker = contextText.indexOf(`[Source ${index + 1}:`, start + 1);
  const passage = start !== -1
    ? contextText.slice(start, nextMarker !== -1 ? nextMarker : undefined).replace(/^.*?\n/, "").trim()
    : "";

  return (
    <div className="border border-slate-300/50 rounded-xl bg-slate-50 overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 px-4 py-3">
        <div className="flex items-start gap-3 min-w-0 flex-1">
          <div className="w-6 h-6 rounded bg-slate-100 border border-slate-300 flex items-center justify-center flex-shrink-0 mt-0.5">
            <span className="text-[10px] font-bold text-slate-500">{index}</span>
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-semibold text-slate-800 truncate">{source.source}</span>
              <div className="flex items-center gap-1.5 px-1.5 py-0.5 rounded bg-slate-50 border border-slate-300/40">
                {topicIcon(source.topic)}
                <span className="text-[10px] text-slate-500">{source.topic}</span>
              </div>
            </div>
            <div className="flex items-center gap-3 mt-1">
              <span className={`text-xs font-bold font-mono ${scoreColor(source.score)}`}>
                {(source.score * 100).toFixed(1)}% relevance
              </span>
              <Badge variant={scoreVariant(source.score)} size="sm">
                {source.score >= 0.45 ? "High Relevance" : source.score >= 0.30 ? "Moderate" : "Low"}
              </Badge>
            </div>
          </div>
        </div>

        {passage && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="flex-shrink-0 text-slate-400 hover:text-slate-700 transition-colors p-1"
            aria-label="Toggle passage"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        )}
      </div>

      {/* Relevance bar */}
      <div className="px-4 pb-2">
        <ProgressBar
          value={source.score * 100}
          color={progressColor(source.score)}
          size="sm"
          showPercentage={false}
        />
      </div>

      {/* Expandable passage */}
      {expanded && passage && (
        <div className="border-t border-slate-200 px-4 py-3">
          <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-2 font-semibold">Retrieved passage</p>
          <pre className="text-xs text-slate-700 whitespace-pre-wrap font-sans leading-relaxed bg-slate-50 border border-slate-200 rounded-lg p-3 max-h-64 overflow-y-auto">
            {passage}
          </pre>
        </div>
      )}
    </div>
  );
}

// ─── KB Status Bar ────────────────────────────────────────────────────────────

function KBStatusBar({ status }: { status: KBStatusResponse }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {[
        {
          label: "Status",
          value: status.is_indexed ? "Indexed" : "Not Indexed",
          icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />,
          ok: status.is_indexed,
        },
        {
          label: "Chunks",
          value: String(status.total_chunks),
          icon: <Layers className="w-3.5 h-3.5 text-blue-600" />,
          ok: true,
        },
        {
          label: "Topics",
          value: String(status.topics.length),
          icon: <Tag className="w-3.5 h-3.5 text-purple-400" />,
          ok: true,
        },
        {
          label: "Dimensions",
          value: status.dimension ? String(status.dimension) : "—",
          icon: <Cpu className="w-3.5 h-3.5 text-amber-600" />,
          ok: true,
        },
      ].map((m) => (
        <div
          key={m.label}
          className="rounded-xl bg-slate-50 border border-slate-300/50 px-4 py-3 flex items-center gap-3"
        >
          {m.icon}
          <div>
            <div className={`text-sm font-bold ${m.ok ? "text-slate-900" : "text-red-600"}`}>{m.value}</div>
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">{m.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Domain Grid ──────────────────────────────────────────────────────────────

function DomainGrid({
  topics,
  selected,
  onSelect,
}: {
  topics: string[];
  selected: string;
  onSelect: (t: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => onSelect("")}
        className={[
          "text-xs px-3 py-1.5 rounded-lg border transition-colors font-medium",
          selected === ""
            ? "bg-blue-600 border-blue-500 text-white"
            : "bg-slate-50 border-slate-300 text-slate-500 hover:text-slate-800 hover:border-slate-300",
        ].join(" ")}
      >
        All Topics
      </button>
      {topics.map((t) => (
        <button
          key={t}
          onClick={() => onSelect(selected === t ? "" : t)}
          className={[
            "text-xs px-3 py-1.5 rounded-lg border transition-colors font-medium flex items-center gap-1.5",
            selected === t
              ? "bg-blue-600 border-blue-500 text-white"
              : "bg-slate-50 border-slate-300 text-slate-500 hover:text-slate-800 hover:border-slate-300",
          ].join(" ")}
        >
          {topicIcon(t)}
          {t}
        </button>
      ))}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

type SearchState = "idle" | "searching" | "success" | "no_results" | "error";

export default function KnowledgePage() {
  const [kbStatus, setKbStatus] = useState<KBStatusResponse | null>(null);
  const [statusError, setStatusError] = useState("");
  const [query, setQuery] = useState("");
  const [topicFilter, setTopicFilter] = useState("");
  const [searchState, setSearchState] = useState<SearchState>("idle");
  const [searchError, setSearchError] = useState("");
  const [result, setResult] = useState<KBQueryResponse | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load KB status on mount
  useEffect(() => {
    fetchKBStatus()
      .then((s) => setKbStatus(s))
      .catch((e) => setStatusError(e.message));
  }, []);

  const handleSearch = useCallback(async (overrideQuery?: string) => {
    const q = (overrideQuery ?? query).trim();
    if (!q) return;

    setSearchState("searching");
    setSearchError("");
    setResult(null);

    try {
      const data = await queryKB(q, 4, 0.25, topicFilter || undefined);
      if (!data.has_grounding || data.sources.length === 0) {
        setSearchState("no_results");
      } else {
        setResult(data);
        setSearchState("success");
      }
    } catch (e: unknown) {
      setSearchError(e instanceof Error ? e.message : "Search failed.");
      setSearchState("error");
    }
  }, [query, topicFilter]);

  const handleExampleClick = (exQuery: string) => {
    setQuery(exQuery);
    handleSearch(exQuery);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") handleSearch();
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="pb-6 border-b border-slate-200">
        <h1 className="text-xl font-semibold tracking-tight text-slate-900">Knowledge Base</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Semantic search over the technical interview knowledge base · powered by FAISS + SentenceTransformers
        </p>
      </div>

      {/* KB Status */}
      {statusError ? (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          Knowledge base status unavailable: {statusError}
        </div>
      ) : kbStatus ? (
        <KBStatusBar status={kbStatus} />
      ) : (
        <div className="h-16 rounded-xl bg-slate-50 animate-pulse" />
      )}

      {/* Domain Filter (topics from backend) */}
      {kbStatus && kbStatus.topics.length > 0 && (
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Technical Domains</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                {kbStatus.topics.length} domains · {kbStatus.documents.length} source documents
              </p>
            </div>
            <BookOpen className="w-4 h-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <DomainGrid
              topics={kbStatus.topics}
              selected={topicFilter}
              onSelect={setTopicFilter}
            />
            {/* Document list */}
            <div className="mt-4 pt-4 border-t border-slate-200">
              <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-2">Source Documents</p>
              <div className="flex flex-wrap gap-2">
                {kbStatus.documents.map((doc) => (
                  <div
                    key={doc}
                    className="flex items-center gap-1.5 text-[11px] text-slate-500 bg-slate-50 border border-slate-300/40 rounded px-2 py-1"
                  >
                    <FileText className="w-3 h-3 text-slate-400" />
                    {doc}
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Semantic Search</CardTitle>
            <p className="text-xs text-slate-500 mt-0.5">
              Ask a technical question — the backend retrieves the most relevant knowledge base passages
            </p>
          </div>
          <Database className="w-4 h-4 text-blue-600" />
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search input */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask the technical knowledge base..."
                disabled={searchState === "searching"}
                className="w-full pl-9 pr-4 py-2.5 rounded-lg bg-slate-100 border border-slate-300 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-colors disabled:opacity-50"
              />
            </div>
            <Button
              variant="primary"
              size="md"
              onClick={() => handleSearch()}
              disabled={!query.trim() || searchState === "searching"}
              isLoading={searchState === "searching"}
            >
              {searchState === "searching" ? "Searching..." : (
                <>
                  <Search className="w-3.5 h-3.5" />
                  Search
                </>
              )}
            </Button>
          </div>

          {topicFilter && (
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <Tag className="w-3 h-3" />
              Filtered to: <Badge variant="info" size="sm">{topicFilter}</Badge>
              <button onClick={() => setTopicFilter("")} className="text-slate-400 hover:text-slate-700 transition-colors">✕ clear</button>
            </div>
          )}

          {/* Example queries */}
          <div>
            <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-2">Example queries</p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_QUERIES.map((eq) => (
                <button
                  key={eq.query}
                  onClick={() => handleExampleClick(eq.query)}
                  disabled={searchState === "searching"}
                  className="text-[11px] text-slate-500 hover:text-slate-800 bg-slate-50 hover:bg-slate-100 border border-slate-300/50 rounded px-2.5 py-1.5 transition-colors text-left disabled:opacity-50"
                >
                  {eq.query}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Search Results ──────────────────────────────────────── */}

      {/* Loading */}
      {searchState === "searching" && (
        <div className="flex items-center gap-3 text-slate-500 py-4">
          <RefreshCw className="w-4 h-4 animate-spin" />
          <span className="text-sm">Searching knowledge base...</span>
        </div>
      )}

      {/* No results */}
      {searchState === "no_results" && (
        <div className="flex items-start gap-3 rounded-xl bg-slate-50 border border-slate-300/50 px-4 py-4">
          <Search className="w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5" />
          <div>
            <div className="text-sm font-semibold text-slate-800">No relevant knowledge found</div>
            <div className="text-xs text-slate-500 mt-0.5">
              Try rephrasing your question, removing the topic filter, or asking about a different concept.
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {searchState === "error" && (
        <div className="flex items-start gap-3 rounded-xl bg-red-50 border border-red-200 px-4 py-4">
          <XCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <div className="text-sm font-semibold text-red-600">Knowledge base is temporarily unavailable</div>
            <div className="text-xs text-red-600/80 mt-0.5">{searchError}</div>
            <button
              className="text-xs text-slate-500 hover:text-slate-800 mt-2 transition-colors"
              onClick={() => setSearchState("idle")}
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Success */}
      {searchState === "success" && result && (
        <div className="space-y-4">
          {/* Result header */}
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-800">
                {result.sources.length} source{result.sources.length !== 1 ? "s" : ""} retrieved
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Top confidence: <span className={`font-bold font-mono ${scoreColor(result.confidence_score)}`}>
                  {(result.confidence_score * 100).toFixed(1)}%
                </span>
                {" "}· Query: <span className="italic">&ldquo;{result.query}&rdquo;</span>
              </p>
            </div>
            <Badge
              variant={result.has_grounding ? "success" : "default"}
              size="sm"
            >
              {result.has_grounding ? "Grounded" : "No grounding"}
            </Badge>
          </div>

          {/* Source cards */}
          <div className="space-y-3">
            {result.sources.map((src, i) => (
              <SourceCard
                key={src.chunk_id}
                source={src}
                index={i + 1}
                contextText={result.context_text}
              />
            ))}
          </div>

          {/* Interview CTA */}
          <div className="flex items-center justify-between rounded-xl bg-slate-50 border border-slate-300/50 p-4">
            <div>
              <div className="text-sm font-semibold text-slate-800">Practice this topic in an interview</div>
              <div className="text-xs text-slate-500 mt-0.5">
                Your adaptive interview will include questions grounded in this knowledge base
              </div>
            </div>
            <Link href="/interview">
              <Button variant="primary" size="sm">
                <Sparkles className="w-3.5 h-3.5" />
                Start Interview
              </Button>
            </Link>
          </div>
        </div>
      )}

      {/* How it works (collapsible) */}
      <RagExplainer />
    </div>
  );
}