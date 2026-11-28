const STYLES: Record<string, string> = {
  passed: 'bg-[#191919] text-white border-[#191919]',
  ready: 'bg-[#191919] text-white border-[#191919]',
  allow: 'bg-[#191919] text-white border-[#191919]',
  connected: 'bg-[#191919] text-white border-[#191919]',
  verified: 'bg-[#191919] text-white border-[#191919]',
  completed: 'bg-[#191919] text-white border-[#191919]',
  captured: 'bg-[#191919] text-white border-[#191919]',
  success: 'bg-[#191919] text-white border-[#191919]',
  balanced: 'bg-[#191919] text-white border-[#191919]',
  review: 'bg-[#E6CA5A] text-[#191919] border-[#C5C4B1]',
  advisory: 'bg-[#E6CA5A] text-[#191919] border-[#C5C4B1]',
  received: 'bg-[#EBEBE6] text-[#191919] border-[#C5C4B1]',
  draft: 'bg-[#F5F5F3] text-[#191919] border-[#C5C4B1]',
  authorized: 'bg-[#EBEBE6] text-[#191919] border-[#C5C4B1]',
  failed: 'bg-[#FF6170] text-[#191919] border-[#FF6170]',
  block: 'bg-[#FF6170] text-[#191919] border-[#FF6170]',
  violation: 'bg-[#FF6170] text-[#191919] border-[#FF6170]',
  refuted: 'bg-[#FF6170] text-[#191919] border-[#FF6170]',
  unreachable: 'bg-[#FF6170] text-[#191919] border-[#FF6170]',
  rejected: 'bg-[#FF6170] text-[#191919] border-[#FF6170]',
}

export function StatusBadge({ value }: { value: string }) {
  const cls =
    STYLES[value.toLowerCase()] ??
    'bg-[#EBEBE6] text-[#191919] border-[#C5C4B1]'
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-md border text-[11px] font-semibold uppercase tracking-wider font-mono-tabular ${cls}`}
    >
      {value}
    </span>
  )
}
