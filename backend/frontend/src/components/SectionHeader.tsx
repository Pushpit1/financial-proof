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
    <div className="flex flex-wrap items-end justify-between gap-4 pb-5 border-b border-[#C5C4B1]">
      <div className="space-y-2 max-w-3xl">
        <span className="t-pill bg-white border border-[#C5C4B1]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#FF6170]" />
          {eyebrow}
        </span>
        <h1 className="text-2xl sm:text-3xl font-medium tracking-tight text-[#191919]">
          {title}
        </h1>
        <p className="text-sm text-[#191919]/75 leading-relaxed">{description}</p>
      </div>
      {rightSlot && <div className="shrink-0">{rightSlot}</div>}
    </div>
  )
}
