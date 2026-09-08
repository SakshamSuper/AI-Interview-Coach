"use client";

import { useAuth } from "@/contexts/AuthContext";

import React, { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import {
  Play, Send, ChevronRight, FileText, Briefcase,
  CheckCircle2, XCircle, RefreshCw, AlertTriangle,
  Layers, Trophy, TrendingUp, BookOpen, ArrowLeft,
  Mic, MicOff, Volume2, VolumeX, Target, Sparkles,
  Edit3, SkipForward,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";

// ─── API Types — mirrors backend Pydantic schemas exactly ─────────────────────

interface InterviewQuestion {
  question: string;
  topic: string;
  difficulty: "Easy" | "Medium" | "Hard";
  question_type: string;
  reason: string | null;
  expected_concepts: string[];
  source_context: string | null;
}

interface AnswerEvaluation {
  technical_accuracy: number;
  relevance: number;
  completeness: number;
  clarity: number;
  communication: number;
  overall_score: number;
  strengths: string[];
  weaknesses: string[];
  missing_concepts: string[];
  feedback: string;
  recommended_topics: string[];
  next_difficulty: string;
}

interface RecommendationOutput {
  overall_summary: string;
  strong_areas: string[];
  weak_areas: string[];
  learning_priorities: string[];
  practice_questions: string[];
}

interface InterviewStartResponse {
  session_id: number;
  target_role: string;
  interview_type: string;
  difficulty: string;
  total_questions: number;
  question_number: number;
  question: InterviewQuestion;
}

interface AnswerSubmitResponse {
  session_id: number;
  question_id: number;
  evaluation: AnswerEvaluation;
  is_last_question: boolean;
}

interface NextQuestionResponse {
  session_id: number;
  is_completed: boolean;
  question_number: number | null;
  total_questions: number;
  current_difficulty: string;
  question: InterviewQuestion | null;
  recommendations: RecommendationOutput | null;
  overall_score: number | null;
  readiness_label: string | null;
  readiness_score: number | null;
}

// ─── Config ───────────────────────────────────────────────────────────────────

// USER_ID is now derived from the authenticated session — see useAuth() below
const RESUME_ID_KEY = "ai_coach_resume_id";
const JD_ID_KEY = "ai_coach_jd_id";

type PageStage =
  | "setup"
  | "starting"
  | "question"
  | "evaluating"
  | "evaluation_shown"
  | "loading_next"
  | "completed"
  | "error"
  | "no_resume"
  | "no_jd";

type VoiceRecordState = "idle" | "recording" | "transcribing" | "done" | "error";
type TtsState = "idle" | "loading" | "playing" | "error";
type InputMode = "text" | "voice";

// ─── API layer ────────────────────────────────────────────────────────────────

async function startInterview(
  resumeId: number | null,
  jdId: number | null,
  difficulty: string,
  totalQuestions: number,
  interviewType: string,
  userId: number | null
): Promise<InterviewStartResponse> {
  const body: Record<string, unknown> = {
    user_id: userId ?? 1,
    interview_type: interviewType,
    difficulty,
    total_questions: totalQuestions,
  };
  if (resumeId) body.resume_id = resumeId;
  if (jdId) body.jd_id = jdId;

  const res = await fetch("/api/py/interviews/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to start interview." }));
    throw new Error(typeof err.detail === "string" ? err.detail : "Failed to start interview.");
  }
  return res.json();
}

async function submitAnswer(sessionId: number, answerText: string): Promise<AnswerSubmitResponse> {
  const res = await fetch(`/api/py/interviews/${sessionId}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answer_text: answerText }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to submit answer." }));
    throw new Error(typeof err.detail === "string" ? err.detail : "Failed to submit answer.");
  }
  return res.json();
}

async function requestNextQuestion(sessionId: number): Promise<NextQuestionResponse> {
  const res = await fetch(`/api/py/interviews/${sessionId}/next`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to get next question." }));
    throw new Error(typeof err.detail === "string" ? err.detail : "Failed to get next question.");
  }
  return res.json();
}

// ─── Voice API helpers ────────────────────────────────────────────────────────

async function synthesizeQuestion(text: string): Promise<string> {
  // Returns a browser-playable URL via the FastAPI /voice/audio/{filename} endpoint
  const res = await fetch("/api/py/voice/speak", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error("TTS synthesis failed.");
  const data = await res.json();
  // audio_url is a relative path like /voice/audio/question_speech_12345.mp3
  // proxy it through the Next.js /api/py prefix
  return "/api/py" + data.audio_url;
}

async function transcribeAudio(blob: Blob): Promise<string> {
  const formData = new FormData();
  const ext = blob.type.includes("ogg") ? "ogg" : blob.type.includes("mp4") ? "mp4" : "webm";
  formData.append("file", blob, `answer.${ext}`);
  const res = await fetch("/api/py/voice/transcribe", {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Transcription failed." }));
    throw new Error(typeof err.detail === "string" ? err.detail : "Transcription failed.");
  }
  const data = await res.json();
  return data.transcript;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function difficultyVariant(d: string): "success" | "warning" | "danger" | "default" {
  if (d === "Easy") return "success";
  if (d === "Medium") return "warning";
  if (d === "Hard") return "danger";
  return "default";
}

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

function readinessVariant(label: string): "success" | "warning" | "danger" | "default" {
  const l = label.toLowerCase();
  if (l.includes("ready")) return "success";
  if (l.includes("borderline") || l.includes("almost")) return "warning";
  if (l.includes("needs")) return "danger";
  return "default";
}

// ─── TTS Player ───────────────────────────────────────────────────────────────

function TtsButton({ questionText }: { questionText: string }) {
  const [state, setState] = useState<TtsState>("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Reset when question changes
  useEffect(() => {
    setState("idle");
    setErrorMsg("");
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
  }, [questionText]);

  const handleListen = async () => {
    if (state === "playing") {
      audioRef.current?.pause();
      setState("idle");
      return;
    }
    setState("loading");
    setErrorMsg("");
    try {
      const url = await synthesizeQuestion(questionText);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => setState("idle");
      audio.onerror = () => {
        setState("error");
        setErrorMsg("Audio playback failed — use text mode.");
      };
      await audio.play();
      setState("playing");
    } catch (e) {
      setState("error");
      setErrorMsg(e instanceof Error ? e.message : "TTS unavailable.");
    }
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={handleListen}
        disabled={state === "loading"}
        className={[
          "flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border font-medium transition-colors",
          state === "playing"
            ? "bg-blue-600/20 border-blue-500/50 text-blue-500"
            : state === "error"
            ? "bg-red-50 border-red-200 text-red-600"
            : "bg-slate-50 border-slate-300 text-slate-500 hover:text-slate-800 hover:border-slate-300",
        ].join(" ")}
      >
        {state === "loading" ? (
          <RefreshCw className="w-3 h-3 animate-spin" />
        ) : state === "playing" ? (
          <VolumeX className="w-3 h-3" />
        ) : (
          <Volume2 className="w-3 h-3" />
        )}
        {state === "loading" ? "Synthesizing..." : state === "playing" ? "Stop" : "Listen to Question"}
      </button>
      {state === "error" && (
        <span className="text-[10px] text-red-600">{errorMsg}</span>
      )}
    </div>
  );
}

// ─── Voice Recorder Panel ─────────────────────────────────────────────────────

function VoiceRecorderPanel({
  onTranscriptReady,
}: {
  onTranscriptReady: (text: string) => void;
}) {
  const [recState, setRecState] = useState<VoiceRecordState>("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [transcript, setTranscript] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [sttInfo, setSttInfo] = useState<{ model: string; device: string } | null>(null);
  const [recordingSecs, setRecordingSecs] = useState(0);
  const mediaRecRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Pre-flight: fetch local Whisper status for display only
  useEffect(() => {
    fetch("/api/py/voice/status")
      .then((r) => r.json())
      .then((d) => setSttInfo({ model: d.model ?? "small", device: d.device ?? "cpu" }))
      .catch(() => null);
  }, []);

  // Recording timer
  useEffect(() => {
    if (recState === "recording") {
      setRecordingSecs(0);
      timerRef.current = setInterval(
        () => setRecordingSecs((s) => s + 1),
        1000
      );
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [recState]);

  const startRecording = async () => {
    // Guard: MediaRecorder not supported (e.g., old browser)
    if (typeof MediaRecorder === "undefined") {
      setRecState("error");
      setErrorMsg(
        "Your browser does not support audio recording. Try Chrome, Firefox, or Edge."
      );
      return;
    }

    setErrorMsg("");
    setTranscript("");
    setIsEditing(false);
    chunksRef.current = [];

    // Request microphone
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      setRecState("error");
      const msg =
        err instanceof Error && err.name === "NotAllowedError"
          ? "Microphone permission denied. Click the browser's camera/mic icon to allow access, then retry."
          : err instanceof Error && err.name === "NotFoundError"
          ? "No microphone found. Connect a microphone and retry."
          : `Microphone error: ${err instanceof Error ? err.message : String(err)}`;
      setErrorMsg(msg);
      return;
    }

    // Pick best supported MIME type
    const mimeType =
      [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/ogg;codecs=opus",
        "audio/mp4",
      ].find((t) => MediaRecorder.isTypeSupported(t)) ?? "";

    try {
      const rec = new MediaRecorder(
        stream,
        mimeType ? { mimeType } : undefined
      );
      mediaRecRef.current = rec;

      rec.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      rec.onerror = () => {
        stream.getTracks().forEach((t) => t.stop());
        setRecState("error");
        setErrorMsg("A recording error occurred. Please retry.");
      };

      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());

        const blob = new Blob(chunksRef.current, {
          type: mimeType || "audio/webm",
        });

        // Guard: empty blob — no audio was captured
        if (blob.size === 0) {
          setRecState("error");
          setErrorMsg(
            "No audio was captured (empty recording). " +
              "Ensure your microphone is working and try again."
          );
          return;
        }

        console.log(
          `[Voice] Blob ready: ${blob.size} bytes, type: ${blob.type}, ` +
            `chunks: ${chunksRef.current.length}`
        );

        setRecState("transcribing");
        try {
          const text = await transcribeAudio(blob);
          setTranscript(text);
          setRecState("done");
          onTranscriptReady(text);
        } catch (e) {
          setRecState("error");
          setErrorMsg(
            e instanceof Error ? e.message : "Transcription failed. Retry."
          );
        }
      };

      rec.start(250); // collect chunks every 250 ms
      setRecState("recording");
    } catch (e) {
      stream.getTracks().forEach((t) => t.stop());
      setRecState("error");
      setErrorMsg(
        e instanceof Error ? e.message : "Could not start recording."
      );
    }
  };

  const stopRecording = () => {
    mediaRecRef.current?.stop();
  };

  const resetVoice = () => {
    // Stop any in-progress recording
    if (mediaRecRef.current && recState === "recording") {
      mediaRecRef.current.stop();
    }
    setRecState("idle");
    setTranscript("");
    setErrorMsg("");
    setIsEditing(false);
    chunksRef.current = [];
    onTranscriptReady(""); // clear answer field too
  };

  const fmtTime = (s: number) =>
    `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;


  return (
    <div className="space-y-3">
      {/* Local Whisper info badge */}
      {sttInfo && (
        <div className="flex items-center gap-2 rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 flex-shrink-0" />
          <span className="text-xs text-emerald-800">
            <span className="font-semibold">Local Whisper active</span>
            {" — "}model: <code className="font-mono bg-emerald-100 px-1 rounded">{sttInfo.model}</code>
            {", "}device: <code className="font-mono bg-emerald-100 px-1 rounded">{sttInfo.device}</code>
            {". No data leaves your machine."}
          </span>
        </div>
      )}

      {/* Record control */}
      <div className="flex items-center gap-3 flex-wrap">
        {recState === "idle" && (
          <button
            onClick={startRecording}
            className="flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-red-600/80 hover:bg-red-600 border border-red-500 text-white font-medium transition-colors"
          >
            <Mic className="w-4 h-4" />
            Start Recording
          </button>
        )}
        {recState === "recording" && (
          <>
            <button
              onClick={stopRecording}
              className="flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-red-700 border border-red-600 text-white font-medium transition-colors"
            >
              <MicOff className="w-4 h-4" />
              Stop Recording
            </button>
            <span className="flex items-center gap-1.5 text-xs text-red-600">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              Recording&nbsp;
              <span className="font-mono font-bold tabular-nums">
                {fmtTime(recordingSecs)}
              </span>
            </span>
          </>
        )}
        {recState === "transcribing" && (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
            Transcribing audio…
          </div>
        )}
        {(recState === "done" || recState === "error") && (
          <button
            onClick={resetVoice}
            className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-300 text-slate-500 hover:text-slate-800 font-medium transition-colors"
          >
            <Mic className="w-3 h-3" />
            Re-record
          </button>
        )}
      </div>

      {/* Error */}
      {recState === "error" && errorMsg && (
        <div className="flex items-start gap-2 rounded-lg bg-red-50 border border-red-200 p-3">
          <XCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
          <span className="text-xs text-red-700 leading-relaxed">{errorMsg}</span>
        </div>
      )}

      {/* Transcript preview + edit */}
      {recState === "done" && transcript && (
        <div className="rounded-lg bg-slate-50 border border-slate-300 p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wide">
              Transcript — review before submitting
            </span>
            <button
              onClick={() => setIsEditing((v) => !v)}
              className="flex items-center gap-1 text-[10px] text-blue-600 hover:text-blue-500 transition-colors"
            >
              <Edit3 className="w-3 h-3" />
              {isEditing ? "Done editing" : "Edit"}
            </button>
          </div>
          {isEditing ? (
            <textarea
              value={transcript}
              onChange={(e) => {
                setTranscript(e.target.value);
                onTranscriptReady(e.target.value);
              }}
              rows={4}
              className="w-full rounded bg-white border border-slate-300 text-sm text-slate-800 px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none leading-relaxed"
            />
          ) : (
            <p className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
              {transcript}
            </p>
          )}
          <p className="text-[10px] text-slate-400">
            Edit the transcript if needed, then submit using the button below.
          </p>
        </div>
      )}
    </div>
  );
}

// ─── Setup Screen ─────────────────────────────────────────────────────────────

function SetupScreen({
  resumeId,
  jdId,
  onStart,
  isStarting,
}: {
  resumeId: number | null;
  jdId: number | null;
  onStart: (difficulty: string, total: number, type: string) => void;
  isStarting: boolean;
}) {
  const [difficulty, setDifficulty] = useState("Medium");
  const [total, setTotal] = useState(5);
  const [interviewType, setInterviewType] = useState("Technical");

  const difficulties = ["Easy", "Medium", "Hard"];
  const types = ["Technical", "Behavioral", "Mixed"];
  const totals = [3, 5, 7, 10];

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Context */}
      <div className="rounded-xl bg-slate-50 border border-slate-300/50 p-5">
        <div className="flex items-center gap-2 mb-3">
          <Target className="w-4 h-4 text-blue-600" />
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">Session Context</span>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="flex items-center gap-2">
            <FileText className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-500">Resume:</span>
            {resumeId ? (
              <Badge variant="success" size="sm">ID {resumeId}</Badge>
            ) : (
              <Badge variant="danger" size="sm">Missing</Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Briefcase className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-500">Job Description:</span>
            {jdId ? (
              <Badge variant="success" size="sm">ID {jdId}</Badge>
            ) : (
              <Badge variant="danger" size="sm">Missing</Badge>
            )}
          </div>
        </div>
        <p className="text-xs text-slate-400 mt-3 leading-relaxed">
          The interview will be automatically grounded using your resume profile and target job description.
          Questions will be generated by the LangGraph question agent using RAG-retrieved knowledge base context.
        </p>
      </div>

      {/* Configuration */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Interview Configuration</CardTitle>
            <p className="text-xs text-slate-500 mt-0.5">Configure your adaptive interview session</p>
          </div>
          <Sparkles className="w-4 h-4 text-blue-600" />
        </CardHeader>
        <CardContent className="space-y-5">
          {/* Interview Type */}
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wide block mb-2">
              Interview Type
            </label>
            <div className="flex gap-2 flex-wrap">
              {types.map((t) => (
                <button
                  key={t}
                  onClick={() => setInterviewType(t)}
                  className={[
                    "text-xs px-4 py-2 rounded-lg border font-medium transition-colors",
                    interviewType === t
                      ? "bg-blue-600 border-blue-500 text-white"
                      : "bg-slate-50 border-slate-300 text-slate-500 hover:text-slate-800",
                  ].join(" ")}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Difficulty */}
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wide block mb-2">
              Starting Difficulty
            </label>
            <div className="flex gap-2">
              {difficulties.map((d) => (
                <button
                  key={d}
                  onClick={() => setDifficulty(d)}
                  className={[
                    "text-xs px-4 py-2 rounded-lg border font-medium transition-colors",
                    difficulty === d
                      ? "bg-blue-600 border-blue-500 text-white"
                      : "bg-slate-50 border-slate-300 text-slate-500 hover:text-slate-800",
                  ].join(" ")}
                >
                  {d}
                </button>
              ))}
            </div>
            <p className="text-[10px] text-slate-400 mt-1.5">
              The backend will adapt difficulty based on your performance.
            </p>
          </div>

          {/* Question Count */}
          <div>
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wide block mb-2">
              Number of Questions
            </label>
            <div className="flex gap-2">
              {totals.map((n) => (
                <button
                  key={n}
                  onClick={() => setTotal(n)}
                  className={[
                    "text-xs px-4 py-2 rounded-lg border font-medium transition-colors",
                    total === n
                      ? "bg-blue-600 border-blue-500 text-white"
                      : "bg-slate-50 border-slate-300 text-slate-500 hover:text-slate-800",
                  ].join(" ")}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          {/* Start */}
          <div className="pt-2 border-t border-slate-200">
            <Button
              variant="primary"
              size="md"
              onClick={() => onStart(difficulty, total, interviewType)}
              isLoading={isStarting}
              disabled={!resumeId && !jdId}
              className="w-full"
            >
              <Play className="w-4 h-4" />
              {isStarting ? "Initializing Session..." : "Begin Adaptive Interview"}
            </Button>
            {!resumeId && !jdId && (
              <p className="text-xs text-amber-600 mt-2 text-center">
                Upload a resume or add a job description first for best results.
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ─── Progress Bar Row ─────────────────────────────────────────────────────────

function InterviewProgress({
  current,
  total,
  difficulty,
  topic,
}: {
  current: number;
  total: number;
  difficulty: string;
  topic: string;
}) {
  const pct = Math.round(((current - 1) / total) * 100);
  return (
    <div className="rounded-xl bg-slate-50 border border-slate-200 p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <span className="text-xs font-bold text-slate-500">
            Question {current} of {total}
          </span>
          <Badge variant={difficultyVariant(difficulty)} size="sm">{difficulty}</Badge>
          <span className="text-xs text-slate-400">{topic}</span>
        </div>
        <span className="text-xs font-mono text-slate-400">{pct}% complete</span>
      </div>
      <div className="h-1 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded-full transition-all duration-700"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ─── Question Block ───────────────────────────────────────────────────────────

function QuestionBlock({ question }: { question: InterviewQuestion }) {
  return (
    <div className="space-y-3">
      <div className="flex items-start gap-2">
        <BookOpen className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
        <p className="text-base font-semibold text-slate-900 leading-relaxed">
          {question.question}
        </p>
      </div>
      {question.reason && (
        <p className="text-xs text-slate-400 pl-6 leading-relaxed italic">{question.reason}</p>
      )}
      {question.expected_concepts.length > 0 && (
        <div className="pl-6 flex flex-wrap gap-1.5">
          {question.expected_concepts.map((c) => (
            <span key={c} className="text-[10px] text-slate-400 bg-slate-50 border border-slate-300/40 rounded px-2 py-0.5">
              {c}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Evaluation Display ───────────────────────────────────────────────────────

function EvaluationPanel({
  evaluation,
  isLast,
  onNext,
  onComplete,
  isLoading,
}: {
  evaluation: AnswerEvaluation;
  isLast: boolean;
  onNext: () => void;
  onComplete: () => void;
  isLoading: boolean;
}) {
  const dims = [
    { label: "Technical Accuracy", value: evaluation.technical_accuracy },
    { label: "Relevance", value: evaluation.relevance },
    { label: "Completeness", value: evaluation.completeness },
    { label: "Clarity", value: evaluation.clarity },
    { label: "Communication", value: evaluation.communication },
  ];

  return (
    <div className="space-y-5 animate-fadeIn">
      {/* Score header */}
      <div className="rounded-xl bg-slate-50 border border-slate-200 p-5">
        <div className="flex items-center justify-between mb-4">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">Answer Evaluation</span>
          <span className={`text-2xl font-black font-mono ${scoreColor(evaluation.overall_score)}`}>
            {evaluation.overall_score.toFixed(0)}/100
          </span>
        </div>
        <div className="space-y-2.5">
          {dims.map((d) => (
            <ProgressBar
              key={d.label}
              label={d.label}
              value={d.value}
              color={scoreBarColor(d.value)}
              size="sm"
            />
          ))}
        </div>
      </div>

      {/* Feedback */}
      <div className="rounded-xl bg-slate-50 border border-slate-300/50 p-4">
        <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Feedback</p>
        <p className="text-sm text-slate-700 leading-relaxed">{evaluation.feedback}</p>
      </div>

      {/* Strengths / Weaknesses */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {evaluation.strengths.length > 0 && (
          <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3">
            <p className="text-[10px] font-bold text-emerald-600 uppercase tracking-wide mb-1.5">Strengths</p>
            <ul className="space-y-1">
              {evaluation.strengths.map((s) => (
                <li key={s} className="flex items-start gap-1.5 text-xs text-slate-700">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600 flex-shrink-0 mt-0.5" />
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}
        {(evaluation.weaknesses.length > 0 || evaluation.missing_concepts.length > 0) && (
          <div className="rounded-lg bg-amber-50 border border-amber-200 p-3">
            <p className="text-[10px] font-bold text-amber-600 uppercase tracking-wide mb-1.5">Areas to Improve</p>
            <ul className="space-y-1">
              {[...evaluation.weaknesses, ...evaluation.missing_concepts].slice(0, 4).map((w) => (
                <li key={w} className="flex items-start gap-1.5 text-xs text-slate-700">
                  <AlertTriangle className="w-3 h-3 text-amber-600 flex-shrink-0 mt-0.5" />
                  {w}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Adaptive signal */}
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <TrendingUp className="w-3.5 h-3.5" />
        Next question difficulty: <Badge variant={difficultyVariant(evaluation.next_difficulty)} size="sm">{evaluation.next_difficulty}</Badge>
      </div>

      {/* Action */}
      <div className="flex justify-end">
        <Button
          variant="primary"
          size="md"
          onClick={isLast ? onComplete : onNext}
          isLoading={isLoading}
        >
          {isLast ? (
            <><Trophy className="w-4 h-4" />Complete Interview</>
          ) : (
            <><ChevronRight className="w-4 h-4" />Next Question</>
          )}
        </Button>
      </div>
    </div>
  );
}

// ─── Completed Screen ─────────────────────────────────────────────────────────

function CompletedScreen({
  score,
  readinessLabel,
  readinessScore,
  recommendations,
  onRestart,
}: {
  score: number;
  readinessLabel: string;
  readinessScore: number;
  recommendations: RecommendationOutput | null;
  onRestart: () => void;
}) {
  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fadeIn">
      {/* Hero score */}
      <div className="text-center py-8 rounded-xl bg-slate-50 border border-slate-200">
        <div className={`text-5xl font-black font-mono mb-2 ${scoreColor(score)}`}>
          {score.toFixed(0)}
        </div>
        <div className="text-sm text-slate-500 mb-3">Overall Interview Score</div>
        <Badge variant={readinessVariant(readinessLabel)} size="sm">{readinessLabel}</Badge>
        {readinessScore > 0 && (
          <div className="mt-2 text-xs text-slate-400">ML Readiness: {readinessScore.toFixed(1)}%</div>
        )}
      </div>

      {/* Recommendations */}
      {recommendations && (
        <>
          {recommendations.overall_summary && (
            <div className="rounded-xl bg-slate-50 border border-slate-300/50 p-4">
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Session Summary</p>
              <p className="text-sm text-slate-700 leading-relaxed">{recommendations.overall_summary}</p>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {recommendations.strong_areas.length > 0 && (
              <Card>
                <CardContent>
                  <p className="text-[10px] font-bold text-emerald-600 uppercase tracking-wide mb-2">Strong Areas</p>
                  <ul className="space-y-1">
                    {recommendations.strong_areas.map((a) => (
                      <li key={a} className="flex items-center gap-1.5 text-xs text-slate-700">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />{a}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
            {recommendations.weak_areas.length > 0 && (
              <Card>
                <CardContent>
                  <p className="text-[10px] font-bold text-amber-600 uppercase tracking-wide mb-2">Areas to Improve</p>
                  <ul className="space-y-1">
                    {recommendations.weak_areas.map((a) => (
                      <li key={a} className="flex items-center gap-1.5 text-xs text-slate-700">
                        <AlertTriangle className="w-3 h-3 text-amber-600" />{a}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>

          {recommendations.learning_priorities.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Learning Priorities</CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="space-y-2">
                  {recommendations.learning_priorities.map((p, i) => (
                    <li key={p} className="flex items-start gap-3 text-sm text-slate-700">
                      <span className="text-xs font-bold text-blue-600 font-mono mt-0.5 flex-shrink-0">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      {p}
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Actions */}
      <div className="flex gap-3 justify-center pt-2">
        <Link href="/"><Button variant="outline" size="md"><ArrowLeft className="w-4 h-4" />Dashboard</Button></Link>
        <Button variant="primary" size="md" onClick={onRestart}><Play className="w-4 h-4" />New Interview</Button>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function InterviewPage() {
  const { userId: USER_ID } = useAuth();
  const [stage, setStage] = useState<PageStage>("setup");
  const [error, setError] = useState("");
  const [resumeId, setResumeId] = useState<number | null>(null);
  const [jdId, setJdId] = useState<number | null>(null);

  // Session state
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [totalQuestions, setTotalQuestions] = useState(5);
  const [currentQuestionNum, setCurrentQuestionNum] = useState(1);
  const [currentQuestion, setCurrentQuestion] = useState<InterviewQuestion | null>(null);
  const [currentDifficulty, setCurrentDifficulty] = useState("Medium");
  const [answerText, setAnswerText] = useState("");
  const [evaluation, setEvaluation] = useState<AnswerEvaluation | null>(null);
  const [isLastQuestion, setIsLastQuestion] = useState(false);
  const [completedData, setCompletedData] = useState<{
    score: number; readinessLabel: string; readinessScore: number;
    recommendations: RecommendationOutput | null;
  } | null>(null);

  // Voice state
  const [inputMode, setInputMode] = useState<InputMode>("text");
  const [voiceKey, setVoiceKey] = useState(0); // reset VoiceRecorderPanel per question

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load IDs from localStorage
  useEffect(() => {
    const rid = localStorage.getItem(RESUME_ID_KEY);
    const jid = localStorage.getItem(JD_ID_KEY);
    setResumeId(rid ? parseInt(rid, 10) : null);
    setJdId(jid ? parseInt(jid, 10) : null);
  }, []);

  const handleStart = useCallback(async (difficulty: string, total: number, interviewType: string) => {
    setStage("starting");
    setError("");
    try {
      const res = await startInterview(resumeId, jdId, difficulty, total, interviewType, USER_ID);
      setSessionId(res.session_id);
      setTotalQuestions(res.total_questions);
      setCurrentQuestionNum(res.question_number);
      setCurrentQuestion(res.question);
      setCurrentDifficulty(res.difficulty);
      setAnswerText("");
      setEvaluation(null);
      setVoiceKey((k) => k + 1);
      setStage("question");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to start interview.");
      setStage("error");
    }
  }, [resumeId, jdId]);

  const handleSubmitAnswer = useCallback(async () => {
    if (!sessionId || !answerText.trim()) return;
    setStage("evaluating");
    setError("");
    try {
      const res = await submitAnswer(sessionId, answerText.trim());
      setEvaluation(res.evaluation);
      setIsLastQuestion(res.is_last_question);
      setCurrentDifficulty(res.evaluation.next_difficulty);
      setStage("evaluation_shown");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to submit answer.");
      setStage("error");
    }
  }, [sessionId, answerText]);

  const handleNextQuestion = useCallback(async () => {
    if (!sessionId) return;
    setStage("loading_next");
    setError("");
    try {
      const res = await requestNextQuestion(sessionId);
      if (res.is_completed) {
        setCompletedData({
          score: res.overall_score ?? 0,
          readinessLabel: res.readiness_label ?? "Unknown",
          readinessScore: res.readiness_score ?? 0,
          recommendations: res.recommendations ?? null,
        });
        setStage("completed");
      } else if (res.question) {
        setCurrentQuestionNum(res.question_number ?? currentQuestionNum + 1);
        setCurrentQuestion(res.question);
        setCurrentDifficulty(res.current_difficulty);
        setAnswerText("");
        setEvaluation(null);
        setVoiceKey((k) => k + 1);
        setStage("question");
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load next question.");
      setStage("error");
    }
  }, [sessionId, currentQuestionNum]);

  const handleComplete = useCallback(async () => {
    if (!sessionId) return;
    setStage("loading_next");
    try {
      const res = await requestNextQuestion(sessionId);
      setCompletedData({
        score: res.overall_score ?? 0,
        readinessLabel: res.readiness_label ?? "Unknown",
        readinessScore: res.readiness_score ?? 0,
        recommendations: res.recommendations ?? null,
      });
      setStage("completed");
    } catch {
      setCompletedData({
        score: evaluation?.overall_score ?? 0,
        readinessLabel: "Session Complete",
        readinessScore: 0,
        recommendations: null,
      });
      setStage("completed");
    }
  }, [sessionId, evaluation]);

  const handleRestart = () => {
    setStage("setup");
    setSessionId(null);
    setCurrentQuestion(null);
    setEvaluation(null);
    setCompletedData(null);
    setAnswerText("");
    setError("");
    setVoiceKey((k) => k + 1);
  };


  // ── Render ────────────────────────────────────────────────────────────────

  if (stage === "no_resume") {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <FileText className="w-10 h-10 text-slate-400" />
        <h3 className="text-sm font-semibold text-slate-800">Resume required</h3>
        <Link href="/resume"><Button variant="outline" size="sm">Upload Resume</Button></Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-5 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">Adaptive Interview</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {stage === "setup" ? "Configure and begin your AI-powered technical interview" :
             stage === "completed" ? "Interview complete — review your results" :
             sessionId ? `Session #${sessionId}` : ""}
          </p>
        </div>
        {stage !== "setup" && stage !== "completed" && (
          <Button variant="ghost" size="sm" onClick={handleRestart}>
            <XCircle className="w-3.5 h-3.5" />Exit
          </Button>
        )}
      </div>

      {/* ── Setup ── */}
      {(stage === "setup" || stage === "starting") && (
        <SetupScreen
          resumeId={resumeId}
          jdId={jdId}
          onStart={handleStart}
          isStarting={stage === "starting"}
        />
      )}

      {/* ── Error ── */}
      {stage === "error" && (
        <div className="max-w-xl mx-auto">
          <div className="flex items-start gap-3 rounded-xl bg-red-50 border border-red-200 p-4">
            <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-sm font-semibold text-red-600">Interview error</div>
              <div className="text-xs text-red-600/80 mt-1 leading-relaxed">{error}</div>
              <div className="mt-3 flex gap-2">
                <Button variant="outline" size="sm" onClick={handleRestart}>Back to Setup</Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Loading ── */}
      {(stage === "loading_next" || stage === "evaluating") && (
        <div className="flex flex-col items-center justify-center py-20 gap-3">
          <RefreshCw className="w-6 h-6 text-blue-600 animate-spin" />
          <span className="text-sm text-slate-500">
            {stage === "evaluating" ? "Evaluating your answer..." : "Generating next question..."}
          </span>
        </div>
      )}

      {/* ── Active Interview ── */}
      {(stage === "question" || stage === "evaluation_shown") && currentQuestion && (
        <div className="max-w-2xl mx-auto space-y-5">
          {/* Progress */}
          <InterviewProgress
            current={currentQuestionNum}
            total={totalQuestions}
            difficulty={currentDifficulty}
            topic={currentQuestion.topic}
          />

          {/* Question card */}
          <div className="rounded-xl bg-slate-50 border border-slate-200 p-6">
            <div className="flex items-start justify-between gap-3 mb-4">
              <QuestionBlock question={currentQuestion} />
            </div>

            {/* TTS — listen to question */}
            <div className="border-t border-slate-200 pt-3 mb-4">
              <TtsButton questionText={currentQuestion.question} />
            </div>

            {/* Answer area — only in question stage */}
            {stage === "question" && (
              <div className="space-y-3">
                {/* Mode toggle */}
                <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-50 border border-slate-300/50 w-fit">
                  <button
                    onClick={() => setInputMode("text")}
                    className={[
                      "flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md font-medium transition-colors",
                      inputMode === "text"
                        ? "bg-slate-200 text-slate-900"
                        : "text-slate-500 hover:text-slate-800",
                    ].join(" ")}
                  >
                    <Edit3 className="w-3 h-3" />
                    Text
                  </button>
                  <button
                    onClick={() => setInputMode("voice")}
                    className={[
                      "flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md font-medium transition-colors",
                      inputMode === "voice"
                        ? "bg-slate-200 text-slate-900"
                        : "text-slate-500 hover:text-slate-800",
                    ].join(" ")}
                  >
                    <Mic className="w-3 h-3" />
                    Voice
                  </button>
                </div>

                {/* TEXT MODE */}
                {inputMode === "text" && (
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-slate-500 uppercase tracking-wide block">
                      Your Answer
                    </label>
                    <textarea
                      ref={textareaRef}
                      value={answerText}
                      onChange={(e) => setAnswerText(e.target.value)}
                      placeholder="Type your answer here... Be thorough — cover key concepts, trade-offs, and examples."
                      rows={7}
                      className="w-full rounded-lg bg-slate-100 border border-slate-300 text-sm text-slate-800 placeholder:text-slate-400 px-4 py-3 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 resize-none transition-colors leading-relaxed"
                    />
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-slate-500 font-mono">
                        {answerText.trim().split(/\s+/).filter(Boolean).length} words
                      </span>
                      <Button
                        variant="primary"
                        size="md"
                        onClick={handleSubmitAnswer}
                        disabled={!answerText.trim()}
                      >
                        <Send className="w-3.5 h-3.5" />
                        Submit Answer
                      </Button>
                    </div>
                  </div>
                )}

                {/* VOICE MODE */}
                {inputMode === "voice" && (
                  <div className="space-y-3">
                    <div className="rounded-lg bg-slate-50 border border-slate-300/50 p-4 space-y-3">
                      <div className="flex items-center gap-2">
                        <Layers className="w-3.5 h-3.5 text-blue-600" />
                        <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">
                          Voice Answer
                        </span>
                        <span className="text-[10px] text-slate-400 ml-auto">
                          {/* Whisper available only with OPENAI_API_KEY; offline fallback active */}
                          STT: {typeof window !== "undefined" && window.MediaRecorder ? "Browser Recording Ready" : "Unavailable"}
                        </span>
                      </div>
                      <VoiceRecorderPanel
                        key={voiceKey}
                        onTranscriptReady={(text) => setAnswerText(text)}
                      />
                      {/* Fallback hint */}
                      <p className="text-[10px] text-slate-500 leading-relaxed">
                        Voice uses the backend transcription service (Whisper when configured,
                        offline fallback otherwise). Always review the transcript before submitting.
                        Switch to Text Mode if recording fails.
                      </p>
                    </div>

                    {/* Edit in textarea + submit */}
                    {answerText.trim() && (
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wide block">
                          Final Answer (edit if needed)
                        </label>
                        <textarea
                          value={answerText}
                          onChange={(e) => setAnswerText(e.target.value)}
                          rows={5}
                          className="w-full rounded-lg bg-slate-100 border border-slate-300 text-sm text-slate-800 placeholder:text-slate-400 px-4 py-3 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 resize-none transition-colors leading-relaxed"
                        />
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] text-slate-500 font-mono">
                            {answerText.trim().split(/\s+/).filter(Boolean).length} words
                          </span>
                          <Button
                            variant="primary"
                            size="md"
                            onClick={handleSubmitAnswer}
                            disabled={!answerText.trim()}
                          >
                            <Send className="w-3.5 h-3.5" />
                            Submit Answer
                          </Button>
                        </div>
                      </div>
                    )}

                    {/* Switch to text fallback */}
                    {!answerText.trim() && (
                      <button
                        onClick={() => setInputMode("text")}
                        className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-700 transition-colors"
                      >
                        <SkipForward className="w-3 h-3" />
                        Switch to Text Mode
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Evaluation */}
          {stage === "evaluation_shown" && evaluation && (
            <EvaluationPanel
              evaluation={evaluation}
              isLast={isLastQuestion}
              onNext={handleNextQuestion}
              onComplete={handleComplete}
              isLoading={false}
            />
          )}
        </div>
      )}

      {/* ── Completed ── */}
      {stage === "completed" && completedData && (
        <CompletedScreen
          score={completedData.score}
          readinessLabel={completedData.readinessLabel}
          readinessScore={completedData.readinessScore}
          recommendations={completedData.recommendations}
          onRestart={handleRestart}
        />
      )}
    </div>
  );
}