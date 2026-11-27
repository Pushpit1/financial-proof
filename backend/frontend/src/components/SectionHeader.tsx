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
    <div className="flex flex-wrap items-end justify-between gap-4 pb-4 border-b border-[#0B1F3A]/15">
      <div className="space-y-1 max-w-3xl">
        <div className="text-[11px] font-mono-tabular font-bold uppercase tracking-wider text-[#047857]">
          {eyebrow}
        </div>
        <h1 className="font-serif-editorial text-2xl sm:text-3xl font-bold tracking-tight text-[#0B1F3A]">
          {title}
        </h1>
        <p className="text-sm text-slate-600 leading-relaxed">{description}</p>
      </div>
      {rightSlot && <div className="shrink-0">{rightSlot}</div>}
    </div>
  )
}
