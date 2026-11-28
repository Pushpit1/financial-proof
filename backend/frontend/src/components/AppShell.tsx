import React, { useState } from 'react'
import {
  Activity,
  FileCode2,
  FileSpreadsheet,
  FlaskConical,
  ShieldCheck,
  Flame,
  ScrollText,
  Menu,
  X,
  Home,
  KeyRound,
  Plus,
} from 'lucide-react'
import type { SubjectSummary, SystemStatus } from '../api/platform'
import { StatusBadge } from './StatusBadge'

export type NavSection =
  | 'overview'
  | 'contracts'
  | 'documents'
  | 'simulations'
  | 'verification'
  | 'analysis'
  | 'audit'

const NAV_ITEMS: Array<{
  id: NavSection
  label: string
  code: string
  icon: React.ComponentType<{ className?: string }>
}> = [
  { id: 'overview', label: 'Overview & Telemetry', code: '1.0', icon: Activity },
  { id: 'contracts', label: 'Financial Contracts', code: '2.0', icon: FileCode2 },
  { id: 'documents', label: 'Documents & Recon', code: '3.0', icon: FileSpreadsheet },
  { id: 'simulations', label: 'Simulations & Attacks', code: '4.0', icon: FlaskConical },
  { id: 'verification', label: 'Proof & Reports', code: '5.0', icon: ShieldCheck },
  { id: 'analysis', label: 'Blast Radius & Guardian', code: '6.0', icon: Flame },
  { id: 'audit', label: 'Audit & Access', code: '7.0', icon: ScrollText },
]

interface AppShellProps {
  activeSection: NavSection
  onSelectSection: (section: NavSection) => void
  onOpenLanding: () => void
  onOpenSignIn: () => void
  operatorLabel: string
  workspaceSubject: string
  subjects: SubjectSummary[]
  onChangeSubject: (subject: string) => void
  onAddSubject: (subject: string) => void
  systemStatus: SystemStatus | null
  children: React.ReactNode
}

export function AppShell({
  activeSection,
  onSelectSection,
  onOpenLanding,
  onOpenSignIn,
  operatorLabel,
  workspaceSubject,
  subjects,
  onChangeSubject,
  onAddSubject,
  systemStatus,
  children,
}: AppShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [creatingSubject, setCreatingSubject] = useState(false)
  const [newSubjectName, setNewSubjectName] = useState('')

  const handleAddSubject = (e: React.FormEvent) => {
    e.preventDefault()
    const clean = newSubjectName.trim()
    if (!clean) return
    onAddSubject(clean)
    setNewSubjectName('')
    setCreatingSubject(false)
  }

  const sidebarContent = (
    <div className="flex flex-col h-full bg-[#191919] text-[#EBEBE6] border-r border-white/10">
      <div className="h-16 px-4 flex items-center justify-between border-b border-white/10">
        <button
          type="button"
          onClick={onOpenLanding}
          className="flex items-center gap-2.5 text-left group cursor-pointer"
        >
          <svg width="24" height="24" viewBox="0 0 28 28" fill="none" aria-hidden="true">
            <polygon points="14,3 25,22 3,22" stroke="#EBEBE6" strokeWidth="1.8" fill="none" />
            <polygon points="14,8 21,20 7,20" stroke="#EBEBE6" strokeWidth="1.2" fill="none" opacity="0.6" />
            <circle cx="14" cy="16" r="2.2" fill="#FF6170" />
          </svg>
          <div>
            <div className="text-sm font-bold tracking-tight text-white group-hover:text-[#FF6170] transition-colors uppercase">
              Financial Proof
            </div>
            <div className="text-[10px] font-mono-tabular uppercase tracking-wider text-white/50">
              Decision Workbench
            </div>
          </div>
        </button>
        <button
          type="button"
          onClick={() => setMobileOpen(false)}
          className="lg:hidden p-1 text-white/60 hover:text-white"
          aria-label="Close navigation"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Multi-Subject Switcher & Quick Creator */}
      <div className="p-3.5 border-b border-white/10 bg-white/5 space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-[10px] font-mono-tabular uppercase tracking-wider text-white/55">
            Active Subject ({subjects.length})
          </label>
          <button
            type="button"
            onClick={() => setCreatingSubject((v) => !v)}
            className="inline-flex items-center gap-1 text-[10px] font-mono-tabular text-[#FF6170] hover:underline cursor-pointer"
          >
            <Plus className="w-3 h-3" />
            {creatingSubject ? 'Close' : 'New Subject'}
          </button>
        </div>

        <select
          value={workspaceSubject}
          onChange={(e) => onChangeSubject(e.target.value)}
          className="w-full px-2.5 py-1.5 rounded-lg border border-white/20 bg-black/40 text-xs font-mono-tabular text-white focus:outline-none focus:border-[#FF6170]"
        >
          {subjects.map((s) => (
            <option key={s.subject} value={s.subject} className="bg-[#191919] text-white">
              {s.subject} ({s.proof_count} {s.proof_count === 1 ? 'proof' : 'proofs'})
            </option>
          ))}
        </select>

        {creatingSubject && (
          <form onSubmit={handleAddSubject} className="flex gap-1.5 pt-1">
            <input
              value={newSubjectName}
              onChange={(e) => setNewSubjectName(e.target.value)}
              placeholder="e.g. payout-batch-q2"
              className="flex-1 min-w-0 px-2 py-1 rounded border border-white/25 bg-black/40 text-[11px] font-mono-tabular text-white focus:outline-none focus:border-[#FF6170]"
            />
            <button
              type="submit"
              className="px-2.5 py-1 rounded bg-[#FF6170] text-[#191919] text-[10px] font-bold uppercase cursor-pointer"
            >
              Add
            </button>
          </form>
        )}
      </div>

      <nav className="flex-1 p-3 space-y-1 overflow-y-auto text-xs">
        {NAV_ITEMS.map(({ id, label, code, icon: Icon }) => {
          const active = activeSection === id
          return (
            <button
              key={id}
              type="button"
              onClick={() => {
                onSelectSection(id)
                setMobileOpen(false)
              }}
              className={`w-full flex items-center justify-between gap-2 px-3 py-2.5 rounded-lg transition-colors text-left cursor-pointer ${
                active
                  ? 'rounded-tl-none bg-white text-[#191919] font-semibold shadow-sm'
                  : 'text-white/75 hover:bg-white/10 hover:text-white'
              }`}
            >
              <span className="flex items-center gap-2.5 min-w-0">
                <Icon className={`w-4 h-4 shrink-0 ${active ? 'text-[#FF6170]' : 'text-white/50'}`} />
                <span className="truncate">{label}</span>
              </span>
              <span className={`font-mono-tabular text-[10px] ${active ? 'text-[#191919]/65' : 'text-white/40'}`}>
                {code}
              </span>
            </button>
          )
        })}
      </nav>

      <div className="p-3.5 border-t border-white/10 space-y-2 text-[11px]">
        <button
          type="button"
          onClick={onOpenSignIn}
          className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg border border-white/20 text-white/90 hover:bg-white/10 text-xs font-medium cursor-pointer"
        >
          <span className="flex items-center gap-2 truncate">
            <KeyRound className="w-3.5 h-3.5 text-[#FF6170] shrink-0" />
            <span className="truncate">{operatorLabel}</span>
          </span>
          <span className="text-[10px] font-mono-tabular text-white/50">AUTH</span>
        </button>

        <button
          type="button"
          onClick={onOpenLanding}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-white/20 text-white/90 hover:bg-white/10 text-xs font-medium cursor-pointer"
        >
          <Home className="w-3.5 h-3.5 text-[#E6CA5A]" />
          Public Website View
        </button>

        <div className="p-2.5 rounded-lg bg-white/5 border border-white/10 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-mono-tabular text-white/60">PostgreSQL</span>
            <StatusBadge value={systemStatus?.database ?? 'checking'} />
          </div>
          <div className="text-[10px] font-mono-tabular text-[#E6CA5A]">
            Decimal(18,2) · AI Advisory Only
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen flex bg-[#F5F5F3] text-[#191919]">
      <aside className="hidden lg:block w-64 shrink-0">{sidebarContent}</aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div className="w-64 h-full">{sidebarContent}</div>
          <div
            className="flex-1 bg-black/45"
            onClick={() => setMobileOpen(false)}
          />
        </div>
      )}

      <div className="flex-1 min-w-0 flex flex-col">
        <header className="h-14 bg-[#EBEBE6] border-b border-[#C5C4B1] px-4 lg:px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-1.5 rounded-lg border border-[#C5C4B1] bg-white text-[#191919]"
              aria-label="Open navigation"
            >
              <Menu className="w-4 h-4" />
            </button>
            <div className="text-xs font-mono-tabular text-[#191919]/65">
              SUBJECT // <span className="text-[#191919] font-semibold">{workspaceSubject}</span>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {systemStatus && (
              <span className="hidden sm:inline-flex items-center gap-1.5 text-xs font-mono-tabular text-[#191919]/65">
                v{systemStatus.version || '2.0'} · {systemStatus.environment}
                {systemStatus.alembic_revision ? ` · ${systemStatus.alembic_revision}` : ''}
              </span>
            )}
            <StatusBadge value={systemStatus?.database === 'connected' ? 'connected' : 'unreachable'} />
          </div>
        </header>

        {systemStatus?.database === 'unreachable' && (
          <div className="bg-[#E6CA5A]/25 border-b border-[#C5C4B1] px-4 sm:px-6 py-2 text-[11px] font-mono-tabular text-[#191919]">
            STATELESS ENGINE MODE: Compilation, simulations, repair verification, reconciliation, blast radius &amp; guardian run live.
          </div>
        )}

        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">
          {children}
        </main>
      </div>
    </div>
  )
}
