import { api } from "./client";
import { getDeleteToken, forgetUpload } from "../lib/ownership";
import type { FileListResponse } from "../types";

export async function fetchFiles(page: number, pageSize = 50): Promise<FileListResponse> {
  const { data } = await api.get<FileListResponse>(`/files?page=${page}&page_size=${pageSize}`);
  // Guard against a misconfigured API base URL: a wrong/missing origin can
  // make requests land on this app's own dev/static server instead of the
  // API, which happily returns index.html as a 200 rather than erroring.
  // Trusting that shape would otherwise crash the gallery render.
  if (!data || !Array.isArray(data.items)) {
    throw new Error("Unexpected response from the API — check VITE_API_BASE_URL.");
  }
  return data;
}

export async function fetchDownloadUrl(fileId: string): Promise<string> {
  const { data } = await api.get(`/files/${fileId}/download-url`);
  return data.url;
}

export async function deleteFile(fileId: string): Promise<void> {
  const deleteToken = getDeleteToken(fileId);
  if (!deleteToken) {
    throw new Error("This upload isn't yours to delete.");
  }
  await api.delete(`/files/${fileId}`, { headers: { "X-Delete-Token": deleteToken } });
  forgetUpload(fileId);
}
