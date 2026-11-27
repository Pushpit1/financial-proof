import React from 'react'

interface SectionHeaderProps {
  eyebrow: string
  title: React.ReactNode
  description: React.ReactNode
  rightSlot?: React.ReactNode
}

export function SectionHeader({
  eyebrow,
  title,
  description,
  rightSlot,
}: SectionHeaderProps) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4 pb-5 border-b border-slate-200">
      <div className="space-y-1.5 max-w-3xl">
        <div className="inline-flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-[#8e2460]">
          <span className="w-2 h-2 rounded-full bg-[#ff6b57]" />
          {eyebrow}
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#0a1429]">
          {title}
        </h1>
        <p className="text-sm text-slate-600 leading-relaxed">{description}</p>
      </div>
      {rightSlot && <div className="shrink-0">{rightSlot}</div>}
    </div>
  )
}
