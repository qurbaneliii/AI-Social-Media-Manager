// filename: hooks/usePresignUpload.ts
// purpose: End-to-end media upload helper (presign, PUT upload, confirm).
// dependencies: react, lib/api

import { useState } from "react";

import { ApiError, confirmUpload, presignUpload, uploadToPresignedUrl } from "@/lib/api";

interface UploadInput {
  company_id: string;
  file: File;
  onProgress?: (pct: number) => void;
}

export const usePresignUpload = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<ApiError | null>(null);
  const [assetId, setAssetId] = useState<string | null>(null);

  const upload = async (input: UploadInput): Promise<string> => {
    setIsUploading(true);
    setProgress(0);
    setError(null);

    try {
      const presigned = await presignUpload(input.company_id, input.file.name, input.file.type);
      setAssetId(presigned.asset_id);

      await uploadToPresignedUrl(presigned.upload_url, input.file, (pct) => {
        setProgress(pct);
        input.onProgress?.(pct);
      });

      await confirmUpload(presigned.asset_id);
      setProgress(100);
      return presigned.asset_id;
    } catch (e) {
      const err = e as ApiError;
      setError(err);
      throw err;
    } finally {
      setIsUploading(false);
    }
  };

  return {
    upload,
    isUploading,
    progress,
    error,
    assetId
  };
};
