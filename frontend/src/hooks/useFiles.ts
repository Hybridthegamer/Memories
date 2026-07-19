import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deleteFile, fetchDownloadUrl, fetchFiles } from "../api/files";
import type { FileListResponse } from "../types";

const PAGE_SIZE = 30;

export function useWallStats() {
  return useQuery({
    queryKey: ["files", "stats"],
    queryFn: () => fetchFiles(1, 1),
    select: (data: FileListResponse) => data.total,
    staleTime: 30_000,
  });
}

export function useFileWall() {
  return useInfiniteQuery<FileListResponse>({
    queryKey: ["files"],
    queryFn: ({ pageParam }) => fetchFiles(pageParam as number, PAGE_SIZE),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const loaded = lastPage.page * lastPage.page_size;
      return loaded < lastPage.total ? lastPage.page + 1 : undefined;
    },
    refetchInterval: (query) => {
      // Poll while anything on the wall is still processing, so thumbnails
      // pop in live without the visitor having to refresh.
      const hasProcessing = query.state.data?.pages?.some((p) => p?.items?.some((f) => f.status === "processing"));
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
