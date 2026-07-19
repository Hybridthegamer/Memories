import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deleteFile, fetchFiles, fetchFolders } from "../api/files";
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

export function useFolders() {
  return useQuery({
    queryKey: ["files", "folders"],
    queryFn: fetchFolders,
    staleTime: 30_000,
  });
}

export function useFileWall(folder?: string | null) {
  return useInfiniteQuery<FileListResponse>({
    queryKey: ["files", "wall", folder ?? null],
    queryFn: ({ pageParam }) => fetchFiles(pageParam as number, PAGE_SIZE, folder),
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

