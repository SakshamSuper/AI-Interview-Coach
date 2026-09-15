"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
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
} from "recharts";
import {
  Sparkles,
  ArrowRight,
  Target,
  Layers,
  TrendingUp,
  AlertTriangle,
  BookOpen,
  ChevronRight,
  Clock,
  Upload,
  Briefcase,
  PlayCircle,
  CheckCircle2,
  BarChart2,
  Zap,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { EmptyState } from "@/components/ui/EmptyState";
import { cn } from "@/lib/utils/cn";

// ─── API types ────────────────────────────────────────────────────────────────

interface ScoreHistoryEntry {
  session_id: number;
  date: string;
  role: string;
  score: number;
  difficulty: string;
  readiness: string;
}


interface AnalyticsResponse {
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

interface SkillGapResponse {
  overall_match_score: number;
  match_category: string;
  gap_report?: {
    missing_skills?: Array<string | { skill: string; [key: string]: any }>;
    high_priority_gaps?: Array<string | { skill: string; [key: string]: any }>;
    job_description_info?: {
      target_role?: string;
      experience_level?: string;
    };
  };
}

interface MLReadinessResponse {
  has_data: boolean;
  readiness_label: string | null;
  readiness_score: number | null;
  model_architecture?: string;
  disclaimer?: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function readinessBadgeVariant(label: string): "success" | "warning" | "danger" | "default" {
  if (label === "Interview Ready") return "success";
  if (label === "Almost Ready") return "warning";
  if (label === "Needs Improvement") return "danger";
  return "default";
}

function matchBadgeVariant(cat: string): "success" | "warning" | "danger" | "info" {
  if (cat === "Strong Match") return "success";
  if (cat === "Moderate Match") return "warning";
  if (cat === "Weak Match") return "danger";
  return "info";
}

function topicColor(score: number): string {
  if (score >= 80) return "#10b981";
  if (score >= 60) return "#2563eb";
  if (score >= 40) return "#2563eb";
  return "#ef4444";
}

function formatScoreLabel(score: number): string {
  if (score >= 80) return "Strong";
  if (score >= 60) return "Good";
  if (score >= 40) return "Fair";
  return "Weak";
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function KpiCard({
  label,
  value,
  icon,
  sub,
  isLoading,
  accentColor = "indigo",
}: {
  label: string;
  value: React.ReactNode;
  icon: React.ReactNode;
  sub?: React.ReactNode;
  isLoading: boolean;
  accentColor?: "indigo" | "emerald" | "blue" | "purple";
}) {
  const accentStyles = {
    indigo: "bg-indigo-50 text-indigo-600 border-indigo-200/80 ring-4 ring-indigo-50/60",
    emerald: "bg-emerald-50 text-emerald-600 border-emerald-200/80 ring-4 ring-emerald-50/60",
    blue: "bg-blue-50 text-blue-600 border-blue-200/80 ring-4 ring-blue-50/60",
    purple: "bg-purple-50 text-purple-600 border-purple-200/80 ring-4 ring-purple-50/60",
  };

  return (
    <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-[0_2px_8px_-2px_rgba(0,0,0,0.06),0_1px_3px_rgba(0,0,0,0.04)] hover:shadow-[0_8px_24px_-4px_rgba(0,0,0,0.09)] hover:-translate-y-0.5 transition-all duration-200 flex flex-col justify-between group">
      <div className="flex items-start justify-between gap-3 mb-3">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">{label}</span>
        <div className={cn("w-10 h-10 rounded-xl border flex items-center justify-center shrink-0 shadow-sm transition-transform duration-200 group-hover:scale-110", accentStyles[accentColor])}>
          {icon}
        </div>
      </div>
      <div className="text-3xl font-black text-slate-900 tracking-tight min-h-[2.5rem] flex items-center">
        {isLoading ? (
          <span className="inline-block w-20 h-7 bg-slate-100 rounded-md animate-pulse" />
        ) : (
          value
        )}
      </div>
      {sub && <div className="mt-3.5 pt-2.5 border-t border-slate-100">{sub}</div>}
    </div>
  );
}

function OnboardingGuide() {
  const steps = [
    {
      step: "01",
      icon: <Upload className="w-5 h-5 text-indigo-600" />,
      badge: "Step 01",
      title: "Upload Your Resume",
      desc: "Upload your PDF or DOCX resume so the AI can build your candidate profile and skills graph.",
      href: "/resume",
      cta: "Upload Resume",
      borderAccent: "hover:border-indigo-300 hover:shadow-indigo-100/50",
      badgeColor: "bg-indigo-50 text-indigo-700 border-indigo-200/80",
      iconBg: "bg-indigo-50/80 border-indigo-100 text-indigo-600 ring-4 ring-indigo-50/50",
    },
    {
      step: "02",
      icon: <Briefcase className="w-5 h-5 text-blue-600" />,
      badge: "Step 02",
      title: "Add a Job Description",
      desc: "Provide the target role specifications to trigger the hybrid semantic matching engine.",
      href: "/jobs",
      cta: "Add Job Description",
      borderAccent: "hover:border-blue-300 hover:shadow-blue-100/50",
      badgeColor: "bg-blue-50 text-blue-700 border-blue-200/80",
      iconBg: "bg-blue-50/80 border-blue-100 text-blue-600 ring-4 ring-blue-50/50",
    },
    {
      step: "03",
      icon: <PlayCircle className="w-5 h-5 text-emerald-600" />,
      badge: "Step 03",
      title: "Start Live Interview",
      desc: "Begin an adaptive session with multi-criteria rubric evaluation and real-time voice coaching.",
      href: "/interview",
      cta: "Start Interview",
      borderAccent: "hover:border-emerald-300 hover:shadow-emerald-100/50",
      badgeColor: "bg-emerald-50 text-emerald-700 border-emerald-200/80",
      iconBg: "bg-emerald-50/80 border-emerald-100 text-emerald-600 ring-4 ring-emerald-50/50",
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600 ring-4 ring-indigo-50/50">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider">Fast-Track Setup</h2>
            <p className="text-xs text-slate-500">Complete these 3 steps to unlock full AI interview preparation</p>
          </div>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {steps.map((s) => (
          <div
            key={s.step}
            className={cn(
              "bg-white border-2 border-slate-200/90 rounded-2xl p-6 shadow-[0_2px_8px_-2px_rgba(0,0,0,0.06),0_1px_3px_rgba(0,0,0,0.04)] hover:shadow-[0_10px_25px_-5px_rgba(0,0,0,0.08)] hover:-translate-y-1 transition-all duration-200 flex flex-col justify-between gap-5 group",
              s.borderAccent
            )}
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className={cn("text-[11px] font-bold px-2.5 py-1 rounded-full border font-mono tracking-wide", s.badgeColor)}>
                  {s.badge}
                </span>
                <div className={cn("w-11 h-11 rounded-2xl border flex items-center justify-center transition-transform duration-200 group-hover:scale-110 shadow-sm", s.iconBg)}>
                  {s.icon}
                </div>
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-1.5 group-hover:text-indigo-600 transition-colors">
                {s.title}
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">{s.desc}</p>
            </div>
            <Link href={s.href} className="mt-auto block pt-2">
              <Button variant="outline" size="sm" className="w-full justify-between font-bold py-2 border-slate-200 bg-slate-50/80 hover:bg-indigo-50 hover:text-indigo-600 hover:border-indigo-200 transition-all group-hover:border-slate-300">
                <span>{s.cta}</span>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition-all" />
              </Button>
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Custom Tooltip for Recharts ──────────────────────────────────────────────

const ChartTooltip = ({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs shadow-xl">
        <div className="text-slate-500 mb-1">{label}</div>
        <div className="text-slate-900 font-bold">{payload[0].value.toFixed(1)}%</div>
      </div>
    );
  }
  return null;
};

// ─── Main Dashboard ───────────────────────────────────────────────────────────

export default function Dashboard() {
  const { userId, name } = useAuth();
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [skillGap, setSkillGap] = useState<SkillGapResponse | null>(null);
  const [mlReadiness, setMlReadiness] = useState<MLReadinessResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const effectiveUserId = userId ?? 1;

  useEffect(() => {
    async function load() {
      try {
        const [aRes, gRes, mRes] = await Promise.all([
          fetch(`/api/py/analytics/${effectiveUserId}`),
          fetch(`/api/py/skill-gaps?user_id=${effectiveUserId}`),
          fetch(`/api/py/ml/readiness?user_id=${effectiveUserId}`),
        ]);
        if (aRes.ok) setAnalytics(await aRes.json());
        if (gRes.ok) setSkillGap(await gRes.json());
        if (mRes.ok) setMlReadiness(await mRes.json());
      } catch {
        // handled via null state
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [effectiveUserId]);



  const totalSessions = analytics?.total_interviews ?? 0;
  const completedSessions = analytics?.completed_interviews ?? 0;
  const hasData = analytics !== null && totalSessions > 0;
  const hasCompletedData = analytics !== null && completedSessions > 0;
  const avgScore = hasCompletedData ? analytics!.average_overall_score : null;
  const matchScore = skillGap?.overall_match_score ?? null;
  // Use real ML prediction if available, otherwise fall back to analytics label
  const readinessTier =
    mlReadiness?.has_data && mlReadiness.readiness_label
      ? mlReadiness.readiness_label
      : hasCompletedData
      ? analytics!.overall_readiness_label
      : "Not Evaluated";
  const mlScore = mlReadiness?.has_data ? mlReadiness.readiness_score : null;
  const mlArch = mlReadiness?.model_architecture ?? "";

  // Only include sessions that have actual completed scores
  const scoredEntries = (analytics?.score_history ?? []).filter((e) => e.score !== null);
  const scoreHistory = scoredEntries.map((e, i) => ({
    name: `Session ${i + 1}`,
    score: parseFloat((e.score ?? 0).toFixed(1)),
  }));

  const topicData = Object.entries(analytics?.topic_performance ?? {}).map(([topic, raw]) => ({
    topic: topic.replace(/_/g, " "),
    score: parseFloat((raw ?? 0).toFixed(1)),
  }));

  const weakAreas = analytics?.weak_areas ?? [];
  const strongAreas = analytics?.strong_areas ?? [];
  const missingSkills = skillGap?.gap_report?.missing_skills ?? [];
  const highPriorityGaps = skillGap?.gap_report?.high_priority_gaps ?? [];

  const hasValidDimensions =
    hasCompletedData &&
    (analytics!.average_technical_score > 0 ||
      analytics!.average_communication_score > 0 ||
      analytics!.average_relevance_score > 0);

  const scoreDimensions = hasValidDimensions
    ? [
        { label: "Technical Accuracy", value: analytics!.average_technical_score, color: "blue" as const },
        { label: "Communication", value: analytics!.average_communication_score, color: "emerald" as const },
        { label: "Relevance", value: analytics!.average_relevance_score, color: "amber" as const },
        { label: "Completeness", value: analytics!.average_completeness_score, color: "purple" as const },
        { label: "Clarity", value: analytics!.average_clarity_score, color: "rose" as const },
      ]
    : [];


  return (
    <div className="space-y-6">
      {/* ── Greeting Header ───────────────────────────────────────────────── */}
      <div className="pt-2 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Good morning, {name && name !== "Candidate" ? name.split(" ")[0] : "Candidate"}
          </h1>
          <p className="text-sm text-slate-600 mt-1">Continue your interview preparation journey.</p>

          {skillGap?.gap_report?.job_description_info?.target_role && (
            <div className="mt-2.5 flex items-center gap-2">
              <span className="text-[11px] text-slate-400 font-bold uppercase tracking-wider">Target Role</span>
              <span className="text-sm font-bold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-md border border-indigo-100">
                {skillGap.gap_report.job_description_info.target_role}
              </span>
            </div>
          )}
        </div>
        <Link href="/interview">
          <Button variant="primary" size="md" className="shadow-sm font-semibold">
            <Sparkles className="w-4 h-4 mr-1.5" />
            Start Interview
          </Button>
        </Link>
      </div>

      {/* ── KPI Strip ────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Total Sessions"
          value={totalSessions}
          icon={<Layers className="w-5 h-5" />}
          accentColor="indigo"
          sub={
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              SQLite persisted
            </div>
          }
          isLoading={isLoading}
        />
        <KpiCard
          label="Avg Overall Score"
          value={avgScore !== null ? `${avgScore.toFixed(1)}%` : "—"}
          icon={<Target className="w-5 h-5" />}
          accentColor="emerald"
          sub={
            avgScore !== null ? (
              <ProgressBar value={avgScore} size="sm" color="emerald" showPercentage={false} />
            ) : (
              <span className="text-xs text-slate-400 italic">Complete an interview to calculate</span>
            )
          }
          isLoading={isLoading}
        />
        <KpiCard
          label="Job Match"
          value={matchScore !== null ? `${matchScore.toFixed(1)}%` : "—"}
          icon={<BarChart2 className="w-5 h-5" />}
          accentColor="blue"
          sub={
            skillGap ? (
              <Badge variant={matchBadgeVariant(skillGap.match_category)} size="sm">
                {skillGap.match_category}
              </Badge>
            ) : (
              <span className="text-xs text-slate-400 italic">Run matching to see score</span>
            )
          }
          isLoading={isLoading}
        />
        <KpiCard
          label="Interview Readiness"
          value={
            readinessTier === "Not Evaluated" ? (
              <span className="text-base font-bold text-slate-400">Not Evaluated</span>
            ) : (
              readinessTier
            )
          }
          icon={<Zap className="w-5 h-5" />}
          accentColor="purple"
          sub={
            mlScore !== null ? (
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant={readinessBadgeVariant(readinessTier)} size="sm">
                  {mlScore.toFixed(1)}% · {mlArch || "ML Model"}
                </Badge>
              </div>
            ) : (
              <Badge variant={readinessBadgeVariant(readinessTier)} size="sm">
                {readinessTier === "Not Evaluated" ? "Complete interview first" : "ML Assessment"}
              </Badge>
            )
          }
          isLoading={isLoading}
        />
      </div>

      {/* ── Empty State Onboarding ────────────────────────────────────────── */}
      {!isLoading && !hasData && <OnboardingGuide />}

      {/* ── Score Trajectory Chart ────────────────────────────────────────── */}
      {hasData && (
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Score Trajectory</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">Overall performance across all sessions</p>
            </div>
            <TrendingUp className="w-4 h-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            {scoreHistory.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={scoreHistory} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 11, fill: "#94a3b8" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[0, 100]}
                    tick={{ fontSize: 11, fill: "#94a3b8" }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v) => `${v}%`}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={{ r: 3.5, fill: "#2563eb", strokeWidth: 0 }}
                    activeDot={{ r: 5, fill: "#60a5fa" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center py-6 gap-2 text-center">
                <TrendingUp className="w-6 h-6 text-slate-300" />
                <p className="text-xs font-semibold text-slate-700">No scored sessions yet</p>
                <p className="text-[11px] text-slate-400 max-w-xs">
                  Complete an interview to track your score trajectory.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Topic Mastery & Score Dimensions ─────────────────────────────── */}
      {hasData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Topic mastery */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Topic Mastery</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">Average score per interview domain</p>
              </div>
              <BarChart2 className="w-4 h-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              {topicData.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={topicData} layout="vertical" margin={{ top: 0, right: 24, bottom: 0, left: 80 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                    <XAxis
                      type="number"
                      domain={[0, 100]}
                      tick={{ fontSize: 10, fill: "#94a3b8" }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(v) => `${v}%`}
                    />
                    <YAxis
                      type="category"
                      dataKey="topic"
                      tick={{ fontSize: 10, fill: "#94a3b8" }}
                      axisLine={false}
                      tickLine={false}
                      width={76}
                    />
                    <Tooltip content={<ChartTooltip />} />
                    <Bar dataKey="score" radius={[0, 4, 4, 0]} maxBarSize={18}>
                      {topicData.map((entry, i) => (
                        <Cell key={i} fill={topicColor(entry.score)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 gap-2 text-center">
                  <BarChart2 className="w-6 h-6 text-slate-300" />
                  <p className="text-xs font-semibold text-slate-700">No topic data yet</p>
                  <p className="text-[11px] text-slate-400 max-w-xs">
                    Complete an interview to see topic mastery.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Score dimensions */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle className="text-base font-bold text-slate-900">Performance Dimensions</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">Multi-axis evaluation breakdown</p>
              </div>
              <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-200/80 flex items-center justify-center text-indigo-600 ring-4 ring-indigo-50/50 shadow-sm">
                <Target className="w-4.5 h-4.5" />
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {scoreDimensions.length > 0 ? (
                scoreDimensions.map((d) => (
                  <ProgressBar
                    key={d.label}
                    label={d.label}
                    value={d.value}
                    color={d.color}
                    size="md"
                  />
                ))
              ) : (
                <div className="flex flex-col items-center justify-center py-8 gap-2 text-center">
                  <Target className="w-6 h-6 text-slate-300" />
                  <p className="text-xs font-semibold text-slate-700">No evaluation data yet</p>
                  <p className="text-[11px] text-slate-400 max-w-xs">
                    Complete an interview to see multi-axis skill evaluation breakdown.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ── Skill Gaps & Recommended Focus ───────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Skill Gaps */}
        <Card>
          <CardHeader>
            <div>
              <CardTitle className="text-base font-bold text-slate-900">Skill Gaps</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                {skillGap ? "From job description analysis" : "Run a job match to identify gaps"}
              </p>
            </div>
            <div className="w-9 h-9 rounded-xl bg-amber-50 border border-amber-200/80 flex items-center justify-center text-amber-600 ring-4 ring-amber-50/50 shadow-sm">
              <AlertTriangle className="w-4.5 h-4.5" />
            </div>
          </CardHeader>
          <CardContent>
            {!skillGap ? (
              <EmptyState
                icon={<AlertTriangle className="w-6 h-6 text-amber-600" />}
                title="No Skill Analysis Yet"
                description="Upload a job description and run matching to identify your skill gaps."
                action={
                  <Link href="/matching">
                    <Button variant="outline" size="sm" className="font-semibold shadow-sm hover:border-amber-300 hover:bg-amber-50/50">
                      Run Job Match <ChevronRight className="w-4 h-4 ml-1 text-slate-400" />
                    </Button>
                  </Link>
                }
              />
            ) : highPriorityGaps.length === 0 && missingSkills.length === 0 ? (
              <div className="flex items-center gap-2 py-4 text-emerald-600 text-sm">
                <CheckCircle2 className="w-4 h-4" />
                No critical skill gaps detected for this role.
              </div>
            ) : (
              <div className="space-y-2">
                {highPriorityGaps.length > 0 && (
                  <div>
                    <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">High Priority</div>
                    <div className="flex flex-wrap gap-1.5">
                      {highPriorityGaps.map((gap, i) => {
                        const skillName = typeof gap === "string" ? gap : gap.skill;
                        return (
                          <Badge key={`${skillName}-${i}`} variant="danger" size="sm">{skillName}</Badge>
                        );
                      })}
                    </div>
                  </div>
                )}
                {missingSkills.length > 0 && (
                  <div className="mt-3">
                    <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Missing Skills</div>
                    <div className="flex flex-wrap gap-1.5">
                      {missingSkills.map((skill, i) => {
                        const skillName = typeof skill === "string" ? skill : (skill as any).skill ?? String(skill);
                        return (
                          <Badge key={`${skillName}-${i}`} variant="warning" size="sm">{skillName}</Badge>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recommended Focus */}
        <Card>
          <CardHeader>
            <div>
              <CardTitle className="text-base font-bold text-slate-900">Recommended Focus</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                {weakAreas.length > 0 ? "Based on your interview performance" : "Awaiting interview data"}
              </p>
            </div>
            <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-200/80 flex items-center justify-center text-indigo-600 ring-4 ring-indigo-50/50 shadow-sm">
              <BookOpen className="w-4.5 h-4.5" />
            </div>
          </CardHeader>
          <CardContent>
            {weakAreas.length === 0 && strongAreas.length === 0 ? (
              <EmptyState
                icon={<BookOpen className="w-6 h-6 text-indigo-600" />}
                title="No Focus Data Yet"
                description="Complete an interview session to see personalized topic recommendations."
                action={
                  <Link href="/interview">
                    <Button variant="outline" size="sm" className="font-semibold shadow-sm hover:border-indigo-300 hover:bg-indigo-50/50">
                      Start Interview <ChevronRight className="w-4 h-4 ml-1 text-slate-400" />
                    </Button>
                  </Link>
                }
              />
            ) : (
              <div className="space-y-4">
                {weakAreas.length > 0 && (
                  <div>
                    <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">Needs Work</div>
                    <ul className="space-y-1.5">
                      {weakAreas.map((area) => (
                        <li key={area} className="flex items-center gap-2 text-sm text-slate-700">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" />
                          {area.replace(/_/g, " ")}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {strongAreas.length > 0 && (
                  <div>
                    <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">Strengths</div>
                    <ul className="space-y-1.5">
                      {strongAreas.map((area) => (
                        <li key={area} className="flex items-center gap-2 text-sm text-slate-700">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0" />
                          {area.replace(/_/g, " ")}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Recent Interview Activity ──────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Recent Practice Sessions</CardTitle>
            <p className="text-xs text-slate-500 mt-0.5">Your last completed sessions</p>
          </div>
          <Link href="/history" className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
            View all <ChevronRight className="w-3 h-3" />
          </Link>
        </CardHeader>
        {scoreHistory.length === 0 ? (
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8 text-center gap-3">
              <Clock className="w-8 h-8 text-slate-300" />
              <p className="text-sm text-slate-400">No interview sessions recorded yet.</p>
              <Link href="/interview">
                <Button variant="primary" size="sm">
                  <ArrowRight className="w-3.5 h-3.5" />
                  Start Your First Session
                </Button>
              </Link>
            </div>
          </CardContent>
        ) : (
          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left px-5 py-2.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Date</th>
                  <th className="text-left px-3 py-2.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Role</th>
                  <th className="text-right px-3 py-2.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Score</th>
                  <th className="text-left px-3 py-2.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Readiness</th>
                  <th className="text-left px-3 py-2.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Status</th>
                  <th className="px-5 py-2.5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {[...scoreHistory].reverse().slice(0, 5).map((s, idx) => {
                  const entry = [...(analytics?.score_history ?? [])].reverse()[idx];
                  const score = s.score;
                  const badgeVariant: "success" | "warning" | "danger" | "info" | "default" =
                    score >= 80 ? "success" : score >= 60 ? "info" : score >= 40 ? "warning" : "danger";
                  return (
                    <tr key={entry?.session_id ?? idx} className="hover:bg-slate-50 transition-colors">
                      <td className="px-5 py-3 text-xs text-slate-400 whitespace-nowrap">
                        {entry?.date ?? `Session ${idx + 1}`}
                      </td>
                      <td className="px-3 py-3 text-slate-700 font-medium max-w-[160px] truncate">
                        {entry?.role ?? `Session #${entry?.session_id ?? idx + 1}`}
                      </td>
                      <td className="px-3 py-3 text-right font-bold font-mono tabular-nums text-slate-800">
                        {score.toFixed(1)}%
                      </td>
                      <td className="px-3 py-3">
                        <Badge variant={badgeVariant} size="sm">
                          {entry?.readiness ?? formatScoreLabel(score)}
                        </Badge>
                      </td>
                      <td className="px-3 py-3">
                        <Badge variant="success" size="sm">Completed</Badge>
                      </td>
                      <td className="px-5 py-3">
                        <Link href={`/history`} className="text-xs text-blue-600 hover:underline font-medium">View</Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}