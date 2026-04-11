// filename: components/onboarding/OnboardingProgressStepper.tsx
// purpose: Visual 11-step onboarding progress with score and parallel indicator.
// dependencies: lucide-react, react

"use client";

import { CheckCircle2, CircleDot, GitFork } from "lucide-react";

interface Props {
  currentStep: number;
  score: number | null;
}

const steps = [
  "Sign up",
  "Company profile",
  "Brand guidelines PDF",
  "Post archive",
  "Sample images",
  "Vocabulary",
  "Tone analysis",
  "Visual extraction",
  "Platform connect",
  "Quality check",
  "First test post"
];

export const OnboardingProgressStepper = ({ currentStep, score }: Props) => {
  return (
    <ol className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4">
      {steps.map((label, idx) => {
        const step = idx + 1;
        const isCompleted = step < currentStep;
        const isCurrent = step === currentStep;
        const isParallel = step === 7 || step === 8;

        return (
          <li key={label} className="flex items-center gap-3">
            <div
              className={[
                "flex h-8 w-8 items-center justify-center rounded-full border text-xs font-semibold",
                isCompleted ? "border-emerald-500 bg-emerald-50 text-emerald-700" : "",
                isCurrent ? "border-sky-600 ring-2 ring-sky-200 text-sky-700" : "",
                !isCompleted && !isCurrent ? "border-slate-300 bg-slate-50 text-slate-500" : ""
              ].join(" ")}
            >
              {isCompleted ? <CheckCircle2 className="h-4 w-4" /> : step}
            </div>
            <div className="flex items-center gap-2">
              <span className={isCurrent ? "font-semibold text-slate-900" : "text-slate-700"}>{label}</span>
              {isParallel ? (
                <span className="inline-flex items-center gap-1 rounded bg-teal-50 px-2 py-0.5 text-[11px] text-teal-700">
                  <GitFork className="h-3 w-3" />
                  parallel
                </span>
              ) : null}
              {step === 10 && score !== null ? (
                <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-slate-900 text-[10px] font-semibold text-white">
                  {Math.round(score)}
                </span>
              ) : null}
              {isCurrent ? <CircleDot className="h-4 w-4 text-sky-600" /> : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
};
