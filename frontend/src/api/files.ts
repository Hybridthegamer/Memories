import { api } from "./client";
import type { FileListResponse } from "../types";

export async function fetchFiles(page: number, pageSize = 50): Promise<FileListResponse> {
  const { data } = await api.get<FileListResponse>(`/files?page=${page}&page_size=${pageSize}`);
  return data;
}

export async function fetchDownloadUrl(fileId: string): Promise<string> {
  const { data } = await api.get(`/files/${fileId}/download-url`);
  return data.url;
}

export async function deleteFile(fileId: string): Promise<void> {
  await api.delete(`/files/${fileId}`);
}
