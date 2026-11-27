const STYLES: Record<string, string> = {
  passed: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  ready: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  allow: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  connected: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  verified: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  completed: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  captured: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  success: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  review: 'bg-amber-50 text-amber-800 border-amber-200',
  advisory: 'bg-amber-50 text-amber-800 border-amber-200',
  received: 'bg-sky-50 text-sky-800 border-sky-200',
  draft: 'bg-slate-100 text-slate-700 border-slate-200',
  authorized: 'bg-sky-50 text-sky-800 border-sky-200',
  failed: 'bg-rose-50 text-rose-800 border-rose-200',
  block: 'bg-rose-50 text-rose-800 border-rose-200',
  unreachable: 'bg-rose-50 text-rose-800 border-rose-200',
  rejected: 'bg-rose-50 text-rose-800 border-rose-200',
}

export function StatusBadge({ value }: { value: string }) {
  const cls =
    STYLES[value.toLowerCase()] ??
    'bg-slate-100 text-slate-700 border-slate-200'
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded border text-[11px] font-medium uppercase tracking-wide font-mono-tabular ${cls}`}
    >
      {value}
    </span>
  )
}
