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
} from 'lucide-react'
import type { SystemStatus } from '../api/platform'
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
  group: string
  icon: React.ComponentType<{ className?: string }>
}> = [
  { id: 'overview', label: 'Overview & Telemetry', group: 'Workspace', icon: Activity },
  { id: 'contracts', label: 'Financial Contracts', group: 'Workspace', icon: FileCode2 },
  { id: 'documents', label: 'Documents & Recon', group: 'Evidence', icon: FileSpreadsheet },
  { id: 'simulations', label: 'Simulations & Attacks', group: 'Verification', icon: FlaskConical },
  { id: 'verification', label: 'Proof & Reports', group: 'Verification', icon: ShieldCheck },
  { id: 'analysis', label: 'Blast Radius, AI & Guardian', group: 'Decisioning', icon: Flame },
  { id: 'audit', label: 'Audit & Access', group: 'Governance', icon: ScrollText },
]

interface AppShellProps {
  activeSection: NavSection
  onSelectSection: (section: NavSection) => void
  onOpenLanding: () => void
  workspaceSubject: string
  onChangeSubject: (subject: string) => void
  systemStatus: SystemStatus | null
  children: React.ReactNode
}

export function AppShell({
  activeSection,
  onSelectSection,
  onOpenLanding,
  workspaceSubject,
  onChangeSubject,
  systemStatus,
  children,
}: AppShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false)

  const sidebarContent = (
    <div className="flex flex-col h-full bg-[#0a1429] text-white border-r border-slate-800">
      <div className="h-16 px-4 flex items-center justify-between border-b border-slate-800">
        <button
          type="button"
          onClick={onOpenLanding}
          className="flex items-center gap-2.5 text-left group"
        >
          <div className="w-8 h-8 rounded-lg alloy-accent-gradient text-[#0a1429] flex items-center justify-center text-xs font-extrabold font-mono-tabular">
            FP
          </div>
          <div>
            <div className="text-sm font-bold tracking-tight text-white group-hover:text-[#f5b74b]">
              Financial Proof
            </div>
            <div className="text-[10px] font-mono-tabular uppercase tracking-wider text-slate-400">
              Decisioning Platform
            </div>
          </div>
        </button>
        <button
          type="button"
          onClick={() => setMobileOpen(false)}
          className="lg:hidden p-1 text-slate-400"
          aria-label="Close navigation"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="p-3.5 border-b border-slate-800 bg-slate-900/40">
        <label className="block text-[10px] font-mono-tabular uppercase tracking-wider text-slate-400 mb-1.5">
          Workspace Subject
        </label>
        <input
          value={workspaceSubject}
          onChange={(e) => onChangeSubject(e.target.value)}
          placeholder="merchant-settlement-q1"
          className="w-full px-2.5 py-1.5 rounded-lg border border-slate-700 bg-slate-900 text-xs font-mono-tabular text-white focus:outline-none focus:border-[#ff6b57]"
        />
      </div>

      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => {
          const active = activeSection === id
          return (
            <button
              key={id}
              type="button"
              onClick={() => {
                onSelectSection(id)
                setMobileOpen(false)
              }}
              className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-xs font-medium transition-colors text-left ${
                active
                  ? 'bg-white text-[#0a1429] font-semibold shadow-sm'
                  : 'text-slate-300 hover:bg-slate-800/70 hover:text-white'
              }`}
            >
              <Icon className={`w-4 h-4 shrink-0 ${active ? 'text-[#ff6b57]' : 'text-slate-400'}`} />
              <span className="truncate">{label}</span>
            </button>
          )
        })}
      </nav>

      <div className="p-3.5 border-t border-slate-800 space-y-2.5 text-[11px]">
        <button
          type="button"
          onClick={onOpenLanding}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-700 text-slate-200 hover:bg-slate-800 text-xs font-medium"
        >
          <Home className="w-3.5 h-3.5 text-[#f5b74b]" />
          Platform Homepage
        </button>
        <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-mono-tabular text-slate-400">PostgreSQL</span>
            <StatusBadge value={systemStatus?.database ?? 'checking'} />
          </div>
          <div className="text-[10px] font-mono-tabular text-emerald-400">
            Deterministic core · AI advisory only
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen flex bg-[#f8f9fc] text-[#0a1429]">
      <aside className="hidden lg:block w-64 shrink-0">{sidebarContent}</aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div className="w-64 h-full">{sidebarContent}</div>
          <div
            className="flex-1 bg-slate-950/40"
            onClick={() => setMobileOpen(false)}
          />
        </div>
      )}

      <div className="flex-1 min-w-0 flex flex-col">
        <header className="h-16 bg-white border-b border-slate-200 px-4 lg:px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-1.5 rounded-lg border border-slate-200 text-[#0a1429]"
              aria-label="Open navigation"
            >
              <Menu className="w-4 h-4" />
            </button>
            <div className="text-xs font-mono-tabular text-slate-500">
              DECISION ENGINE // <span className="text-[#0a1429] font-semibold">{workspaceSubject}</span>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {systemStatus && (
              <span className="hidden sm:inline-flex items-center gap-1.5 text-xs font-mono-tabular text-slate-500">
                v{systemStatus.version || '2.0'} · {systemStatus.environment}
              </span>
            )}
            <StatusBadge value={systemStatus?.database === 'connected' ? 'connected' : 'unreachable'} />
          </div>
        </header>

        {systemStatus?.database === 'unreachable' && (
          <div className="bg-amber-50 border-b border-amber-200 px-4 sm:px-6 py-2 text-[11px] font-mono-tabular text-amber-900">
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
