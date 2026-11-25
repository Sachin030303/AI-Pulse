export function formatDate(value) {
  if (!value) return 'Date unavailable';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(date);
}
export function shortText(value, maxLength = 180) {
  const text = String(value || '').trim();
  return text.length > maxLength ? `${text.slice(0, maxLength - 1)}…` : text;
}
export function safeUrl(value) {
  try {
    const url = new URL(value);
    return ['https:', 'http:'].includes(url.protocol) ? url.href : null;
  } catch { return null; }
}
export function friendlyError(error) {
  if (error?.status === 401) return 'Session expired or authentication required. Sign in again.';
  if (error?.status === 403) return 'This account does not have access to this section.';
  return error?.message || 'An unexpected error occurred.';
}
