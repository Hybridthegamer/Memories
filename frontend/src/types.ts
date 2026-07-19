export type MediaType = "image" | "video";

export type FileStatus = "pending" | "uploaded" | "processing" | "ready" | "failed";

export interface FileItem {
  id: string;
  original_name: string;
  media_type: MediaType;
  size_bytes: number;
  status: FileStatus;
  thumbnail_url: string | null;
  created_at: string;
  delete_deadline: string;
  folder: string | null;
}

export interface FileListResponse {
  items: FileItem[];
  page: number;
  page_size: number;
  total: number;
}

export interface FolderSummary {
  name: string;
  file_count: number;
}
