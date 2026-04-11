// filename: components/ui/TagInput.tsx
// purpose: Comma/enter based chip input for short token lists.

"use client";

import { X } from "lucide-react";
import { useState } from "react";

interface Props {
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
}

export const TagInput = ({ label, values, onChange, placeholder }: Props) => {
  const [input, setInput] = useState("");

  const add = (value: string) => {
    const next = value.trim();
    if (!next || values.includes(next)) return;
    onChange([...values, next]);
    setInput("");
  };

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-slate-700">{label}</label>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === ",") {
            e.preventDefault();
            add(input.replace(/,$/, ""));
          }
        }}
        onBlur={() => add(input)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
      />
      <div className="flex flex-wrap gap-2">
        {values.map((item) => (
          <span key={item} className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
            {item}
            <button
              type="button"
              onClick={() => onChange(values.filter((v) => v !== item))}
              className="text-slate-500 hover:text-slate-900"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
      </div>
    </div>
  );
};
