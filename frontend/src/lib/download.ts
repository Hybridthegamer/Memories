// Presigned download URLs already carry a Content-Disposition: attachment
// header from the backend, so a plain anchor click reliably downloads
// rather than navigates — even cross-origin, and without the popup-blocker
// issues window.open(url, "_blank") runs into when triggered repeatedly
// (e.g. for mass download).
export function triggerDownload(url: string): void {
  const a = document.createElement("a");
  a.href = url;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
}
