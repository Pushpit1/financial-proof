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
  { id: 'overview', label: 'Overview & Demo', group: 'Workspace', icon: Activity },
  { id: 'contracts', label: 'Financial Contracts', group: 'Workspace', icon: FileCode2 },
  { id: 'documents', label: 'Documents & Recon', group: 'Evidence', icon: FileSpreadsheet },
  { id: 'simulations', label: 'Simulations & Attacks', group: 'Verification', icon: FlaskConical },
  { id: 'verification', label: 'Proof & Reports', group: 'Verification', icon: ShieldCheck },
  { id: 'analysis', label: 'Blast Radius, AI & Guardian', group: 'Assurance', icon: Flame },
  { id: 'audit', label: 'Audit & Settings', group: 'Governance', icon: ScrollText },
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
    <div className="flex flex-col h-full bg-white border-r border-slate-200">
      <div className="h-14 px-4 flex items-center justify-between border-b border-slate-200">
        <button
          type="button"
          onClick={onOpenLanding}
          className="flex items-center gap-2.5 text-left group"
        >
          <div className="w-7 h-7 rounded bg-[#1E3A5F] text-white flex items-center justify-center text-xs font-bold font-mono-tabular">
            FP
          </div>
          <div>
            <div className="text-sm font-semibold tracking-tight text-slate-900 group-hover:text-[#1E3A5F]">
              Financial Proof
            </div>
            <div className="text-[10px] font-mono-tabular uppercase tracking-wider text-slate-500">
              Verification Engine
            </div>
          </div>
        </button>
        <button
          type="button"
          onClick={() => setMobileOpen(false)}
          className="lg:hidden p-1 text-slate-500"
          aria-label="Close navigation"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="p-3 border-b border-slate-200 bg-slate-50/70">
        <label className="block text-[10px] font-mono-tabular uppercase tracking-wider text-slate-500 mb-1">
          Active Workspace Subject
        </label>
        <input
          value={workspaceSubject}
          onChange={(e) => onChangeSubject(e.target.value)}
          placeholder="merchant-settlement-01"
          className="w-full px-2.5 py-1.5 rounded border border-slate-300 bg-white text-xs font-mono-tabular text-slate-900 focus:outline-none focus:border-[#1E3A5F]"
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
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors text-left ${
                active
                  ? 'bg-[#1E3A5F] text-white'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span className="truncate">{label}</span>
            </button>
          )
        })}
      </nav>

      <div className="p-3 border-t border-slate-200 space-y-2 text-[11px]">
        <button
          type="button"
          onClick={onOpenLanding}
          className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs"
        >
          <Home className="w-3.5 h-3.5" />
          Public Overview
        </button>
        <div className="px-2 py-2 rounded bg-slate-50 border border-slate-200 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-slate-500">PostgreSQL / DB</span>
            <StatusBadge value={systemStatus?.database ?? 'checking'} />
          </div>
          <div className="text-[10px] font-mono-tabular text-slate-500">
            Deterministic core · AI advisory only
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen flex bg-[#F9F8F5] text-slate-900">
      <aside className="hidden lg:block w-64 shrink-0">{sidebarContent}</aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div className="w-64 h-full">{sidebarContent}</div>
          <div
            className="flex-1 bg-slate-900/30"
            onClick={() => setMobileOpen(false)}
          />
        </div>
      )}

      <div className="flex-1 min-w-0 flex flex-col">
        <header className="h-14 bg-white border-b border-slate-200 px-4 lg:px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-1.5 rounded border border-slate-200 text-slate-600"
              aria-label="Open navigation"
            >
              <Menu className="w-4 h-4" />
            </button>
            <div className="text-xs font-mono-tabular text-slate-500">
              WORKSPACE / <span className="text-slate-900 font-semibold">{workspaceSubject}</span>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {systemStatus && (
              <span className="hidden sm:inline-flex items-center gap-1.5 text-xs font-mono-tabular text-slate-500">
                v{systemStatus.version} · {systemStatus.environment}
              </span>
            )}
            <StatusBadge value={systemStatus?.database === 'connected' ? 'connected' : 'unreachable'} />
          </div>
        </header>

        {systemStatus?.database === 'unreachable' && (
          <div className="bg-amber-50 border-b border-amber-200 px-6 py-2.5 text-xs text-amber-900 flex flex-wrap items-center justify-between gap-2">
            <span>
              <strong>Database Unreachable ({systemStatus.database_error_type || 'connection error'}):</strong>{' '}
              Stateless compilation, adversarial simulation, snapshot verification, reconciliation, and blast-radius computation are operational. Persisted storage requires a live PostgreSQL <code className="font-mono-tabular">DATABASE_URL</code>.
            </span>
          </div>
        )}

        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">
          {children}
        </main>
      </div>
    </div>
  )
}
