// There are no accounts. "Ownership" of an upload is just knowing the
// one-time delete token the server handed back when you uploaded it. We
// keep a local map of { fileId -> token } so this browser can prove it was
// the uploader later. Losing localStorage (different device, cleared data)
// means losing delete rights on your own uploads — that's the accepted
// tradeoff for a no-login platform.

const STORAGE_KEY = "memories.my_uploads";

interface OwnedUpload {
  deleteToken: string;
  uploadedAt: string;
}

type OwnershipMap = Record<string, OwnedUpload>;

function readMap(): OwnershipMap {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as OwnershipMap) : {};
  } catch {
    return {};
  }
}

function writeMap(map: OwnershipMap): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(map));
  } catch {
    // localStorage unavailable (private mode, quota) — ownership just won't persist.
  }
}

export function rememberUpload(fileId: string, deleteToken: string): void {
  const map = readMap();
  map[fileId] = { deleteToken, uploadedAt: new Date().toISOString() };
  writeMap(map);
}

export function getDeleteToken(fileId: string): string | null {
  return readMap()[fileId]?.deleteToken ?? null;
}

export function forgetUpload(fileId: string): void {
  const map = readMap();
  delete map[fileId];
  writeMap(map);
}

export function isMine(fileId: string): boolean {
  return getDeleteToken(fileId) !== null;
}
