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
    <div className="bg-white border border-slate-200 rounded-2xl p-4 alloy-card space-y-3 text-xs">
      <div className="font-mono-tabular font-bold text-[#0a1429] border-b border-slate-100 pb-2.5 flex items-center justify-between gap-2">
        <span>POLICY SPEC // {sectionCode}</span>
        <StatusBadge value={badge} />
      </div>
      <div className="p-3.5 rounded-xl bg-[#0a1429] text-slate-100 font-mono-tabular space-y-1 text-[11px] relative overflow-hidden">
        <div className="h-0.5 w-full alloy-accent-gradient absolute top-0 left-0" />
        {axiomLines}
      </div>
      <div className="text-slate-600 leading-relaxed">{note}</div>
    </div>
  )
}
