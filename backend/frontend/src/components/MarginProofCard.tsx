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
    <div className="bg-white border border-[#C5C4B1] alloy-card p-5 space-y-3 text-xs shadow-xs">
      <div className="font-mono-tabular font-bold text-[#191919] border-b border-[#191919]/10 pb-2.5 flex items-center justify-between gap-2">
        <span>POLICY SPEC // {sectionCode}</span>
        <StatusBadge value={badge} />
      </div>
      <div className="p-3.5 rounded-xl bg-[#191919] text-[#EBEBE6] font-mono-tabular space-y-1 text-[11px] relative overflow-hidden">
        <div className="h-0.5 w-full bg-[#FF6170] absolute top-0 left-0" />
        {axiomLines}
      </div>
      <div className="text-[#191919]/75 leading-relaxed">{note}</div>
    </div>
  )
}
