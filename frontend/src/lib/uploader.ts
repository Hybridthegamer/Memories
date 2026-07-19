import { api } from "../api/client";
import { rememberUpload } from "./ownership";

export type UploadProgressCallback = (percent: number) => void;

// PUT with progress via XHR (fetch's upload progress support is inconsistent).
function putWithProgress(
  url: string,
  blob: Blob,
  contentType: string,
  onProgress: UploadProgressCallback
): Promise<string> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", url);
    xhr.setRequestHeader("Content-Type", contentType);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(xhr.getResponseHeader("ETag") ?? "");
      } else {
        reject(new Error(`Upload failed: ${xhr.status}`));
      }
    };
    xhr.onerror = () => reject(new Error("Network error during upload"));
    xhr.send(blob);
  });
}

const SINGLE_UPLOAD_THRESHOLD = 50 * 1024 * 1024; // 50MB

export async function uploadFile(file: File, onProgress: UploadProgressCallback, folder?: string): Promise<string> {
  if (file.size < SINGLE_UPLOAD_THRESHOLD) {
    return uploadSingle(file, onProgress, folder);
  }
  return uploadMultipart(file, onProgress, folder);
}

async function uploadSingle(file: File, onProgress: UploadProgressCallback, folder?: string): Promise<string> {
  const { data } = await api.post("/files/upload-request", {
    filename: file.name,
    content_type: file.type,
    size_bytes: file.size,
    folder: folder || undefined,
  });
  const { file_id, upload_url, delete_token } = data;

  await putWithProgress(upload_url, file, file.type, onProgress);
  await api.post(`/files/${file_id}/confirm`);
  rememberUpload(file_id, delete_token);
  return file_id;
}

async function uploadMultipart(file: File, onProgress: UploadProgressCallback, folder?: string): Promise<string> {
  const { data } = await api.post("/files/upload-request/multipart/initiate", {
    filename: file.name,
    content_type: file.type,
    size_bytes: file.size,
    folder: folder || undefined,
  });
  const { file_id, part_size_bytes, delete_token } = data;

  const totalParts = Math.ceil(file.size / part_size_bytes);
  const parts: { part_number: number; etag: string }[] = [];
  let uploadedBytes = 0;

  try {
    for (let i = 0; i < totalParts; i++) {
      const partNumber = i + 1;
      const start = i * part_size_bytes;
      const end = Math.min(start + part_size_bytes, file.size);
      const chunk = file.slice(start, end);

      const { data: partData } = await api.post(`/files/${file_id}/multipart/part-url`, {
        part_number: partNumber,
      });

      const etag = await putWithProgress(partData.url, chunk, file.type, (chunkPercent) => {
        const chunkBytes = (chunk.size * chunkPercent) / 100;
        onProgress(Math.round(((uploadedBytes + chunkBytes) / file.size) * 100));
      });

      parts.push({ part_number: partNumber, etag });
      uploadedBytes += chunk.size;
    }

    await api.post(`/files/${file_id}/multipart/complete`, { parts });
  } catch (err) {
    await api.post(`/files/${file_id}/multipart/abort`).catch(() => {});
    throw err;
  }

  rememberUpload(file_id, delete_token);
  return file_id;
}
