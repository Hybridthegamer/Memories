import { useAuth } from "../context/AuthContext";
import { UploadDropzone } from "../components/UploadDropzone";
import { GalleryGrid } from "../components/GalleryGrid";

export function GalleryPage() {
  const { logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="flex items-center justify-between px-6 py-4 bg-white border-b">
        <h1 className="text-lg font-semibold">Memories</h1>
        <button onClick={logout} className="text-sm text-gray-500 underline">
          Log out
        </button>
      </header>
      <main className="max-w-5xl mx-auto p-6 space-y-6">
        <UploadDropzone />
        <GalleryGrid />
      </main>
    </div>
  );
}
