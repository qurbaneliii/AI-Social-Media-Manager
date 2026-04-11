// filename: components/ui/FileDropzone.tsx
// purpose: Drag-and-drop uploader wrapper using react-dropzone.

"use client";

import { UploadCloud } from "lucide-react";
import { useDropzone } from "react-dropzone";

interface Props {
  label: string;
  accept?: Record<string, string[]>;
  multiple?: boolean;
  onFiles: (files: File[]) => void;
  disabled?: boolean;
}

export const FileDropzone = ({ label, accept, multiple = false, onFiles, disabled }: Props) => {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept,
    multiple,
    disabled,
    onDrop: (files) => onFiles(files)
  });

  return (
    <div
      {...getRootProps()}
      className={`rounded-xl border-2 border-dashed p-6 text-center transition ${
        isDragActive ? "border-teal-500 bg-teal-50" : "border-slate-300 bg-slate-50"
      } ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
    >
      <input {...getInputProps()} />
      <UploadCloud className="mx-auto mb-2 h-6 w-6 text-slate-500" />
      <p className="text-sm font-medium text-slate-700">{label}</p>
      <p className="text-xs text-slate-500">Drag files here or click to browse</p>
    </div>
  );
};
