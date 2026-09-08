"use client";

import { useAuth } from "@/contexts/AuthContext";
import React, { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertTriangle,
  X,
  ChevronRight,
  Mail,
  Phone,
  Link2,
  GitBranch,
  GraduationCap,
  Briefcase,
  FolderGit2,
  Award,
  Code2,
  Layers,
  Cpu,
  Database,
  Cloud,
  Sparkles,
  RefreshCw,
  MapPin,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";

// ─── Types ────────────────────────────────────────────────────────────────────

interface ContactInfo {
  email?: string | null;
  phone?: string | null;
  linkedin?: string | null;
  github?: string | null;
  location?: string | null;
}

interface EducationItem {
  degree: string;
  institution?: string | null;
  year?: string | null;
  field_of_study?: string | null;
}

interface ExperienceItem {
  title: string;
  company?: string | null;
  duration?: string | null;
  description?: string | null;
  skills_used: string[];
}

interface ProjectItem {
  name: string;
  description?: string | null;
  technologies: string[];
  url?: string | null;
}

interface CandidateProfile {
  name: string;
  contact: ContactInfo;
  summary?: string | null;
  skills: string[];
  programming_languages: string[];
  frameworks: string[];
  tools: string[];
  databases: string[];
  cloud_devops: string[];
  education: EducationItem[];
  experience: ExperienceItem[];
  projects: ProjectItem[];
  certifications: string[];
  achievements: string[];
}

interface ResumeUploadResponse {
  resume_id: number;
  filename: string;
  profile: CandidateProfile;
}

type UploadState = "idle" | "dragging" | "uploading" | "parsing" | "success" | "error";

const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".doc", ".txt", ".md"];
const MAX_SIZE_BYTES = 10 * 1024 * 1024;
const RESUME_ID_KEY = "ai_coach_resume_id";

// ─── Sub-Components ──────────────────────────────────────────────────────────

function SkillBadges({
  skills,
  variant = "default",
}: {
  skills: string[];
  variant?: "default" | "info" | "success" | "purple" | "warning";
}) {
  if (!skills.length) return <span className="text-xs text-slate-400 italic">None detected</span>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {skills.map((s) => (
        <Badge key={s} variant={variant} size="sm">
          {s}
        </Badge>
      ))}
    </div>
  );
}

// ─── Upload Zone ──────────────────────────────────────────────────────────────

function UploadZone({
  state,
  onFile,
  onDragOver,
  onDragLeave,
  onDrop,
  inputRef,
}: {
  state: UploadState;
  onFile: (file: File) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: () => void;
  onDrop: (e: React.DragEvent) => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
}) {
  const isActive = state === "dragging";
  const isLoading = state === "uploading" || state === "parsing";

  return (
    <div
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      onClick={() => !isLoading && inputRef.current?.click()}
      className={[
        "relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-all duration-150",
        isActive
          ? "border-blue-500 bg-blue-50/50"
          : "border-slate-300 bg-white hover:border-slate-400 hover:bg-slate-50/60 shadow-sm",
        isLoading ? "pointer-events-none opacity-70" : "",
      ].join(" ")}
    >
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept={ACCEPTED_EXTENSIONS.join(",")}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
          e.target.value = "";
        }}
      />

      {isLoading ? (
        <>
          <div className="w-10 h-10 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center">
            <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-800">
              {state === "uploading" ? "Uploading resume..." : "Parsing with NLP pipeline..."}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              {state === "parsing"
                ? "Extracting skills, experience & education profile"
                : "Transferring file to local backend"}
            </div>
          </div>
        </>
      ) : (
        <>
          <div
            className={[
              "w-10 h-10 rounded-lg border flex items-center justify-center transition-colors",
              isActive ? "bg-blue-100 border-blue-300" : "bg-slate-100 border-slate-200",
            ].join(" ")}
          >
            <Upload
              className={[
                "w-5 h-5 transition-colors",
                isActive ? "text-blue-600" : "text-slate-600",
              ].join(" ")}
            />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-800">
              {isActive ? "Release file to upload" : "Upload your resume"}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              Drag & drop or click to browse &middot; PDF, DOCX, TXT up to 10MB
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ─── Compact Candidate Profile View ──────────────────────────────────────────

function CandidateProfileView({
  data,
  filename,
  onReset,
}: {
  data: ResumeUploadResponse;
  filename: string;
  onReset: () => void;
}) {
  const p = data.profile;
  const initials =
    p.name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2) || "CA";

  const hasExperience = p.experience.length > 0;
  const hasEducation = p.education.length > 0;
  const hasProjects = p.projects.length > 0;
  const hasCerts = p.certifications.length > 0;
  const hasAchievements = p.achievements.length > 0;

  return (
    <div className="space-y-4">
      {/* 1. Status Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 px-3.5 py-2.5 rounded-lg bg-emerald-50/70 border border-emerald-200/80 text-xs">
        <div className="flex items-center gap-2 text-slate-700 min-w-0">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span className="font-semibold text-emerald-900">Parsed Successfully:</span>
          <span className="font-mono text-slate-600 truncate max-w-xs">{filename}</span>
          <span className="text-slate-400">&middot;</span>
          <span className="text-slate-500 font-medium">Resume #{data.resume_id}</span>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-slate-500 shrink-0">
          <span className="font-semibold text-slate-700">{p.skills.length}</span> skills
          <span>&middot;</span>
          <span className="font-semibold text-slate-700">{p.experience.length}</span> roles
          <span>&middot;</span>
          <span className="font-semibold text-slate-700">{p.projects.length}</span> projects
          <Button
            variant="outline"
            size="sm"
            onClick={onReset}
            className="h-6 text-[11px] px-2 ml-1 text-slate-600 hover:text-slate-900 border-emerald-300 hover:bg-emerald-100/50"
          >
            <RefreshCw className="w-2.5 h-2.5 mr-1" />
            Upload New
          </Button>
        </div>
      </div>

      {/* 2. Candidate Information Card */}
      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white shrink-0 shadow-sm">
              {initials}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-900 leading-tight">{p.name}</h2>
                <Badge variant="success" size="sm">
                  Active
                </Badge>
              </div>
              {p.summary ? (
                <p className="text-xs text-slate-600 mt-1 leading-relaxed max-w-3xl line-clamp-2">
                  {p.summary}
                </p>
              ) : (
                <p className="text-xs text-slate-400 mt-0.5">Parsed candidate profile</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1.5 self-start shrink-0">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
              {p.skills.length} Detected Skills
            </span>
          </div>
        </div>

        {/* Contact Strip */}
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 pt-3 mt-3 border-t border-slate-100 text-xs text-slate-600">
          {p.contact.email && (
            <a
              href={`mailto:${p.contact.email}`}
              className="flex items-center gap-1.5 hover:text-blue-600 transition-colors"
            >
              <Mail className="w-3.5 h-3.5 text-slate-400" />
              <span>{p.contact.email}</span>
            </a>
          )}
          {p.contact.phone && (
            <span className="flex items-center gap-1.5 text-slate-600">
              <Phone className="w-3.5 h-3.5 text-slate-400" />
              <span>{p.contact.phone}</span>
            </span>
          )}
          {p.contact.location && (
            <span className="flex items-center gap-1.5 text-slate-600">
              <MapPin className="w-3.5 h-3.5 text-slate-400" />
              <span>{p.contact.location}</span>
            </span>
          )}
          {p.contact.linkedin && (
            <a
              href={p.contact.linkedin}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 hover:text-blue-600 transition-colors"
            >
              <Link2 className="w-3.5 h-3.5 text-slate-400" />
              <span>LinkedIn</span>
            </a>
          )}
          {p.contact.github && (
            <a
              href={p.contact.github}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 hover:text-blue-600 transition-colors"
            >
              <GitBranch className="w-3.5 h-3.5 text-slate-400" />
              <span>GitHub</span>
            </a>
          )}
          {!p.contact.email &&
            !p.contact.phone &&
            !p.contact.linkedin &&
            !p.contact.github && (
              <span className="text-slate-400 italic">No contact details detected in resume</span>
            )}
        </div>
      </div>

      {/* 3. Key Skills Card (Unified, Compact, Information-Dense) */}
      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
        <div className="flex items-center justify-between pb-2.5 mb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4 text-blue-600" />
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
              Key Skills & Competencies
            </h3>
          </div>
          <span className="text-[11px] font-medium text-slate-400">
            {p.skills.length} Total Extracted
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
          {/* Programming Languages */}
          {p.programming_languages.length > 0 && (
            <div className="p-2.5 rounded-md bg-slate-50/80 border border-slate-100">
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Code2 className="w-3 h-3 text-blue-600" /> Languages
              </div>
              <SkillBadges skills={p.programming_languages} variant="info" />
            </div>
          )}

          {/* Frameworks & Libraries */}
          {p.frameworks.length > 0 && (
            <div className="p-2.5 rounded-md bg-slate-50/80 border border-slate-100">
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Layers className="w-3 h-3 text-purple-600" /> Frameworks & Libraries
              </div>
              <SkillBadges skills={p.frameworks} variant="purple" />
            </div>
          )}

          {/* Tools & Platforms */}
          {p.tools.length > 0 && (
            <div className="p-2.5 rounded-md bg-slate-50/80 border border-slate-100">
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Cpu className="w-3 h-3 text-slate-600" /> Tools & Platforms
              </div>
              <SkillBadges skills={p.tools} />
            </div>
          )}

          {/* Databases */}
          {p.databases.length > 0 && (
            <div className="p-2.5 rounded-md bg-slate-50/80 border border-slate-100">
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Database className="w-3 h-3 text-emerald-600" /> Databases
              </div>
              <SkillBadges skills={p.databases} variant="success" />
            </div>
          )}

          {/* Cloud & DevOps */}
          {p.cloud_devops.length > 0 && (
            <div className="p-2.5 rounded-md bg-slate-50/80 border border-slate-100">
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Cloud className="w-3 h-3 text-amber-600" /> Cloud & DevOps
              </div>
              <SkillBadges skills={p.cloud_devops} variant="warning" />
            </div>
          )}

          {/* All Detected Skills Summary */}
          <div className="p-2.5 rounded-md bg-slate-50/80 border border-slate-100 flex flex-col justify-between">
            <div>
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                <Award className="w-3 h-3 text-blue-600" /> Skill Inventory
              </div>
              <p className="text-[11px] text-slate-500 leading-snug">
                {p.skills.slice(0, 10).join(", ")}
                {p.skills.length > 10 ? ` +${p.skills.length - 10} more` : ""}
              </p>
            </div>
            <div className="text-[10px] text-blue-600 font-semibold mt-1">
              {p.skills.length} indexed for interview matching
            </div>
          </div>
        </div>
      </div>

      {/* 4. Two-Column Layout for Experience, Education, Projects, Achievements */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column (Work Experience & Projects) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Experience */}
          {hasExperience && (
            <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
              <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-emerald-600" />
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                    Work Experience
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">
                  {p.experience.length} {p.experience.length === 1 ? "position" : "positions"}
                </span>
              </div>

              <div className="space-y-3.5 divide-y divide-slate-100">
                {p.experience.map((e, i) => (
                  <div key={i} className={i > 0 ? "pt-3" : ""}>
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="text-sm font-semibold text-slate-900 leading-tight">
                          {e.title}
                        </div>
                        <div className="text-xs text-slate-500 font-medium mt-0.5">
                          {e.company}
                          {e.duration ? ` \u00b7 ${e.duration}` : ""}
                        </div>
                      </div>
                      {e.duration && !e.company && (
                        <Badge variant="default" size="sm">
                          {e.duration}
                        </Badge>
                      )}
                    </div>
                    {e.description && (
                      <p className="text-xs text-slate-600 leading-relaxed mt-1.5 line-clamp-3">
                        {e.description}
                      </p>
                    )}
                    {e.skills_used.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {e.skills_used.slice(0, 6).map((s) => (
                          <span
                            key={s}
                            className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-medium"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Projects */}
          {hasProjects && (
            <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
              <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <FolderGit2 className="w-4 h-4 text-blue-600" />
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                    Projects
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">{p.projects.length} recorded</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {p.projects.map((proj, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-md bg-slate-50/70 border border-slate-200/80 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-1 mb-1.5">
                        <span className="text-xs font-bold text-slate-900 leading-snug">
                          {proj.name}
                        </span>
                        {proj.url && (
                          <a
                            href={proj.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-blue-600 hover:text-blue-700 shrink-0 mt-0.5"
                          >
                            <Link2 className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                      {proj.description && (
                        <p className="text-[11px] text-slate-600 leading-relaxed line-clamp-4 mb-2">
                          {proj.description}
                        </p>
                      )}
                    </div>
                    {proj.technologies.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {proj.technologies.map((t) => (
                          <span
                            key={t}
                            className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 font-medium"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column (Education & Achievements/Certs) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Education */}
          {hasEducation && (
            <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
              <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <GraduationCap className="w-4 h-4 text-blue-600" />
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                    Education
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">
                  {p.education.length} {p.education.length === 1 ? "entry" : "entries"}
                </span>
              </div>

              <div className="space-y-2.5">
                {p.education.map((e, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-md bg-slate-50/70 border border-slate-200/80 flex items-start gap-2.5"
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                    <div>
                      <div className="text-xs font-bold text-slate-900">{e.degree}</div>
                      <div className="text-[11px] text-slate-600 mt-0.5">
                        {e.institution}
                        {e.field_of_study ? ` \u2014 ${e.field_of_study}` : ""}
                        {e.year ? ` \u00b7 ${e.year}` : ""}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Certifications & Achievements in a compact combined card */}
          {(hasCerts || hasAchievements) && (
            <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm space-y-3">
              {hasCerts && (
                <div>
                  <div className="flex items-center gap-1.5 pb-1.5 mb-2 border-b border-slate-100">
                    <Award className="w-3.5 h-3.5 text-amber-600" />
                    <h4 className="text-[11px] font-bold text-slate-700 uppercase tracking-wide">
                      Certifications
                    </h4>
                  </div>
                  <ul className="space-y-1 text-xs text-slate-600">
                    {p.certifications.map((c, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                        <span className="truncate">{c}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {hasAchievements && (
                <div>
                  <div className="flex items-center gap-1.5 pb-1.5 mb-2 border-b border-slate-100">
                    <Award className="w-3.5 h-3.5 text-emerald-600" />
                    <h4 className="text-[11px] font-bold text-slate-700 uppercase tracking-wide">
                      Achievements
                    </h4>
                  </div>
                  <ul className="space-y-1 text-xs text-slate-600">
                    {p.achievements.map((a, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                        <span className="truncate">{a}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 5. Bottom CTA (Compact & Streamlined) */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-lg bg-white border border-slate-200 px-4 py-2.5 shadow-sm">
        <div className="flex items-center gap-2.5 text-xs text-slate-600">
          <Sparkles className="w-4 h-4 text-blue-600 shrink-0" />
          <span>
            Profile active and ready. Pair with a target Job Description to analyze match score and skill gaps.
          </span>
        </div>
        <Link href="/jobs" className="shrink-0">
          <Button variant="primary" size="sm" className="h-7 text-xs px-3">
            Add Job Description
            <ChevronRight className="w-3.5 h-3.5 ml-1" />
          </Button>
        </Link>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function ResumePage() {
  const { userId: USER_ID } = useAuth();
  const effectiveUserId = USER_ID ?? 1;

  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [result, setResult] = useState<ResumeUploadResponse | null>(null);
  const [uploadedFilename, setUploadedFilename] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // On mount: try to reload last uploaded resume from localStorage
  useEffect(() => {
    const savedId = localStorage.getItem(RESUME_ID_KEY);
    if (savedId && !result) {
      fetch(`/api/py/resumes/${savedId}`)
        .then((r) => (r.ok ? r.json() : null))
        .then((data: ResumeUploadResponse | null) => {
          if (data) {
            setResult(data);
            setUploadedFilename(data.filename);
            setUploadState("success");
          }
        })
        .catch(() => null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const validateFile = (file: File): string | null => {
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      return `Unsupported file type: ${ext}. Use PDF, DOCX, DOC, TXT, or MD.`;
    }
    if (file.size > MAX_SIZE_BYTES) {
      return `File is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum is 10 MB.`;
    }
    if (file.size === 0) {
      return "File is empty.";
    }
    return null;
  };

  const processFile = useCallback(
    async (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        setErrorMsg(validationError);
        setUploadState("error");
        return;
      }

      setUploadedFilename(file.name);
      setErrorMsg("");
      setUploadState("uploading");

      const formData = new FormData();
      formData.append("file", file);
      formData.append("user_id", String(effectiveUserId));

      try {
        setUploadState("parsing");
        const res = await fetch("/api/py/resumes/upload", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "Upload failed." }));
          throw new Error(err.detail || `Error ${res.status}`);
        }

        const data: ResumeUploadResponse = await res.json();
        localStorage.setItem(RESUME_ID_KEY, String(data.resume_id));
        setResult(data);
        setUploadState("success");
      } catch (e: unknown) {
        setErrorMsg(e instanceof Error ? e.message : "Upload failed. Please try again.");
        setUploadState("error");
      }
    },
    [effectiveUserId]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setUploadState("dragging");
  }, []);

  const handleDragLeave = useCallback(() => {
    setUploadState("idle");
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files?.[0];
      if (file) processFile(file);
      else setUploadState("idle");
    },
    [processFile]
  );

  const handleReset = () => {
    setResult(null);
    setUploadState("idle");
    setErrorMsg("");
    setUploadedFilename("");
    localStorage.removeItem(RESUME_ID_KEY);
  };

  return (
    <div className="space-y-4 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-3 border-b border-slate-200">
        <div>
          <h1 className="text-lg font-bold tracking-tight text-slate-900">Resume Intelligence</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Extract skills, experience, and build your candidate profile for adaptive interview coaching
          </p>
        </div>
        {uploadState === "success" && (
          <Badge variant="success" size="sm">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            Profile Active
          </Badge>
        )}
      </div>

      {/* Content */}
      {uploadState === "success" && result ? (
        <CandidateProfileView data={result} filename={uploadedFilename} onReset={handleReset} />
      ) : (
        <div className="max-w-xl mx-auto space-y-3 pt-4">
          <UploadZone
            state={uploadState}
            onFile={processFile}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            inputRef={inputRef}
          />

          {/* Error state */}
          {uploadState === "error" && (
            <div className="flex items-start gap-2.5 rounded-lg bg-red-50 border border-red-200 px-3.5 py-2.5">
              <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold text-red-700">Upload failed</div>
                <div className="text-xs text-red-600/80 mt-0.5">{errorMsg}</div>
              </div>
              <button
                onClick={() => setUploadState("idle")}
                className="text-slate-400 hover:text-slate-700 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Empty state hint */}
          {uploadState === "idle" && (
            <EmptyState
              icon={<FileText className="w-5 h-5 text-slate-500" />}
              title="No resume uploaded yet"
              description="Upload your resume to extract competencies, experience, and projects. All parsing runs securely via the local NLP pipeline."
              action={
                <div className="flex gap-2 justify-center">
                  <Link href="/jobs">
                    <Button variant="ghost" size="sm" className="h-7 text-xs">
                      Skip to Job Description
                    </Button>
                  </Link>
                </div>
              }
            />
          )}
        </div>
      )}
    </div>
  );
}
