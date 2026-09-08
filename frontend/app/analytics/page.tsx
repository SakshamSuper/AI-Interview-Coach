"use client";

import { useAuth } from "@/contexts/AuthContext";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  Cell,
  PieChart,
  Pie,
} from "recharts";
import {
  BarChart3, TrendingUp, Brain, Layers, Target,
  Trophy, FileText, ChevronRight, RefreshCw, XCircle,
  CheckCircle2, AlertTriangle, Info,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

// --- Types ---

interface ScoreHistoryEntry {
  session_id: number;
  date: string;
  role: string;
  score: number | null;
  difficulty: string;
  readiness: string;
}

interface AnalyticsData {
  total_interviews: number;
  completed_interviews: number;
  overall_readiness_label: string;
  average_overall_score: number;
  average_technical_score: number;
  average_communication_score: number;
  average_relevance_score: number;
  average_completeness_score: number;
  average_clarity_score: number;
  topic_performance: Record<string, number>;
  score_history: ScoreHistoryEntry[];
  strong_areas: string[];
  weak_areas: string[];
}

interface MLReadinessData {
  has_data: boolean;
  message?: string;
  readiness_label: string | null;
  readiness_score: number | null;
  class_probabilities: Record<string, number> | null;
  strengths_identified: string[];
  improvement_areas: string[];
  model_architecture: string;
  disclaimer: string;
  sessions_used: number;
  feature_inputs: {
    avg_technical: number;
    avg_relevance: number;
    avg_completeness: number;
    avg_clarity: number;
    avg_communication: number;
    answer_length: number;
    answer_length_source: string;
    keyword_coverage: number;
    keyword_coverage_source: string;
    difficulty_numeric: number;
    difficulty_source: string;
    attempt_number: number;
    sessions_completed: number;
    avg_overall: number;
  };
}

type TimeRange = "4w" | "3m" | "all";

// USER_ID is now derived from the authenticated session — see useAuth() below
const DONUT_COLORS = ["#2563eb", "#3b82f6", "#60a5fa", "#1d4ed8", "#1e40af", "#93c5fd"];

// --- Helpers ---

function readinessVariant(label: string | null): "success" | "warning" | "danger" | "default" {
  if (!label) return "default";
  const l = label.toLowerCase();
  if (l.includes("ready") && !l.includes("almost")) return "success";
  if (l.includes("almost") || l.includes("borderline")) return "warning";
  if (l.includes("needs")) return "danger";
  return "default";
}

function readinessColor(label: string | null) {
  if (!label) return "text-slate-500";
  const l = label.toLowerCase();
  if (l.includes("ready") && !l.includes("almost")) return "text-emerald-700";
  if (l.includes("almost") || l.includes("borderline")) return "text-slate-700";
  return "text-red-700";
}

function filterByTimeRange(
  history: ScoreHistoryEntry[],
  range: TimeRange
): ScoreHistoryEntry[] {
  if (range === "all") return history;
  const now = Date.now();
  const days = range === "4w" ? 28 : 90;
  const cutoff = now - days * 24 * 60 * 60 * 1000;
  return history.filter((e) => {
    try {
      const d = new Date(e.date.replace(" ", "T")).getTime();
      return d >= cutoff;
    } catch {
      return true;
    }
  });
}

// --- Tooltips ---

const LineTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { value: number; payload: { date: string } }[];
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-slate-200 rounded-md px-3 py-2 shadow-sm text-xs">
        <div className="text-slate-400 mb-0.5">{payload[0]?.payload?.date}</div>
        <div className="font-bold text-slate-800 tabular-nums">
          {payload[0].value.toFixed(1)}%
        </div>
      </div>
    );
  }
  return null;
};

const BarTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-slate-200 rounded-md px-3 py-2 shadow-sm text-xs">
        <div className="text-slate-500 mb-0.5">{label}</div>
        <div className="font-bold text-slate-800 tabular-nums">
          {payload[0].value.toFixed(1)}%
        </div>
      </div>
    );
  }
  return null;
};

const PieTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { name: string; payload: { avgScore: number } }[];
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-slate-200 rounded-md px-3 py-2 shadow-sm text-xs">
        <div className="font-semibold text-slate-700">{payload[0].name}</div>
        <div className="text-slate-400 mt-0.5">
          Avg score:{" "}
          <span className="font-bold text-slate-700">
            {payload[0].payload.avgScore.toFixed(1)}%
          </span>
        </div>
      </div>
    );
  }
  return null;
};

function PanelEmpty({
  icon: Icon,
  title,
  subtitle,
}: {
  icon: React.ElementType;
  title: string;
  subtitle: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center h-36 gap-1.5 text-center px-4">
      <div className="w-7 h-7 rounded-full bg-slate-50 border border-slate-100 flex items-center justify-center">
        <Icon className="w-3.5 h-3.5 text-slate-400" />
      </div>
      <p className="text-xs font-medium text-slate-700">{title}</p>
      <p className="text-[11px] text-slate-400 max-w-[200px] leading-relaxed">
        {subtitle}
      </p>
    </div>
  );
}

function ChartEmpty({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-36 gap-2">
      <BarChart3 className="w-6 h-6 text-slate-200" />
      <p className="text-xs text-slate-400 text-center max-w-[160px] leading-relaxed">
        {message}
      </p>
    </div>
  );
}

// --- ML Readiness Panel ---

function MLReadinessPanel({ data }: { data: MLReadinessData }) {
  const fi = data.feature_inputs;
  const probs = data.class_probabilities || {};
  const probEntries = Object.entries(probs).sort((a, b) => b[1] - a[1]);

  function fiColor(v: number) {
    if (v >= 80) return "text-emerald-600";
    if (v >= 60) return "text-slate-700";
    return "text-red-600";
  }

  if (!data.has_data) {
    return (
      <div className="bg-white border border-slate-200 rounded-lg">
        <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-slate-800">ML Readiness Prediction</p>
            <p className="text-xs text-slate-400 mt-0.5">
              Scikit-Learn {data.model_architecture || "classifier"}
            </p>
          </div>
          <Brain className="w-4 h-4 text-blue-600" />
        </div>
        <div className="px-5 py-8 flex flex-col items-center text-center gap-3">
          <Brain className="w-7 h-7 text-slate-300" />
          <p className="text-sm text-slate-500">
            {data.message || "Complete an interview to receive your ML readiness prediction."}
          </p>
          <Link href="/interview">
            <Button variant="primary" size="sm">
              <Trophy className="w-3.5 h-3.5" />
              Start Interview
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-lg">
      <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-800">ML Readiness Prediction</p>
          <p className="text-xs text-slate-400 mt-0.5">
            {data.model_architecture} &middot; {data.sessions_used} sessions used
          </p>
        </div>
        <Brain className="w-4 h-4 text-blue-600" />
      </div>
      <div className="px-5 py-4 space-y-4">
        <div className="rounded-lg bg-slate-50 border border-slate-200 p-4 text-center space-y-1">
          <div className="text-[10px] text-slate-400 uppercase tracking-wide font-semibold">
            Predicted Readiness
          </div>
          <div className={`text-2xl font-bold ${readinessColor(data.readiness_label)}`}>
            {data.readiness_label}
          </div>
          <div className="text-xs text-slate-500 font-mono tabular-nums">
            Score:{" "}
            <span className={`font-bold ${readinessColor(data.readiness_label)}`}>
              {data.readiness_score?.toFixed(1)}%
            </span>
          </div>
        </div>
        {probEntries.length > 0 && (
          <div>
            <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-2">
              Class Probabilities
            </p>
            <div className="space-y-1.5">
              {probEntries.map(([cls, prob]) => (
                <div key={cls} className="flex items-center gap-3">
                  <span className="text-xs text-slate-500 w-36 shrink-0">{cls}</span>
                  <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        cls.includes("Ready") && !cls.includes("Almost")
                          ? "bg-emerald-500"
                          : cls.includes("Almost")
                          ? "bg-blue-400"
                          : "bg-red-400"
                      }`}
                      style={{ width: `${(prob * 100).toFixed(1)}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono text-slate-500 w-10 text-right tabular-nums">
                    {(prob * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
        <div>
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-2">
            Feature Inputs
          </p>
          <div className="grid grid-cols-2 gap-1.5 text-xs">
            {[
              { label: "Avg Technical", val: fi.avg_technical },
              { label: "Avg Communication", val: fi.avg_communication },
              { label: "Avg Completeness", val: fi.avg_completeness },
              { label: "Avg Clarity", val: fi.avg_clarity },
              { label: "Avg Overall", val: fi.avg_overall },
            ].map(({ label, val }) => (
              <div
                key={label}
                className="bg-slate-50 rounded px-2.5 py-2 flex items-center justify-between"
              >
                <span className="text-slate-400">{label}</span>
                <span className={`font-mono font-bold ${fiColor(val)}`}>
                  {val.toFixed(1)}
                </span>
              </div>
            ))}
            <div className="bg-slate-50 rounded px-2.5 py-2 flex items-center justify-between">
              <span className="text-slate-400">Sessions Done</span>
              <span className="font-mono font-bold text-blue-600">{fi.sessions_completed}</span>
            </div>
          </div>
        </div>
        {data.strengths_identified.length > 0 && (
          <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3">
            <p className="text-[10px] font-semibold text-emerald-700 uppercase tracking-wide mb-1.5">
              Strengths
            </p>
            <ul className="space-y-1">
              {data.strengths_identified.map((s) => (
                <li key={s} className="flex items-start gap-1.5 text-xs text-slate-700">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600 flex-shrink-0 mt-0.5" />
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}
        {data.improvement_areas.length > 0 && (
          <div className="rounded-lg bg-slate-50 border border-slate-200 p-3">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
              Improvement Areas
            </p>
            <ul className="space-y-1">
              {data.improvement_areas.map((a) => (
                <li key={a} className="flex items-start gap-1.5 text-xs text-slate-700">
                  <AlertTriangle className="w-3 h-3 text-amber-500 flex-shrink-0 mt-0.5" />
                  {a}
                </li>
              ))}
            </ul>
          </div>
        )}
        <div className="flex items-start gap-2 bg-slate-50 border border-slate-200 rounded-lg p-3">
          <Info className="w-3 h-3 text-slate-400 flex-shrink-0 mt-0.5" />
          <p className="text-[9px] text-slate-400 leading-relaxed">{data.disclaimer}</p>
        </div>
      </div>
    </div>
  );
}

// --- Main ---

export default function AnalyticsPage() {
  const { userId: USER_ID } = useAuth();
  const effectiveUserId = USER_ID ?? 1;
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [ml, setMl] = useState<MLReadinessData | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [range, setRange] = useState<TimeRange>("all");

  useEffect(() => {
    setLoading(true);
    setErr("");
    Promise.all([
      fetch(`/api/py/analytics/${effectiveUserId}`).then((r) => {
        if (!r.ok) throw new Error(`Analytics HTTP ${r.status}`);
        return r.json();
      }),
      fetch(`/api/py/ml/readiness?user_id=${effectiveUserId}`).then((r) => {
        if (!r.ok) throw new Error(`ML readiness HTTP ${r.status}`);
        return r.json();
      }),
    ])
      .then(([a, m]) => {
        setAnalytics(a);
        setMl(m);
      })
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, [effectiveUserId]);

  const filteredHistory = useMemo(
    () => (analytics ? filterByTimeRange(analytics.score_history, range) : []),
    [analytics, range]
  );

  const lineData = useMemo(
    () =>
      filteredHistory
        .filter((e) => e.score !== null)
        .map((e) => ({
          label: `S${e.session_id}`,
          score: parseFloat((e.score ?? 0).toFixed(1)),
          date: e.date,
        })),
    [filteredHistory]
  );

  const hasSkillData = useMemo(() => {
    if (!analytics || analytics.completed_interviews === 0) return false;
    return (
      analytics.average_technical_score > 0 ||
      analytics.average_communication_score > 0 ||
      analytics.average_relevance_score > 0
    );
  }, [analytics]);

  const skillData = useMemo(() => {
    if (!analytics || !hasSkillData) return [];
    return [
      { name: "Technical", score: analytics.average_technical_score },
      { name: "Comm.", score: analytics.average_communication_score },
      { name: "Relevance", score: analytics.average_relevance_score },
      { name: "Complete.", score: analytics.average_completeness_score },
      { name: "Clarity", score: analytics.average_clarity_score },
    ];
  }, [analytics, hasSkillData]);

  const topicData = useMemo(() => {
    if (!analytics) return [];
    return Object.entries(analytics.topic_performance)
      .sort((a, b) => b[1] - a[1])
      .map(([name, avgScore]) => ({ name, value: 1, avgScore }));
  }, [analytics]);

  const filteredCompleted = filteredHistory.filter((e) => e.score !== null);
  const filteredAvgScore =
    filteredCompleted.length > 0
      ? filteredCompleted.reduce((s, e) => s + (e.score ?? 0), 0) /
        filteredCompleted.length
      : null;

  const hasData = analytics !== null && analytics.total_interviews > 0;
  const RANGE_LABELS: Record<TimeRange, string> = {
    "4w": "Last 4 weeks",
    "3m": "Last 3 months",
    all: "All time",
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">Performance Analytics</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Track your interview performance over time.
          </p>
        </div>
        <div className="flex items-center gap-0.5 bg-white border border-slate-200 rounded-md p-0.5 self-start shrink-0">
          {(["4w", "3m", "all"] as TimeRange[]).map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={[
                "px-2.5 py-1 text-xs rounded font-medium transition-colors cursor-pointer",
                range === r
                  ? "bg-slate-900 text-white"
                  : "text-slate-500 hover:text-slate-700 hover:bg-slate-50",
              ].join(" ")}
            >
              {RANGE_LABELS[r]}
            </button>
          ))}
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-20 gap-3">
          <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />
          <span className="text-sm text-slate-500">Loading analytics...</span>
        </div>
      )}

      {/* Error */}
      {!loading && err && (
        <div className="flex items-start gap-3 rounded-lg bg-red-50 border border-red-200 p-4">
          <XCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <div className="text-sm font-semibold text-red-700">
              Failed to load analytics
            </div>
            <div className="text-xs text-red-600/80 mt-1">{err}</div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !err && analytics && analytics.total_interviews === 0 && (
        <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
          <BarChart3 className="w-10 h-10 text-slate-300" />
          <h3 className="text-sm font-semibold text-slate-700">No interview data yet</h3>
          <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
            Complete your first adaptive interview session to see analytics, score
            trajectories, skill performance, and ML readiness predictions.
          </p>
          <Link href="/interview">
            <Button variant="primary" size="sm">
              <Trophy className="w-3.5 h-3.5" />
              Start Interview
            </Button>
          </Link>
        </div>
      )}

      {/* Main content */}
      {!loading && !err && hasData && (
        <div className="space-y-5">
          {/* ROW 1: Three chart panels */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* 1. Score Progression */}
            <div className="bg-white border border-slate-200 rounded-lg flex flex-col">
              <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-slate-800">Score Progression</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {lineData.length > 0
                      ? `${lineData.length} scored session${lineData.length !== 1 ? "s" : ""}`
                      : "No data for this period"}
                  </p>
                </div>
                <TrendingUp className="w-3.5 h-3.5 text-blue-600 shrink-0" />
              </div>
              <div className="px-2 pt-3 pb-1 flex-1">
                {lineData.length >= 2 ? (
                  <ResponsiveContainer width="100%" height={174}>
                    <LineChart
                      data={lineData}
                      margin={{ top: 4, right: 8, bottom: 4, left: -8 }}
                    >
                      <CartesianGrid
                        strokeDasharray="2 3"
                        stroke="#f1f5f9"
                        vertical={false}
                      />
                      <XAxis
                        dataKey="label"
                        tick={{ fontSize: 9, fill: "#94a3b8" }}
                        axisLine={false}
                        tickLine={false}
                        interval="preserveStartEnd"
                      />
                      <YAxis
                        domain={[0, 100]}
                        ticks={[0, 25, 50, 75, 100]}
                        tick={{ fontSize: 9, fill: "#94a3b8" }}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={(v) => `${v}%`}
                        width={30}
                      />
                      <Tooltip content={<LineTooltip />} />
                      <Line
                        type="monotone"
                        dataKey="score"
                        stroke="#2563eb"
                        strokeWidth={1.5}
                        dot={{ r: 3, fill: "#2563eb", strokeWidth: 0 }}
                        activeDot={{ r: 4, fill: "#1d4ed8", strokeWidth: 0 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : lineData.length === 1 ? (
                  <div className="flex flex-col items-center justify-center h-36 gap-1">
                    <div className="text-2xl font-bold text-slate-800 tabular-nums">
                      {lineData[0].score.toFixed(1)}%
                    </div>
                    <p className="text-xs text-slate-400">
                      1 session &mdash; need 2+ for trend
                    </p>
                  </div>
                ) : (
                  <PanelEmpty
                    icon={TrendingUp}
                    title="No scored sessions yet"
                    subtitle="Complete an interview to see your progression."
                  />
                )}
              </div>
              {lineData.length >= 1 && (
                <div className="px-4 py-2.5 border-t border-slate-50 flex items-center gap-4">
                  <div className="text-xs text-slate-400">
                    Avg{" "}
                    <span className="font-semibold text-slate-700 tabular-nums ml-1">
                      {(
                        lineData.reduce((s, d) => s + d.score, 0) /
                        lineData.length
                      ).toFixed(1)}
                      %
                    </span>
                  </div>
                  {lineData.length >= 2 && (
                    <div className="text-xs text-slate-400">
                      Latest{" "}
                      <span className="font-semibold text-slate-700 tabular-nums ml-1">
                        {lineData[lineData.length - 1].score.toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* 2. Skill Performance */}
            <div className="bg-white border border-slate-200 rounded-lg flex flex-col">
              <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-slate-800">Skill Performance</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Avg by evaluation dimension
                  </p>
                </div>
                <Layers className="w-3.5 h-3.5 text-blue-600 shrink-0" />
              </div>
              <div className="px-2 pt-3 pb-1 flex-1">
                {skillData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={174}>
                    <BarChart
                      data={skillData}
                      margin={{ top: 12, right: 12, bottom: 4, left: -16 }}
                    >
                      <CartesianGrid
                        strokeDasharray="2 3"
                        stroke="#f1f5f9"
                        vertical={false}
                      />
                      <XAxis
                        dataKey="name"
                        tick={{ fontSize: 9, fill: "#64748b" }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        domain={[0, 100]}
                        ticks={[0, 25, 50, 75, 100]}
                        tick={{ fontSize: 9, fill: "#94a3b8" }}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={(v) => `${v}%`}
                        width={30}
                      />
                      <Tooltip content={<BarTooltip />} />
                      <Bar dataKey="score" radius={[3, 3, 0, 0]} maxBarSize={22}>
                        {skillData.map((entry, i) => (
                          <Cell
                            key={i}
                            fill={
                              entry.score >= 80
                                ? "#10b981"
                                : entry.score >= 60
                                ? "#2563eb"
                                : "#60a5fa"
                            }
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <PanelEmpty
                    icon={Layers}
                    title="No evaluation data yet"
                    subtitle="Complete an interview to see evaluation dimensions."
                  />
                )}
              </div>
              {skillData.length > 0 && (
                <div className="px-4 py-2 border-t border-slate-50 text-xs text-slate-400">
                  Best:{" "}
                  <span className="font-semibold text-slate-700 ml-1">
                    {skillData.reduce((a, b) => (a.score > b.score ? a : b)).name}
                  </span>
                  <span className="tabular-nums ml-1">
                    {skillData
                      .reduce((a, b) => (a.score > b.score ? a : b))
                      .score.toFixed(1)}
                    %
                  </span>
                </div>
              )}
            </div>

            {/* 3. Question Topics */}
            <div className="bg-white border border-slate-200 rounded-lg flex flex-col">
              <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-slate-800">Question Topics</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {topicData.length > 0
                      ? `${topicData.length} topic area${topicData.length !== 1 ? "s" : ""} covered`
                      : "No topic data yet"}
                  </p>
                </div>
                <Target className="w-3.5 h-3.5 text-blue-600 shrink-0" />
              </div>
              <div className="px-4 pt-3 pb-3 flex-1 flex flex-col">
                {topicData.length > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height={120}>
                      <PieChart>
                        <Pie
                          data={topicData}
                          cx="50%"
                          cy="50%"
                          innerRadius={30}
                          outerRadius={52}
                          paddingAngle={topicData.length > 1 ? 4 : 0}
                          dataKey="value"
                          nameKey="name"
                          strokeWidth={0}
                        >
                          {topicData.map((_, i) => (
                            <Cell
                              key={i}
                              fill={DONUT_COLORS[i % DONUT_COLORS.length]}
                            />
                          ))}
                        </Pie>
                        <Tooltip content={<PieTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                    <ul className="space-y-1.5 mt-2">
                      {topicData.map((t, i) => (
                        <li key={t.name} className="flex items-center gap-2 text-xs">
                          <span
                            className="w-2 h-2 rounded-full flex-shrink-0"
                            style={{
                              backgroundColor:
                                DONUT_COLORS[i % DONUT_COLORS.length],
                            }}
                          />
                          <span className="text-slate-600 flex-1 truncate">{t.name}</span>
                          <span className="font-mono text-slate-500 tabular-nums">
                            {t.avgScore.toFixed(0)}%
                          </span>
                        </li>
                      ))}
                    </ul>
                  </>
                ) : (
                  <PanelEmpty
                    icon={Target}
                    title="No topic data yet"
                    subtitle="Complete an interview to see topic coverage."
                  />
                )}
              </div>
            </div>
          </div>

          {/* Summary metrics strip */}
          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
            <dl className="grid grid-cols-2 md:grid-cols-4 divide-x divide-y md:divide-y-0 divide-slate-100">
              <div className="px-5 py-4">
                <dt className="text-[11px] text-slate-400 font-medium uppercase tracking-wide">
                  Avg Overall Score
                </dt>
                <dd className="text-xl font-bold text-slate-800 mt-1 tabular-nums">
                  {analytics.completed_interviews > 0 ? (
                    <>
                      {filteredAvgScore !== null
                        ? filteredAvgScore.toFixed(1)
                        : analytics.average_overall_score.toFixed(1)}
                      <span className="text-xs font-normal text-slate-400 ml-0.5">/100</span>
                    </>
                  ) : (
                    <span className="text-slate-400 font-normal text-lg">—</span>
                  )}
                </dd>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  {analytics.completed_interviews > 0
                    ? range !== "all"
                      ? RANGE_LABELS[range]
                      : "Across completed"
                    : "Complete an interview to calculate"}
                </div>
              </div>
              <div className="px-5 py-4">
                <dt className="text-[11px] text-slate-400 font-medium uppercase tracking-wide">
                  Sessions Completed
                </dt>
                <dd className="text-xl font-bold text-slate-800 mt-1 tabular-nums">
                  {filteredCompleted.length}
                  {range !== "all" && analytics.completed_interviews > 0 && (
                    <span className="text-xs font-normal text-slate-400 ml-1">
                      of {analytics.completed_interviews}
                    </span>
                  )}
                </dd>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  {analytics.total_interviews} total attempted
                </div>
              </div>
              <div className="px-5 py-4">
                <dt className="text-[11px] text-slate-400 font-medium uppercase tracking-wide">
                  Avg Technical
                </dt>
                <dd className="text-xl font-bold text-slate-800 mt-1 tabular-nums">
                  {analytics.completed_interviews > 0 ? (
                    <>
                      {analytics.average_technical_score.toFixed(1)}
                      <span className="text-xs font-normal text-slate-400 ml-0.5">/100</span>
                    </>
                  ) : (
                    <span className="text-slate-400 font-normal text-lg">—</span>
                  )}
                </dd>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  {analytics.completed_interviews > 0 ? "Technical accuracy avg" : "No evaluation data"}
                </div>
              </div>
              <div className="px-5 py-4">
                <dt className="text-[11px] text-slate-400 font-medium uppercase tracking-wide">
                  Readiness
                </dt>
                <dd
                  className={`text-lg font-bold mt-1 leading-tight ${analytics.completed_interviews > 0 ? readinessColor(analytics.overall_readiness_label) : "text-slate-400 font-medium"}`}
                >
                  {analytics.completed_interviews > 0 ? analytics.overall_readiness_label : "Not Evaluated"}
                </dd>
                {ml?.has_data && (
                  <div className="text-[10px] text-slate-400 mt-0.5 font-mono">
                    {ml.readiness_score?.toFixed(1)}% &middot; {ml.model_architecture}
                  </div>
                )}
              </div>
            </dl>
          </div>

          {/* Interview Performance table */}
          <div className="bg-white border border-slate-200 rounded-lg">
            <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-slate-800">
                  Interview Performance
                </p>
                <p className="text-xs text-slate-400 mt-0.5">
                  {filteredHistory.length} session
                  {filteredHistory.length !== 1 ? "s" : ""} &middot; {RANGE_LABELS[range]}
                </p>
              </div>
              <Link
                href="/history"
                className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
              >
                Full history <ChevronRight className="w-3 h-3" />
              </Link>
            </div>
            {filteredHistory.length === 0 ? (
              <div className="px-5 py-8 flex flex-col items-center gap-2 text-center">
                <BarChart3 className="w-7 h-7 text-slate-200" />
                <p className="text-xs text-slate-400">No sessions in this period</p>
                <button
                  onClick={() => setRange("all")}
                  className="text-xs text-blue-600 hover:underline cursor-pointer"
                >
                  Show all time
                </button>
              </div>
            ) : (
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100">
                      <th className="text-left px-5 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wide">
                        Date
                      </th>
                      <th className="text-left px-3 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wide">
                        Role
                      </th>
                      <th className="text-left px-3 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wide">
                        Difficulty
                      </th>
                      <th className="text-right px-3 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wide">
                        Score
                      </th>
                      <th className="text-right px-3 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wide">
                        Readiness
                      </th>
                      <th className="text-right px-5 py-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wide">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...filteredHistory].reverse().map((e) => (
                      <tr
                        key={e.session_id}
                        className="border-b border-slate-50 last:border-0 hover:bg-slate-50 transition-colors"
                      >
                        <td className="px-5 py-2.5 text-xs text-slate-400 whitespace-nowrap">
                          {e.date}
                        </td>
                        <td className="px-3 py-2.5 text-slate-700 font-medium max-w-[140px] truncate">
                          {e.role}
                        </td>
                        <td className="px-3 py-2.5">
                          <Badge
                            variant={
                              e.difficulty === "Hard"
                                ? "danger"
                                : e.difficulty === "Easy"
                                ? "success"
                                : "warning"
                            }
                            size="sm"
                          >
                            {e.difficulty}
                          </Badge>
                        </td>
                        <td className="px-3 py-2.5 text-right font-mono font-bold tabular-nums text-slate-800">
                          {e.score != null ? (
                            e.score.toFixed(0)
                          ) : (
                            <span className="text-slate-300">—</span>
                          )}
                        </td>
                        <td className="px-3 py-2.5 text-right">
                          {e.readiness ? (
                            <Badge
                              variant={readinessVariant(e.readiness)}
                              size="sm"
                            >
                              {e.readiness}
                            </Badge>
                          ) : (
                            <span className="text-xs text-slate-300">—</span>
                          )}
                        </td>
                        <td className="px-5 py-2.5 text-right">
                          <Badge
                            variant={e.score != null ? "success" : "default"}
                            size="sm"
                          >
                            {e.score != null ? "Completed" : "In Progress"}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* ML Readiness */}
          {ml && <MLReadinessPanel data={ml} />}

          {/* Navigation */}
          <div className="flex justify-center pb-2">
            <Link href="/history">
              <Button variant="outline" size="sm">
                <FileText className="w-3.5 h-3.5" />
                View Full Session History
                <ChevronRight className="w-3.5 h-3.5" />
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
