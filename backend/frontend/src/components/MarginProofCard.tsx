import React from 'react'
import { StatusBadge } from './StatusBadge'

interface MarginProofCardProps {
  sectionCode: string
  badge?: string
  axiomLines: React.ReactNode
  note: React.ReactNode
}

export function MarginProofCard({
  sectionCode,
  badge = 'verified',
  axiomLines,
  note,
}: MarginProofCardProps) {
  return (
    <div className="bg-white border border-[#0B1F3A]/20 rounded-xl p-4 distill-card space-y-3 text-xs">
      <div className="font-mono-tabular font-bold text-[#0B1F3A] border-b border-slate-200 pb-2 flex items-center justify-between gap-2">
        <span>MARGIN PROOF NOTE // {sectionCode}</span>
        <StatusBadge value={badge} />
      </div>
      <div className="p-3 rounded-lg bg-[#0B1F3A] text-slate-100 font-mono-tabular space-y-1 text-[11px]">
        {axiomLines}
      </div>
      <div className="text-slate-600 leading-relaxed">{note}</div>
    </div>
  )
}
