import React, { useCallback, useEffect, useState } from 'react'
import { FolderKanban, Play, Plus, RefreshCw, Trash2 } from 'lucide-react'
import { apiClient } from '../api/client'
import {
  platformApi,
  type AuditEvent,
  type SubjectSummary,
  type SystemStatus,
} from '../api/platform'
import type { NavSection } from '../components/AppShell'
import { MarginProofCard } from '../components/MarginProofCard'
import { SectionHeader } from '../components/SectionHeader'
import { StatusBadge } from '../components/StatusBadge'

interface OverviewSectionProps {
  workspaceSubject: string
  subjects: SubjectSummary[]
  onSelectSubject: (subject: string) => void
  onAddSubject: (subject: string) => void
  onRemoveSubject: (subject: string) => void
  systemStatus: SystemStatus | null
  onRefreshSystem: () => Promise<void>
  onNavigate: (section: NavSection) => void
}

export function OverviewSection({
  workspaceSubject,
  subjects,
  onSelectSubject,
  onAddSubject,
  onRemoveSubject,
  systemStatus,
  onRefreshSystem,
  onNavigate,
}: OverviewSectionProps) {
  const [contractsCount, setContractsCount] = useState<number | null>(null)
  const [proofsCount, setProofsCount] = useState<number | null>(null)
  const [docsCount, setDocsCount] = useState<number | null>(null)
  const [audits, setAudits] = useState<AuditEvent[]>([])
  const [demoState, setDemoState] = useState<Record<string, unknown> | null>(null)
  const [cardErrors, setCardErrors] = useState<{
    contracts?: boolean
    proofs?: boolean
    documents?: boolean
  }>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [newSubjectInput, setNewSubjectInput] = useState('')

  const loadOverview = useCallback(async () => {
    setLoading(true)
    setError('')
    setCardErrors({})

    const [demoRes, cRes, pRes, dRes, aRes] = await Promise.allSettled([
      apiClient.get<{ success: boolean; state: Record<string, unknown> }>('/demo/state'),
      platformApi.listContracts(),
      platformApi.listProofsBySubject(workspaceSubject),
      platformApi.listDocuments(),
      platformApi.listAudit(),
    ])

    const errs: string[] = []
    const nextCardErrs: { contracts?: boolean; proofs?: boolean; documents?: boolean } = {}

    if (demoRes.status === 'fulfilled') {
      setDemoState(demoRes.value.state)
    } else {
      errs.push(`Demo: ${demoRes.reason instanceof Error ? demoRes.reason.message : 'failed'}`)
    }

    if (cRes.status === 'fulfilled') {
      setContractsCount(cRes.value.length)
    } else {
      nextCardErrs.contracts = true
      errs.push(`Contracts: ${cRes.reason instanceof Error ? cRes.reason.message : 'failed'}`)
    }

    if (pRes.status === 'fulfilled') {
      setProofsCount(pRes.value.length)
    } else {
      nextCardErrs.proofs = true
      errs.push(`Proofs: ${pRes.reason instanceof Error ? pRes.reason.message : 'failed'}`)
    }

    if (dRes.status === 'fulfilled') {
      setDocsCount(dRes.value.length)
    } else {
      nextCardErrs.documents = true
      errs.push(`Documents: ${dRes.reason instanceof Error ? dRes.reason.message : 'failed'}`)
    }

    if (aRes.status === 'fulfilled') {
      setAudits(aRes.value.slice(0, 8))
    } else {
      setAudits([])
      errs.push(`Audit: ${aRes.reason instanceof Error ? aRes.reason.message : 'failed'}`)
    }

    setCardErrors(nextCardErrs)
    if (errs.length > 0) setError(errs.join(' · '))
    setLoading(false)
  }, [workspaceSubject])

  useEffect(() => {
    void loadOverview()
  }, [loadOverview, systemStatus?.database])

  const resetDemo = async () => {
    setError('')
    try {
      const res = await apiClient.post<{ state: Record<string, unknown> }>('/demo/reset', {})
      setDemoState(res.state)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Demo reset failed.')
    }
  }

  const handleCreateSubject = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newSubjectInput.trim()) return
    onAddSubject(newSubjectInput.trim())
    setNewSubjectInput('')
  }

  const formatStat = (count: number | null, hasErr?: boolean) => {
    if (count !== null) return String(count)
    if (loading) return '…'
    if (hasErr) return 'API err'
    return systemStatus?.database === 'connected' ? '0' : 'DB offline'
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Section 1.0 // Axiomatic Engine Telemetry"
        title={
          <>
            Deterministic Verification Overview (<span className="math-var">{workspaceSubject}</span>)
          </>
        }
        description="Real-time deterministic state, multi-subject proof tracking, canonical simulation seeds, and immutable audit traces."
        rightSlot={
          <button
            type="button"
            onClick={() => {
              void onRefreshSystem()
              void loadOverview()
            }}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-md border border-[#C5C4B1] bg-white text-xs font-medium text-[#191919] hover:bg-slate-50 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh State
          </button>
        }
      />

      {error && (
        <div className="p-3 rounded-lg border border-rose-200 bg-rose-50 text-rose-800 text-xs">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Persisted Contracts"
          value={formatStat(contractsCount, cardErrors.contracts)}
          sub="Versioned financial rules"
          onClick={() => onNavigate('contracts')}
        />
        <StatCard
          label="Subject Proofs"
          value={formatStat(proofsCount, cardErrors.proofs)}
          sub={`Active: ${workspaceSubject}`}
          onClick={() => onNavigate('verification')}
        />
        <StatCard
          label="Evidence Documents"
          value={formatStat(docsCount, cardErrors.documents)}
          sub="SHA-256 verified files"
          onClick={() => onNavigate('documents')}
        />
        <StatCard
          label="Active Subjects"
          value={String(subjects.length)}
          sub={`DB: ${systemStatus?.database ?? 'checking'}${systemStatus?.alembic_revision ? ` · ${systemStatus.alembic_revision}` : ''}`}
          onClick={() => onNavigate('verification')}
        />
      </div>

      {/* Multi-Subject Management Strip */}
      <section className="bg-white border border-[#C5C4B1] rounded-xl p-5 distill-card space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-3">
          <div className="flex items-center gap-2 text-xs font-mono-tabular font-bold text-[#191919]">
            <FolderKanban className="w-4 h-4 text-[#FF6170]" />
            <span>MULTI-SUBJECT WORKSPACE MANAGER ({subjects.length})</span>
          </div>

          <form onSubmit={handleCreateSubject} className="flex flex-wrap items-center gap-2">
            <input
              type="text"
              value={newSubjectInput}
              onChange={(e) => setNewSubjectInput(e.target.value)}
              placeholder="New subject slug (e.g. payout-batch-q2)"
              className="rounded-lg border border-[#C5C4B1] bg-[#F5F5F3] px-3 py-1.5 text-xs font-mono-tabular min-w-[220px]"
            />
            <button
              type="submit"
              className="inline-flex items-center gap-1 rounded bg-[#191919] px-3 py-1.5 text-xs font-medium text-white hover:bg-[#2D2D2D] cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              Add &amp; Switch
            </button>
          </form>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
          {subjects.map((item) => {
            const active = item.subject === workspaceSubject
            return (
              <div
                key={item.subject}
                className={`p-3 rounded-lg border flex items-center justify-between gap-2 transition ${
                  active
                    ? 'bg-[#191919] text-white border-[#191919]'
                    : 'bg-[#F5F5F3] text-[#191919] border-[#C5C4B1] hover:border-[#191919]'
                }`}
              >
                <button
                  type="button"
                  onClick={() => onSelectSubject(item.subject)}
                  className="text-left min-w-0 flex-1 cursor-pointer"
                >
                  <div className="font-mono-tabular font-semibold truncate">{item.subject}</div>
                  <div className={`text-[11px] font-mono-tabular mt-0.5 ${active ? 'text-white/75' : 'text-slate-600'}`}>
                    {item.proof_count} {item.proof_count === 1 ? 'proof' : 'proofs'} · status: {item.latest_status}
                  </div>
                </button>
                <div className="flex items-center gap-1.5 shrink-0">
                  {active && (
                    <span className="t-pill !bg-[#FF6170] !text-[#191919] !py-0.5 !px-2 !text-[10px]">
                      ACTIVE
                    </span>
                  )}
                  {item.proof_count === 0 && subjects.length > 1 && (
                    <button
                      type="button"
                      onClick={() => onRemoveSubject(item.subject)}
                      title="Remove unused local subject"
                      className={`p-1 rounded hover:bg-black/10 cursor-pointer ${active ? 'text-white/70 hover:text-white' : 'text-slate-500 hover:text-[#191919]'}`}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <section className="lg:col-span-5 bg-white border border-[#C5C4B1] rounded-xl p-5 distill-card space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <div>
              <div className="text-[11px] font-mono-tabular font-bold text-[#191919]">
                CANONICAL DETERMINISTIC SEED
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Live state from <code className="font-mono-tabular">/api/demo/state</code>
              </p>
            </div>
            <button
              type="button"
              onClick={() => void resetDemo()}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#191919] text-white text-xs font-medium hover:bg-[#2D2D2D] cursor-pointer"
            >
              <Play className="w-3.5 h-3.5" />
              Reset Seed
            </button>
          </div>

          {demoState ? (
            <div className="grid grid-cols-2 gap-2.5 text-xs font-mono-tabular">
              <div className="p-2.5 rounded bg-[#F5F5F3] border border-slate-200">
                <div className="text-slate-500">Seed</div>
                <div className="font-bold text-[#191919] mt-0.5">{String(demoState.seed)}</div>
              </div>
              <div className="p-2.5 rounded bg-[#F5F5F3] border border-slate-200">
                <div className="text-slate-500">Simulation ID</div>
                <div className="font-bold text-[#191919] mt-0.5 truncate">{String(demoState.simulation_id)}</div>
              </div>
              <div className="p-2.5 rounded bg-[#F5F5F3] border border-slate-200">
                <div className="text-slate-500">Contract ID</div>
                <div className="font-bold text-[#191919] mt-0.5 truncate">{String(demoState.contract_id)}</div>
              </div>
              <div className="p-2.5 rounded bg-[#F5F5F3] border border-slate-200">
                <div className="text-slate-500">Payment ID</div>
                <div className="font-bold text-[#191919] mt-0.5 truncate">{String(demoState.payment_id)}</div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 font-mono-tabular">Loading canonical state…</div>
          )}

          <div className="flex flex-wrap gap-2 pt-1">
            <button
              type="button"
              onClick={() => onNavigate('simulations')}
              className="px-3 py-1.5 rounded border border-[#C5C4B1] text-xs font-medium text-[#191919] hover:bg-slate-50 cursor-pointer"
            >
              Open Simulations →
            </button>
            <button
              type="button"
              onClick={() => onNavigate('analysis')}
              className="px-3 py-1.5 rounded border border-[#C5C4B1] text-xs font-medium text-[#191919] hover:bg-slate-50 cursor-pointer"
            >
              Blast Radius &amp; Guardian →
            </button>
          </div>
        </section>

        <section className="lg:col-span-4 bg-white border border-[#C5C4B1] rounded-xl overflow-hidden distill-card">
          <div className="px-5 py-3.5 border-b border-slate-200 flex items-center justify-between">
            <h2 className="text-xs font-mono-tabular font-bold text-[#191919]">
              RECENT AUDIT STREAM
            </h2>
            <button
              type="button"
              onClick={() => onNavigate('audit')}
              className="text-xs text-[#191919] hover:underline font-medium cursor-pointer"
            >
              View all
            </button>
          </div>
          {audits.length === 0 ? (
            <div className="p-5 text-xs text-slate-600 leading-relaxed">
              {loading
                ? 'Loading recent audit stream…'
                : systemStatus?.database === 'connected'
                  ? 'No audit events recorded yet. Execute a Guardian check, Contract decision, or Proof evaluation.'
                  : 'Audit persistence requires a connected PostgreSQL database. All stateless verification engines remain operational.'}
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {audits.map((ev) => (
                <div key={ev.id} className="px-5 py-2.5 flex items-center justify-between gap-2 text-xs">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <StatusBadge value={ev.category} />
                      <span className="font-mono-tabular font-medium text-[#191919] truncate">
                        {ev.action}
                      </span>
                    </div>
                    <div className="text-slate-500 truncate mt-0.5">{ev.summary}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <aside className="lg:col-span-3">
          <MarginProofCard
            sectionCode="SEC. 1.0"
            badge={systemStatus?.database === 'connected' ? 'connected' : 'advisory'}
            axiomLines={
              <>
                <div>∀ tx ∈ Ledger : Drift(tx) == 0</div>
                <div className="text-emerald-300">Arithmetic: Decimal(18, 2)</div>
                <div className="text-amber-300">AI Override: FORBIDDEN</div>
              </>
            }
            note="Every platform module separates deterministic financial arithmetic from read-only advisory diagnostics. Open Demo Mode active (sign-in optional)."
          />
        </aside>
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  sub,
  onClick,
}: {
  label: string
  value: string
  sub: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="text-left bg-white border border-[#C5C4B1] rounded-xl p-4 distill-card hover:border-[#191919] transition-colors cursor-pointer"
    >
      <div className="text-[11px] font-mono-tabular uppercase tracking-wider text-slate-500">
        {label}
      </div>
      <div className="mt-2 text-2xl font-bold font-mono-tabular text-[#191919]">
        {value}
      </div>
      <div className="mt-1 text-xs text-slate-500 truncate">{sub}</div>
    </button>
  )
}
