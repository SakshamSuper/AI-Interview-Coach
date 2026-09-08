"use client";

import { useAuth } from "@/contexts/AuthContext";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ChevronRight,
  RefreshCw,
  Sparkles,
  Target,
  TrendingUp,
  FileText,
  Briefcase,
  Zap,
  BarChart2,
  BookOpen,
  ArrowRight,
  Info,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";

// ─── API Types (mirrors backend Pydantic schemas exactly) ─────────────────────

interface SkillMatchItem {
  skill: string;
  match_score: number;
  category: "Strong Match" | "Matched" | "Partially Matched" | "Missing";
  is_required: boolean;
  context_found?: string | null;
}

interface SkillGapItem {
  skill: string;
  is_required: boolean;
  gap_priority: "High" | "Medium" | "Low";
  current_proficiency_estimate: number;
  recommended_topics: string[];
}

interface SkillGapReport {
  strong_skills: string[];
  matched_skills: string[];
  partially_matched_skills: string[];
  missing_skills: string[];
  high_priority_gaps: SkillGapItem[];
}

interface MatchScoreExplanation {
  required_skills_coverage: number;
  preferred_skills_coverage: number;
  semantic_similarity_score: number;
  experience_education_alignment: number;
  summary_explanation: string;
}

interface MatchAnalysisResponse {
  overall_match_score: number;
  match_category: string;
  skill_breakdown: SkillMatchItem[];
  gap_report: SkillGapReport;
  explanation: MatchScoreExplanation;
}

type PageState = "idle" | "checking" | "running" | "success" | "error" | "no_resume" | "no_jd";

// USER_ID is now derived from the authenticated session — see useAuth() below
const RESUME_ID_KEY = "ai_coach_resume_id";
const JD_ID_KEY = "ai_coach_jd_id";

// ─── API layer ────────────────────────────────────────────────────────────────

async function runMatchAnalysis(
  userId: number,
  resumeId: number | null,
  jdId: number | null
): Promise<MatchAnalysisResponse> {
  const body: Record<string, number> = { user_id: userId };
  if (resumeId) body.resume_id = resumeId;
  if (jdId) body.jd_id = jdId;

  const res = await fetch("/api/py/matching", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Matching failed." }));
    const detail = Array.isArray(err.detail)
      ? err.detail.map((d: { msg: string }) => d.msg).join("; ")
      : err.detail || `Error ${res.status}`;
    throw new Error(detail);
  }

  return res.json();
}

async function fetchExistingGaps(userId: number): Promise<MatchAnalysisResponse | null> {
  const res = await fetch(`/api/py/skill-gaps?user_id=${userId}`);
  if (!res.ok) return null;
  return res.json();
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function categoryBadge(cat: string) {
  if (cat === "Strong Match") return "success" as const;
  if (cat === "Moderate Match") return "warning" as const;
  if (cat === "Weak Match") return "danger" as const;
  return "default" as const;
}

function scoreColor(score: number): string {
  if (score >= 75) return "text-emerald-600";
  if (score >= 50) return "text-amber-600";
  return "text-red-600";
}

function scoreRingColor(score: number): string {
  if (score >= 75) return "#10b981";
  if (score >= 50) return "#f59e0b";
  return "#ef4444";
}

function priorityVariant(p: string): "danger" | "warning" | "default" {
  if (p === "High") return "danger";
  if (p === "Medium") return "warning";
  return "default";
}

// ─── Score Ring (SVG) ─────────────────────────────────────────────────────────

function ScoreRing({ score, category }: { score: number; category: string }) {
  const r = 52;
  const circ = 2 * Math.PI * r;
  const filled = (score / 100) * circ;
  const color = scoreRingColor(score);

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative w-36 h-36">
        <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
          {/* Track */}
          <circle cx="60" cy="60" r={r} fill="none" stroke="#e2e8f0" strokeWidth="10" />
          {/* Fill */}
          <circle
            cx="60"
            cy="60"
            r={r}
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${filled} ${circ}`}
            style={{ transition: "stroke-dasharray 0.8s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-3xl font-black tracking-tight ${scoreColor(score)}`}>
            {score.toFixed(0)}%
          </span>
          <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wide mt-0.5">
            Match
          </span>
        </div>
      </div>
      <Badge variant={categoryBadge(category)} size="sm">{category}</Badge>
    </div>
  );
}

// ─── Score Breakdown Strip ────────────────────────────────────────────────────

function ScoreBreakdown({ explanation }: { explanation: MatchScoreExplanation }) {
  const rows = [
    { label: "Required Skills", value: explanation.required_skills_coverage, color: "blue" as const },
    { label: "Preferred Skills", value: explanation.preferred_skills_coverage, color: "emerald" as const },
    { label: "Semantic Similarity", value: explanation.semantic_similarity_score, color: "amber" as const },
    { label: "Experience Alignment", value: explanation.experience_education_alignment, color: "purple" as const },
  ];

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Score Breakdown</CardTitle>
          <p className="text-xs text-slate-500 mt-0.5">Weighted components of the overall match</p>
        </div>
        <BarChart2 className="w-4 h-4 text-slate-500" />
      </CardHeader>
      <CardContent className="space-y-3">
        {rows.map((r) => (
          <ProgressBar key={r.label} label={r.label} value={r.value} color={r.color} size="md" />
        ))}
        {explanation.summary_explanation && (
          <div className="flex items-start gap-2 pt-2 border-t border-slate-200">
            <Info className="w-3.5 h-3.5 text-slate-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-slate-500 leading-relaxed">{explanation.summary_explanation}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Skill Category Section ───────────────────────────────────────────────────

function SkillSection({
  title,
  skills,
  variant,
  icon,
  emptyText,
}: {
  title: string;
  skills: string[];
  variant: "success" | "info" | "warning" | "danger" | "default";
  icon: React.ReactNode;
  emptyText?: string;
}) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-slate-500">{icon}</span>
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">{title}</span>
        {skills.length > 0 && (
          <span className="text-[10px] text-slate-500 font-mono ml-1">{skills.length}</span>
        )}
      </div>
      {skills.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {skills.map((s) => (
            <Badge key={s} variant={variant} size="sm">{s}</Badge>
          ))}
        </div>
      ) : (
        <p className="text-xs text-slate-400 italic">{emptyText ?? "None"}</p>
      )}
    </div>
  );
}

// ─── Priority Gap Card ────────────────────────────────────────────────────────

function PriorityGapList({ gaps }: { gaps: SkillGapItem[] }) {
  if (gaps.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>High-Priority Gaps</CardTitle>
          <p className="text-xs text-slate-500 mt-0.5">Skills ranked by impact on your candidacy</p>
        </div>
        <AlertTriangle className="w-4 h-4 text-amber-600" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {gaps.map((g, i) => (
            <div key={g.skill} className="flex items-start gap-4 py-3 border-b border-slate-200 last:border-0 last:pb-0">
              <span className="text-xs font-bold text-slate-500 font-mono w-5 flex-shrink-0 mt-0.5">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-semibold text-slate-800">{g.skill}</span>
                  <Badge variant={priorityVariant(g.gap_priority)} size="sm">{g.gap_priority} Priority</Badge>
                  {g.is_required && <Badge variant="danger" size="sm">Required</Badge>}
                </div>
                <div className="mb-2">
                  <ProgressBar
                    value={g.current_proficiency_estimate}
                    size="sm"
                    color="amber"
                    showPercentage={false}
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">
                    Current alignment: {g.current_proficiency_estimate.toFixed(0)}%
                  </span>
                </div>
                {g.recommended_topics.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {g.recommended_topics.slice(0, 2).map((t) => (
                      <span key={t} className="text-[10px] text-slate-400 bg-slate-50 border border-slate-300/50 rounded px-1.5 py-0.5">
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Skill Breakdown Table ────────────────────────────────────────────────────

function SkillBreakdownTable({ breakdown }: { breakdown: SkillMatchItem[] }) {
  if (breakdown.length === 0) return null;

  const catVariant = (cat: string) => {
    if (cat === "Strong Match") return "success" as const;
    if (cat === "Matched") return "info" as const;
    if (cat === "Partially Matched") return "warning" as const;
    return "danger" as const;
  };

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Full Skill Breakdown</CardTitle>
          <p className="text-xs text-slate-500 mt-0.5">{breakdown.length} skills evaluated from the job description</p>
        </div>
        <Target className="w-4 h-4 text-blue-600" />
      </CardHeader>
      <CardContent>
        <div className="divide-y divide-slate-100">
          {breakdown.map((item) => (
            <div key={item.skill} className="flex items-center gap-4 py-2.5">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-800">{item.skill}</span>
                  {item.is_required && (
                    <span className="text-[9px] font-bold text-red-600 uppercase tracking-wider">Required</span>
                  )}
                </div>
                {item.context_found && (
                  <p className="text-[11px] text-slate-400 truncate mt-0.5">{item.context_found}</p>
                )}
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                <span className={`text-xs font-bold font-mono ${scoreColor(item.match_score)}`}>
                  {item.match_score.toFixed(0)}%
                </span>
                <Badge variant={catVariant(item.category)} size="sm">{item.category}</Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Empty / Prerequisite States ─────────────────────────────────────────────

function PrerequisiteCard({
  icon,
  title,
  description,
  href,
  cta,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  href: string;
  cta: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-12 text-center max-w-md mx-auto">
      <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-300 flex items-center justify-center">
        {icon}
      </div>
      <div>
        <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
        <p className="text-xs text-slate-500 mt-1 leading-relaxed">{description}</p>
      </div>
      <Link href={href}>
        <Button variant="outline" size="sm">
          {cta} <ChevronRight className="w-3.5 h-3.5 ml-1" />
        </Button>
      </Link>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function MatchingPage() {
  const { userId: USER_ID } = useAuth();
  const [pageState, setPageState] = useState<PageState>("checking");
  const [errorMsg, setErrorMsg] = useState("");
  const [result, setResult] = useState<MatchAnalysisResponse | null>(null);
  const [resumeId, setResumeId] = useState<number | null>(null);
  const [jdId, setJdId] = useState<number | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  // On mount: read IDs from localStorage and try to load existing gaps
  useEffect(() => {
    const rid = localStorage.getItem(RESUME_ID_KEY);
    const jid = localStorage.getItem(JD_ID_KEY);

    const rIdNum = rid ? parseInt(rid, 10) : null;
    const jIdNum = jid ? parseInt(jid, 10) : null;

    setResumeId(rIdNum);
    setJdId(jIdNum);

    if (!rIdNum) {
      setPageState("no_resume");
      return;
    }
    if (!jIdNum) {
      setPageState("no_jd");
      return;
    }

    // Try loading an existing analysis first
    fetchExistingGaps(USER_ID ?? 1)
      .then((data) => {
        if (data) {
          setResult(data);
          setPageState("success");
        } else {
          setPageState("idle");
        }
      })
      .catch(() => setPageState("idle"));
  }, [USER_ID]);

  const handleRunAnalysis = useCallback(async () => {
    if (isRunning) return;
    setIsRunning(true);
    setPageState("running");
    setErrorMsg("");

    try {
      const data = await runMatchAnalysis(USER_ID ?? 1, resumeId, jdId);
      setResult(data);
      setPageState("success");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Match analysis failed.";
      setErrorMsg(msg);
      setPageState("error");
    } finally {
      setIsRunning(false);
    }
  }, [resumeId, jdId, isRunning]);

  const handleRerun = () => {
    setResult(null);
    setPageState("idle");
    setErrorMsg("");
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">Match & Skill Gap</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Compare your candidate profile against the target role requirements
          </p>
        </div>
        <div className="flex items-center gap-2">
          {pageState === "success" && result && (
            <>
              <Badge variant={categoryBadge(result.match_category)} size="sm">
                {result.match_category}
              </Badge>
              <Button variant="ghost" size="sm" onClick={handleRerun}>
                <RefreshCw className="w-3.5 h-3.5" />
                Re-run
              </Button>
            </>
          )}
          {pageState === "idle" && (
            <Button variant="primary" size="sm" onClick={handleRunAnalysis} isLoading={isRunning}>
              <Sparkles className="w-3.5 h-3.5" />
              Run Match Analysis
            </Button>
          )}
        </div>
      </div>

      {/* ── States ─────────────────────────────────────────────────────── */}

      {/* Checking */}
      {pageState === "checking" && (
        <div className="flex items-center justify-center py-24">
          <div className="flex items-center gap-3 text-slate-500">
            <RefreshCw className="w-5 h-5 animate-spin" />
            <span className="text-sm">Loading profile data...</span>
          </div>
        </div>
      )}

      {/* No resume */}
      {pageState === "no_resume" && (
        <PrerequisiteCard
          icon={<FileText className="w-5 h-5 text-slate-500" />}
          title="Resume required"
          description="Upload your resume first so the matching engine can compare your skills against the job requirements."
          href="/resume"
          cta="Upload Resume"
        />
      )}

      {/* No JD */}
      {pageState === "no_jd" && (
        <PrerequisiteCard
          icon={<Briefcase className="w-5 h-5 text-slate-500" />}
          title="Job description required"
          description="Add a target job description so the matching engine has requirements to compare against."
          href="/jobs"
          cta="Add Job Description"
        />
      )}

      {/* Running */}
      {pageState === "running" && (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <div className="w-14 h-14 rounded-xl bg-slate-100 border border-slate-300 flex items-center justify-center">
            <RefreshCw className="w-7 h-7 text-blue-600 animate-spin" />
          </div>
          <div className="text-center">
            <div className="text-sm font-semibold text-slate-800">Analyzing your profile...</div>
            <div className="text-xs text-slate-400 mt-1">
              Running hybrid NLP matching · semantic similarity · skill gap analysis
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {pageState === "error" && (
        <div className="max-w-xl mx-auto">
          <div className="flex items-start gap-3 rounded-xl bg-red-50 border border-red-200 p-4">
            <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-sm font-semibold text-red-600">Analysis failed</div>
              <div className="text-xs text-red-600/80 mt-1 leading-relaxed">{errorMsg}</div>
              <div className="mt-3 flex gap-2">
                <Button variant="outline" size="sm" onClick={handleRunAnalysis} isLoading={isRunning}>
                  Try Again
                </Button>
                <Link href="/resume">
                  <Button variant="ghost" size="sm">Check Resume</Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Idle: ready to run */}
      {pageState === "idle" && (
        <div className="max-w-md mx-auto">
          <div className="flex flex-col items-center justify-center gap-5 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-12 text-center">
            <div className="w-14 h-14 rounded-xl bg-slate-100 border border-slate-300 flex items-center justify-center">
              <Target className="w-7 h-7 text-blue-600" />
            </div>
            <div>
              <h4 className="text-base font-semibold text-slate-800">Ready to analyze your fit</h4>
              <p className="text-xs text-slate-500 mt-1.5 leading-relaxed max-w-xs">
                Both your resume and job description are loaded. Run the matching engine to see your score, skill gaps, and interview focus areas.
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              Resume loaded
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 ml-2" />
              Job description loaded
            </div>
            <Button variant="primary" size="md" onClick={handleRunAnalysis} isLoading={isRunning}>
              <Sparkles className="w-4 h-4" />
              {isRunning ? "Analyzing..." : "Run Match Analysis"}
            </Button>
          </div>
        </div>
      )}

      {/* ── Success ─────────────────────────────────────────────────────── */}
      {pageState === "success" && result && (
        <div className="space-y-6">
          {/* Match overview card */}
          <Card>
            <CardContent>
              <div className="flex flex-col md:flex-row md:items-center gap-8">
                {/* Score Ring */}
                <div className="flex-shrink-0 flex justify-center">
                  <ScoreRing
                    score={result.overall_match_score}
                    category={result.match_category}
                  />
                </div>

                {/* Skill summary columns */}
                <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <SkillSection
                    title="Strong Matches"
                    skills={result.gap_report.strong_skills}
                    variant="success"
                    icon={<CheckCircle2 className="w-3.5 h-3.5" />}
                    emptyText="No strong matches detected"
                  />
                  <SkillSection
                    title="Matched Skills"
                    skills={result.gap_report.matched_skills}
                    variant="info"
                    icon={<TrendingUp className="w-3.5 h-3.5" />}
                    emptyText="No partial matches"
                  />
                  <SkillSection
                    title="Partially Matched"
                    skills={result.gap_report.partially_matched_skills}
                    variant="warning"
                    icon={<Zap className="w-3.5 h-3.5" />}
                    emptyText="None"
                  />
                  <SkillSection
                    title="Missing Skills"
                    skills={result.gap_report.missing_skills}
                    variant="danger"
                    icon={<XCircle className="w-3.5 h-3.5" />}
                    emptyText="No missing skills — full coverage"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Score Breakdown */}
          <ScoreBreakdown explanation={result.explanation} />

          {/* Priority Gaps */}
          {result.gap_report.high_priority_gaps.length > 0 ? (
            <PriorityGapList gaps={result.gap_report.high_priority_gaps} />
          ) : (
            <Card>
              <CardContent>
                <div className="flex items-center gap-3 py-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                  <div>
                    <div className="text-sm font-semibold text-slate-800">No high-priority gaps identified</div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      Your profile covers all critical requirements for this role.
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Full Skill Breakdown */}
          <SkillBreakdownTable breakdown={result.skill_breakdown} />

          {/* Interview Connection */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Interview Focus Areas</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">
                  Your adaptive interview will be tailored based on this analysis
                </p>
              </div>
              <BookOpen className="w-4 h-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {result.gap_report.high_priority_gaps.length > 0 ? (
                  <>
                    <p className="text-xs text-slate-500">
                      The session will prioritize these areas based on your identified gaps:
                    </p>
                    <ul className="space-y-2">
                      {result.gap_report.high_priority_gaps.slice(0, 5).map((g) => (
                        <li key={g.skill} className="flex items-center gap-2 text-sm text-slate-700">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" />
                          {g.skill}
                          <span className="text-xs text-slate-400">— {g.recommended_topics[0]}</span>
                        </li>
                      ))}
                    </ul>
                  </>
                ) : result.gap_report.strong_skills.length > 0 ? (
                  <>
                    <p className="text-xs text-slate-500">
                      Strong profile detected. Your interview will assess depth across your matched skills:
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {result.gap_report.strong_skills.slice(0, 8).map((s) => (
                        <Badge key={s} variant="success" size="sm">{s}</Badge>
                      ))}
                      {result.gap_report.strong_skills.length > 8 && (
                        <span className="text-xs text-slate-400 self-center">
                          +{result.gap_report.strong_skills.length - 8} more
                        </span>
                      )}
                    </div>
                  </>
                ) : (
                  <p className="text-xs text-slate-400 italic">No specific focus areas determined yet.</p>
                )}

                {/* CTA */}
                <div className="flex items-center justify-between pt-4 border-t border-slate-200 mt-4">
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <ArrowRight className="w-3.5 h-3.5 text-blue-600" />
                    Questions will be generated based on your skill gap profile
                  </div>
                  <Link href="/interview">
                    <Button variant="primary" size="sm">
                      <Sparkles className="w-3.5 h-3.5" />
                      Start Adaptive Interview
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}