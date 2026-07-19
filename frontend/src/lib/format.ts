export function isWithinDeleteWindow(deadline: string): boolean {
  return new Date(deadline).getTime() > Date.now();
}

export function formatTimeLeft(deadline: string): string {
  const ms = new Date(deadline).getTime() - Date.now();
  if (ms <= 0) return "";
  const hours = Math.floor(ms / (1000 * 60 * 60));
  if (hours < 1) return "under 1h left to delete";
  if (hours < 24) return `${hours}h left to delete`;
  return `${Math.floor(hours / 24)}d left to delete`;
}
