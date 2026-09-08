"use client";

import { useAuth } from "@/contexts/AuthContext";

import React, { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import {
  Briefcase,
  CheckCircle2,
  AlertTriangle,
  X,
  ChevronRight,
  ListChecks,
  Star,
  Layers,
  GraduationCap,
  RefreshCw,
  FileSearch,
  Sparkles,
  Clock,
  Target,
  ArrowRight,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";

// ─── Types ────────────────────────────────────────────────────────────────────

interface JobProfile {
  job_title: string;
  role_level?: string | null;
  required_skills: string[];
  preferred_skills: string[];
  responsibilities: string[];
  technologies: string[];
  education_requirements: string[];
  min_years_experience?: number | null;
  domain_requirements: string[];
  keywords: string[];
}

interface JobAnalyzeResponse {
  jd_id: number;
  profile: JobProfile;
}

type PageState = "idle" | "analyzing" | "success" | "error";

// USER_ID is now derived from the authenticated session — see useAuth() below
const JD_ID_KEY = "ai_coach_jd_id";
const MAX_CHARS = 20000;

// ─── Helpers ──────────────────────────────────────────────────────────────────

function SkillPills({ skills, variant = "default" }: { skills: string[]; variant?: "default" | "info" | "success" | "warning" | "danger" | "purple" }) {
  if (!skills.length) return <span className="text-xs text-slate-400 italic">None extracted</span>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {skills.map((s) => (
        <Badge key={s} variant={variant} size="sm">{s}</Badge>
      ))}
    </div>
  );
}

function SectionLabel({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span className="text-slate-500">{icon}</span>
      <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">{text}</span>
    </div>
  );
}

// ─── JD Profile Display ───────────────────────────────────────────────────────

function JobProfileView({ data, onReset }: {
  data: JobAnalyzeResponse;
  onReset: () => void;
}) {
  const p = data.profile;

  const levelVariant = (level?: string | null): "success" | "warning" | "info" | "default" => {
    if (!level) return "default";
    if (level === "Senior" || level === "Staff" || level === "Lead") return "warning";
    if (level === "Junior") return "info";
    return "default";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-200 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-800">Job description analyzed</div>
            <div className="flex items-center gap-2 mt-0.5">
              <Briefcase className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-xs text-slate-400">{p.job_title}</span>
              <Badge variant="success" size="sm">JD #{data.jd_id}</Badge>
            </div>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={onReset}>
          <RefreshCw className="w-3.5 h-3.5" />
          Analyze New JD
        </Button>
      </div>

      {/* Role summary card */}
      <Card>
        <CardContent>
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex-1">
              <h2 className="text-xl font-bold text-slate-900">{p.job_title}</h2>
              <div className="flex flex-wrap items-center gap-2 mt-2">
                {p.role_level && (
                  <Badge variant={levelVariant(p.role_level)} size="sm">{p.role_level}</Badge>
                )}
                {p.min_years_experience != null && (
                  <div className="flex items-center gap-1.5 text-xs text-slate-500">
                    <Clock className="w-3.5 h-3.5" />
                    {p.min_years_experience}+ years experience
                  </div>
                )}
                {p.education_requirements.length > 0 && (
                  <div className="flex items-center gap-1.5 text-xs text-slate-500">
                    <GraduationCap className="w-3.5 h-3.5" />
                    {p.education_requirements.join(" or ")}
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="text-center px-4 py-2 rounded-lg bg-slate-50 border border-slate-300/50">
                <div className="text-xl font-bold text-blue-600">{p.required_skills.length}</div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">Required Skills</div>
              </div>
              <div className="text-center px-4 py-2 rounded-lg bg-slate-50 border border-slate-300/50">
                <div className="text-xl font-bold text-blue-600">{p.preferred_skills.length}</div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">Preferred Skills</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Skills grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div><CardTitle>Required Skills</CardTitle></div>
            <ListChecks className="w-4 h-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <SkillPills skills={p.required_skills} variant="danger" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div><CardTitle>Preferred Skills</CardTitle></div>
            <Star className="w-4 h-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <SkillPills skills={p.preferred_skills} variant="warning" />
          </CardContent>
        </Card>
      </div>

      {/* Technologies */}
      {p.technologies.length > 0 && (
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Technologies & Stack</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">All technical skills mentioned in the role</p>
            </div>
            <Layers className="w-4 h-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <SkillPills skills={p.technologies} variant="info" />
          </CardContent>
        </Card>
      )}

      {/* Domain requirements */}
      {p.domain_requirements.length > 0 && (
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Domain Requirements</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">Specialized domain expertise expected</p>
            </div>
            <Target className="w-4 h-4 text-purple-400" />
          </CardHeader>
          <CardContent>
            <SkillPills skills={p.domain_requirements} variant="purple" />
          </CardContent>
        </Card>
      )}

      {/* Responsibilities */}
      {p.responsibilities.length > 0 && (
        <Card>
          <CardHeader>
            <div><CardTitle>Key Responsibilities</CardTitle></div>
            <FileSearch className="w-4 h-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {p.responsibilities.map((r, i) => (
                <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0 mt-1.5" />
                  {r}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* CTA to next step */}
      <div className="flex items-center justify-between rounded-xl bg-slate-50 border border-slate-300/50 p-4">
        <div>
          <div className="text-sm font-semibold text-slate-800">Ready to see how you match?</div>
          <div className="text-xs text-slate-500 mt-0.5">Run skill-gap analysis to compare your profile against this role</div>
        </div>
        <Link href="/matching">
          <Button variant="primary" size="sm">
            Run Skill-Gap Analysis
            <ChevronRight className="w-3.5 h-3.5" />
          </Button>
        </Link>
      </div>
    </div>
  );
}

// ─── Input form ───────────────────────────────────────────────────────────────

function JDInputForm({ onSubmit, isLoading }: {
  onSubmit: (text: string, title: string) => void;
  isLoading: boolean;
}) {
  const [text, setText] = useState("");
  const [title, setTitle] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim().length < 50) return;
    onSubmit(text.trim(), title.trim());
  };

  const charCount = text.length;
  const isValid = charCount >= 50 && charCount <= MAX_CHARS;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Title field */}
      <div>
        <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
          Job Title <span className="text-slate-500 font-normal">(optional — auto-detected if blank)</span>
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          disabled={isLoading}
          placeholder="e.g. Senior Machine Learning Engineer"
          className="w-full px-3 py-2.5 rounded-lg bg-slate-100 border border-slate-300 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-colors disabled:opacity-50"
        />
      </div>

      {/* JD textarea */}
      <div>
        <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
          Job Description Text <span className="text-red-600">*</span>
        </label>
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value.slice(0, MAX_CHARS))}
          disabled={isLoading}
          rows={14}
          placeholder={`Paste the full job description here...\n\nInclude:\n- Required skills and qualifications\n- Responsibilities\n- Preferred / nice-to-have skills\n- Experience requirements\n- Education requirements`}
          className="w-full px-4 py-3 rounded-xl bg-white border border-slate-300 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none font-mono leading-relaxed disabled:opacity-50"
        />
        <div className="flex items-center justify-between mt-1.5">
          <span className="text-xs text-slate-400">Minimum 50 characters required</span>
          <span className={["text-xs font-mono", charCount > MAX_CHARS * 0.9 ? "text-amber-600" : "text-slate-400"].join(" ")}>
            {charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()}
          </span>
        </div>
      </div>

      {/* Submit */}
      <div className="flex items-center justify-between pt-1">
        <p className="text-xs text-slate-400">
          The NLP pipeline will extract skills, requirements, and role level automatically.
        </p>
        <Button
          type="submit"
          variant="primary"
          size="md"
          disabled={!isValid || isLoading}
          isLoading={isLoading}
        >
          {isLoading ? "Analyzing..." : (
            <>
              <Sparkles className="w-3.5 h-3.5" />
              Analyze Job Description
            </>
          )}
        </Button>
      </div>
    </form>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function JobsPage() {
  const { userId: USER_ID } = useAuth();
  const [pageState, setPageState] = useState<PageState>("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [result, setResult] = useState<JobAnalyzeResponse | null>(null);

  // On mount: try to reload last JD from localStorage
  useEffect(() => {
    const savedId = localStorage.getItem(JD_ID_KEY);
    if (savedId && !result) {
      fetch(`/api/py/jobs/${savedId}`)
        .then((r) => r.ok ? r.json() : null)
        .then((data: JobAnalyzeResponse | null) => {
          if (data) {
            setResult(data);
            setPageState("success");
          }
        })
        .catch(() => null);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = useCallback(async (text: string, title: string) => {
    setPageState("analyzing");
    setErrorMsg("");

    try {
      const res = await fetch("/api/py/jobs/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: USER_ID,
          title: title || undefined,
          job_description_text: text,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Analysis failed." }));
        throw new Error(err.detail || `Error ${res.status}`);
      }

      const data: JobAnalyzeResponse = await res.json();
      localStorage.setItem(JD_ID_KEY, String(data.jd_id));
      setResult(data);
      setPageState("success");
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : "Analysis failed. Please try again.");
      setPageState("error");
    }
  }, []);

  const handleReset = () => {
    setResult(null);
    setPageState("idle");
    setErrorMsg("");
    localStorage.removeItem(JD_ID_KEY);
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">Job Description</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Paste a job description to extract requirements, skills, and build your target role profile
          </p>
        </div>
        {pageState === "success" && (
          <Badge variant="success" size="sm">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            Role Profile Active
          </Badge>
        )}
      </div>

      {/* Content */}
      {pageState === "success" && result ? (
        <JobProfileView data={result} onReset={handleReset} />
      ) : (
        <div className="max-w-3xl mx-auto space-y-4">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Paste Job Description</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">Paste the full text of the target role posting</p>
              </div>
              <Briefcase className="w-4 h-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <JDInputForm
                onSubmit={handleSubmit}
                isLoading={pageState === "analyzing"}
              />
            </CardContent>
          </Card>

          {/* Error */}
          {pageState === "error" && (
            <div className="flex items-start gap-3 rounded-lg bg-red-50 border border-red-200 px-4 py-3">
              <AlertTriangle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-red-600">Analysis failed</div>
                <div className="text-xs text-red-600/80 mt-0.5">{errorMsg}</div>
              </div>
              <button onClick={() => setPageState("idle")} className="text-slate-400 hover:text-slate-700 transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Idle hint */}
          {pageState === "idle" && (
            <div className="rounded-xl bg-slate-50 border border-slate-200 p-5">
              <SectionLabel icon={<ArrowRight className="w-3.5 h-3.5" />} text="How it works" />
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {[
                  { step: "01", text: "Paste the job description text above" },
                  { step: "02", text: "The NLP pipeline extracts skills, role level, and requirements" },
                  { step: "03", text: "Run skill-gap analysis to compare with your resume" },
                ].map((s) => (
                  <div key={s.step} className="flex items-start gap-3">
                    <span className="text-xs font-bold text-slate-500 font-mono mt-0.5">{s.step}</span>
                    <p className="text-xs text-slate-500 leading-relaxed">{s.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Navigation back to resume */}
          <div className="flex items-center justify-between text-xs text-slate-400 pt-2">
            <span>Step 2 of 3 in your setup flow</span>
            <div className="flex gap-3">
              <Link href="/resume" className="hover:text-slate-700 transition-colors flex items-center gap-1">
                ← Resume
              </Link>
              <Link href="/matching" className="hover:text-slate-700 transition-colors flex items-center gap-1">
                Skill-Gap Analysis →
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}