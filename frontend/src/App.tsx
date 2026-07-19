import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GalleryPage } from "./pages/GalleryPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <GalleryPage />
    </QueryClientProvider>
  );
}
