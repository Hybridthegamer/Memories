import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deleteFile, fetchDownloadUrl, fetchFiles } from "../api/files";
import type { FileListResponse } from "../types";

export function useFileList(page: number) {
  return useQuery<FileListResponse>({
    queryKey: ["files", page],
    queryFn: () => fetchFiles(page),
    refetchInterval: (query) => {
      // Poll while any item is still processing, to reflect thumbnail-ready status.
      const hasProcessing = query.state.data?.items?.some((f) => f.status === "processing");
      return hasProcessing ? 3000 : false;
    },
  });
}

export function useDeleteFile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fileId: string) => deleteFile(fileId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["files"] }),
  });
}

export function useDownloadUrl() {
  return useMutation({
    mutationFn: (fileId: string) => fetchDownloadUrl(fileId),
  });
}
