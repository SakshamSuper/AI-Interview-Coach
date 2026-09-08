"use client";

import { useAuth } from "@/contexts/AuthContext";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  History, Calendar, CheckCircle2, ChevronRight, XCircle,
  RefreshCw, Clock, Trophy, Target, BookOpen, AlertTriangle,
  TrendingUp, BarChart3, MessageSquare, ChevronDown, ChevronUp,
  Layers, FileText,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";

// ─── Types ────────────────────────────────────────────────────────────────────

interface SessionSummary {
  session_id: number;
  user_id: number | null;
  target_role: string;
  interview_type: string;
  difficulty: string;
  status: string;
  total_questions: number;
  current_question_index: number;
  overall_score: number | null;
  readiness_score: number | null;
  readiness_label: string | null;
  created_at: string;
  completed_at: string | null;
}

interface QuestionEval {
  question_number: number;
  question_text: string;
  topic: string;
  difficulty: string;
  candidate_answer: string;
  technical_accuracy: number;
  relevance: number;
  completeness: number;
  clarity: number;
  communication: number;
  overall_score: number;
  feedback: string;
  strengths: string[];
  weaknesses: string[];
  missing_concepts: string[];
}

interface SessionDetail {
  session_id: number;
  target_role: string;
  difficulty: string;
  status: string;
  overall_score: number | null;
  readiness_score: number | null;
  readiness_label: string | null;
  average_dimensions: {
    technical_accuracy: number;
    relevance: number;
    completeness: number;
    clarity: number;
    communication: number;
  } | null;
  questions_and_evaluations: QuestionEval[];
  recommendations: {
    overall_summary: string | null;
    strong_areas: string[];
    weak_areas: string[];
    learning_priorities: string[];
    practice_questions: string[];
  } | null;
  has_evaluations: boolean;
}

// ─── Constants ────────────────────────────────────────────────────────────────
// USER_ID is now derived from the authenticated session — see useAuth() below

// ─── Helpers ──────────────────────────────────────────────────────────────────

function scoreColor(s: number) {
  if (s >= 80) return "text-emerald-600";
  if (s >= 60) return "text-amber-600";
  return "text-red-600";
}

function scoreBarColor(s: number): "emerald" | "amber" | "rose" {
  if (s >= 80) return "emerald";
  if (s >= 60) return "amber";
  return "rose";
}

function readinessVariant(label: string | null): "success" | "warning" | "danger" | "default" {
  if (!label) return "default";
  const l = label.toLowerCase();
  if (l.includes("ready") && !l.includes("almost")) return "success";
  if (l.includes("almost") || l.includes("borderline")) return "warning";
  if (l.includes("needs")) return "danger";
  return "default";
}

function difficultyVariant(d: string): "success" | "warning" | "danger" | "default" {
  if (d === "Easy") return "success";
  if (d === "Medium") return "warning";
  if (d === "Hard") return "danger";
  return "default";
}

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) +
    " " + d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

// ─── Question detail card ─────────────────────────────────────────────────────

function QuestionDetailCard({ qe, index }: { qe: QuestionEval; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const dims = [
    { label: "Technical", value: qe.technical_accuracy },
    { label: "Relevance", value: qe.relevance },
    { label: "Completeness", value: qe.completeness },
    { label: "Clarity", value: qe.clarity },
    { label: "Communication", value: qe.communication },
  ];

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 overflow-hidden">
      {/* Header row — always visible */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full text-left px-4 py-3 flex items-center gap-3 hover:bg-slate-100/30 transition-colors"
      >
        <span className="text-xs font-bold text-slate-400 font-mono w-6 shrink-0">Q{index + 1}</span>
        <span className="flex-1 text-sm text-slate-800 font-medium leading-snug line-clamp-2">
          {qe.question_text}
        </span>
        <div className="flex items-center gap-2 shrink-0">
          <Badge variant={difficultyVariant(qe.difficulty)} size="sm">{qe.difficulty}</Badge>
          <span className={`text-sm font-bold font-mono ${scoreColor(qe.overall_score)}`}>
            {qe.overall_score.toFixed(0)}
          </span>
          {expanded ? (
            <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          )}
        </div>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="border-t border-slate-200 px-4 pb-4 pt-3 space-y-4">
          {/* Topic */}
          <div className="flex items-center gap-2">
            <Layers className="w-3 h-3 text-slate-400" />
            <span className="text-[10px] text-slate-400 uppercase tracking-wide font-bold">Topic:</span>
            <span className="text-xs text-slate-700">{qe.topic}</span>
          </div>

          {/* Candidate answer */}
          <div>
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wide mb-1.5 flex items-center gap-1.5">
              <MessageSquare className="w-3 h-3" />Candidate Answer
            </p>
            <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 rounded-lg p-3 border border-slate-300/40">
              {qe.candidate_answer || <span className="text-slate-400 italic">No answer recorded.</span>}
            </p>
          </div>

          {/* Score dimensions */}
          <div>
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wide mb-2">Evaluation Scores</p>
            <div className="space-y-1.5">
              {dims.map((d) => (
                <ProgressBar key={d.label} label={d.label} value={d.value} color={scoreBarColor(d.value)} size="sm" />
              ))}
            </div>
          </div>

          {/* Feedback */}
          {qe.feedback && (
            <div className="rounded-lg bg-slate-50 border border-slate-300/40 p-3">
              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wide mb-1">Feedback</p>
              <p className="text-xs text-slate-700 leading-relaxed">{qe.feedback}</p>
            </div>
          )}

          {/* Strengths / Weaknesses */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {qe.strengths.length > 0 && (
              <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-2.5">
                <p className="text-[9px] font-bold text-emerald-600 uppercase tracking-wide mb-1">Strengths</p>
                <ul className="space-y-0.5">
                  {qe.strengths.map((s) => (
                    <li key={s} className="flex items-start gap-1 text-[11px] text-slate-700">
                      <CheckCircle2 className="w-2.5 h-2.5 text-emerald-600 flex-shrink-0 mt-0.5" />{s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {(qe.weaknesses.length > 0 || qe.missing_concepts.length > 0) && (
              <div className="rounded-lg bg-amber-50 border border-amber-200 p-2.5">
                <p className="text-[9px] font-bold text-amber-600 uppercase tracking-wide mb-1">Gaps</p>
                <ul className="space-y-0.5">
                  {[...qe.weaknesses, ...qe.missing_concepts].slice(0, 4).map((w) => (
                    <li key={w} className="flex items-start gap-1 text-[11px] text-slate-700">
                      <AlertTriangle className="w-2.5 h-2.5 text-amber-600 flex-shrink-0 mt-0.5" />{w}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Session detail panel ─────────────────────────────────────────────────────

function SessionDetailPanel({
  sessionId,
  onClose,
}: {
  sessionId: number;
  onClose: () => void;
}) {
  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    setLoading(true);
    setErr("");
    fetch(`/api/py/analytics/session/${sessionId}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setDetail)
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />
        <span className="text-sm text-slate-500">Loading session detail...</span>
      </div>
    );
  }

  if (err) {
    return (
      <div className="flex items-start gap-3 rounded-xl bg-red-50 border border-red-200 p-4">
        <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
        <div>
          <div className="text-sm font-semibold text-red-600">Failed to load session</div>
          <div className="text-xs text-red-600/80 mt-1">{err}</div>
          <button onClick={onClose} className="mt-2 text-xs text-slate-500 underline">Go back</button>
        </div>
      </div>
    );
  }

  if (!detail) return null;

  const dims = detail.average_dimensions;

  return (
    <div className="space-y-5 animate-fadeIn">
      {/* Back button */}
      <div className="flex items-center gap-3">
        <button
          onClick={onClose}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ChevronUp className="w-3.5 h-3.5 rotate-[270deg]" />
          All Sessions
        </button>
        <span className="text-slate-600">|</span>
        <span className="text-xs text-slate-400">Session #{sessionId}</span>
        <Badge variant={readinessVariant(detail.readiness_label)} size="sm">
          {detail.readiness_label || "In Progress"}
        </Badge>
      </div>

      {/* Summary row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-xl bg-slate-50 border border-slate-200 p-4 text-center">
          <div className={`text-3xl font-black font-mono ${scoreColor(detail.overall_score ?? 0)}`}>
            {detail.overall_score?.toFixed(0) ?? "—"}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 uppercase tracking-wide">Overall Score</div>
        </div>
        <div className="rounded-xl bg-slate-50 border border-slate-200 p-4 text-center">
          <div className="text-2xl font-bold text-slate-800">{detail.target_role}</div>
          <div className="text-[10px] text-slate-400 mt-1 uppercase tracking-wide">Target Role</div>
        </div>
        <div className="rounded-xl bg-slate-50 border border-slate-200 p-4 text-center">
          <Badge variant={difficultyVariant(detail.difficulty)} size="sm">{detail.difficulty}</Badge>
          <div className="text-[10px] text-slate-400 mt-2 uppercase tracking-wide">Difficulty</div>
        </div>
        <div className="rounded-xl bg-slate-50 border border-slate-200 p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">
            {detail.questions_and_evaluations.length}/{detail.questions_and_evaluations.length || "?"}
          </div>
          <div className="text-[10px] text-slate-400 mt-1 uppercase tracking-wide">Questions</div>
        </div>
      </div>

      {/* Dimension scores */}
      {dims && (
        <Card>
          <CardHeader><CardTitle>Dimension Performance</CardTitle></CardHeader>
          <CardContent className="space-y-2.5">
            <ProgressBar label="Technical Accuracy" value={dims.technical_accuracy} color={scoreBarColor(dims.technical_accuracy)} size="sm" />
            <ProgressBar label="Relevance" value={dims.relevance} color={scoreBarColor(dims.relevance)} size="sm" />
            <ProgressBar label="Completeness" value={dims.completeness} color={scoreBarColor(dims.completeness)} size="sm" />
            <ProgressBar label="Clarity" value={dims.clarity} color={scoreBarColor(dims.clarity)} size="sm" />
            <ProgressBar label="Communication" value={dims.communication} color={scoreBarColor(dims.communication)} size="sm" />
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      {detail.recommendations && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {detail.recommendations.strong_areas.length > 0 && (
            <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3">
              <p className="text-[10px] font-bold text-emerald-600 uppercase tracking-wide mb-1.5">Strong Areas</p>
              <ul className="space-y-1">
                {detail.recommendations.strong_areas.map((a) => (
                  <li key={a} className="flex items-start gap-1.5 text-xs text-slate-700">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600 flex-shrink-0 mt-0.5" />{a}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {detail.recommendations.weak_areas.length > 0 && (
            <div className="rounded-lg bg-amber-50 border border-amber-200 p-3">
              <p className="text-[10px] font-bold text-amber-600 uppercase tracking-wide mb-1.5">Weak Areas</p>
              <ul className="space-y-1">
                {detail.recommendations.weak_areas.map((a) => (
                  <li key={a} className="flex items-start gap-1.5 text-xs text-slate-700">
                    <AlertTriangle className="w-3 h-3 text-amber-600 flex-shrink-0 mt-0.5" />{a}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Q&A Transcript */}
      {detail.questions_and_evaluations.length > 0 && (
        <div>
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-3 flex items-center gap-2">
            <BookOpen className="w-3.5 h-3.5" />
            Interview Transcript — {detail.questions_and_evaluations.length} Questions
          </p>
          <div className="space-y-2">
            {detail.questions_and_evaluations.map((qe, i) => (
              <QuestionDetailCard key={qe.question_number} qe={qe} index={i} />
            ))}
          </div>
        </div>
      )}

      {!detail.has_evaluations && (
        <div className="text-center py-8 text-sm text-slate-400">
          This session has no evaluations — it may have been abandoned before completion.
        </div>
      )}
    </div>
  );
}

// ─── Main History Page ────────────────────────────────────────────────────────

export default function HistoryPage() {
  const { userId: USER_ID } = useAuth();
  const effectiveUserId = USER_ID ?? 1;
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    fetch(`/api/py/interviews/?user_id=${effectiveUserId}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setSessions)
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, [effectiveUserId]);


  const completed = sessions.filter((s) => s.status === "completed");
  const inProgress = sessions.filter((s) => s.status !== "completed");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900 flex items-center gap-2">
            <History className="w-6 h-6 text-blue-600" />
            Interview Session History
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Complete audit trail of all interview sessions with full Q&amp;A transcripts and evaluations.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {!loading && (
            <Badge variant="info" size="sm">{sessions.length} sessions</Badge>
          )}
          <Link href="/interview">
            <Button variant="primary" size="sm">
              <Trophy className="w-3.5 h-3.5" />New Interview
            </Button>
          </Link>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-20 gap-3">
          <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />
          <span className="text-sm text-slate-500">Loading session history...</span>
        </div>
      )}

      {/* Error */}
      {!loading && err && (
        <div className="flex items-start gap-3 rounded-xl bg-red-50 border border-red-200 p-4">
          <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <div className="text-sm font-semibold text-red-600">Failed to load history</div>
            <div className="text-xs text-red-600/80 mt-1">{err}</div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !err && sessions.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
          <FileText className="w-12 h-12 text-slate-600" />
          <h3 className="text-sm font-semibold text-slate-700">No sessions yet</h3>
          <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
            Complete your first adaptive interview to see your session history, evaluations, and performance breakdown here.
          </p>
          <Link href="/interview">
            <Button variant="primary" size="sm">
              <Trophy className="w-3.5 h-3.5" />Start Your First Interview
            </Button>
          </Link>
        </div>
      )}

      {/* Session detail view */}
      {!loading && !err && selectedId !== null && (
        <SessionDetailPanel sessionId={selectedId} onClose={() => setSelectedId(null)} />
      )}

      {/* Session list */}
      {!loading && !err && sessions.length > 0 && selectedId === null && (
        <div className="space-y-6">
          {/* Completed sessions table */}
          {completed.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span className="text-sm font-semibold text-slate-900">
                  Completed Sessions
                </span>
                <span className="ml-auto text-xs text-slate-400">{completed.length}</span>
              </div>
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left px-6 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Date</th>
                      <th className="text-left px-3 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Role</th>
                      <th className="text-left px-3 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Difficulty</th>
                      <th className="text-left px-3 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Questions</th>
                      <th className="text-right px-3 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Score</th>
                      <th className="text-left px-3 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Readiness</th>
                      <th className="px-6 py-3"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {completed.map((s) => (
                      <tr
                        key={s.session_id}
                        className="hover:bg-slate-50 transition-colors cursor-pointer group"
                        onClick={() => setSelectedId(s.session_id)}
                      >
                        <td className="px-6 py-3.5 text-xs text-slate-500 whitespace-nowrap">
                          {formatDate(s.created_at)}
                        </td>
                        <td className="px-3 py-3.5 text-slate-800 font-medium max-w-[180px] truncate">
                          {s.target_role}
                        </td>
                        <td className="px-3 py-3.5">
                          <Badge variant={difficultyVariant(s.difficulty)} size="sm">{s.difficulty}</Badge>
                        </td>
                        <td className="px-3 py-3.5 text-xs text-slate-500 tabular-nums">
                          {s.current_question_index}/{s.total_questions}
                        </td>
                        <td className={`px-3 py-3.5 text-right font-bold font-mono tabular-nums ${scoreColor(s.overall_score ?? 0)}`}>
                          {s.overall_score?.toFixed(1) ?? "—"}
                        </td>
                        <td className="px-3 py-3.5">
                          {s.readiness_label && (
                            <Badge variant={readinessVariant(s.readiness_label)} size="sm">
                              {s.readiness_label}
                            </Badge>
                          )}
                        </td>
                        <td className="px-6 py-3.5">
                          <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-slate-700 transition-colors" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* In-progress sessions table */}
          {inProgress.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden opacity-80">
              <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-600" />
                <span className="text-sm font-semibold text-slate-900">
                  In Progress / Abandoned
                </span>
                <span className="ml-auto text-xs text-slate-400">{inProgress.length}</span>
              </div>
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left px-6 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Date</th>
                      <th className="text-left px-3 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Role</th>
                      <th className="text-left px-3 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Progress</th>
                      <th className="text-left px-3 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Status</th>
                      <th className="px-6 py-3"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {inProgress.map((s) => (
                      <tr
                        key={s.session_id}
                        className="hover:bg-slate-50 transition-colors cursor-pointer group"
                        onClick={() => setSelectedId(s.session_id)}
                      >
                        <td className="px-6 py-3.5 text-xs text-slate-500 whitespace-nowrap">
                          {formatDate(s.created_at)}
                        </td>
                        <td className="px-3 py-3.5 text-slate-700 font-medium max-w-[180px] truncate">
                          {s.target_role}
                        </td>
                        <td className="px-3 py-3.5 text-xs text-slate-500 tabular-nums">
                          {s.current_question_index}/{s.total_questions} answered
                        </td>
                        <td className="px-3 py-3.5">
                          <Badge variant="default" size="sm">Incomplete</Badge>
                        </td>
                        <td className="px-6 py-3.5">
                          <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-slate-700 transition-colors" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}