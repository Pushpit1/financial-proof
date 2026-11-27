import { useEffect, useState } from 'react'
import { Play, RefreshCw } from 'lucide-react'
import { apiClient } from '../api/client'
import { platformApi, type AuditEvent, type SystemStatus } from '../api/platform'
import type { NavSection } from '../components/AppShell'
import { MarginProofCard } from '../components/MarginProofCard'
import { SectionHeader } from '../components/SectionHeader'
import { StatusBadge } from '../components/StatusBadge'

interface OverviewSectionProps {
  workspaceSubject: string
  systemStatus: SystemStatus | null
  onRefreshSystem: () => Promise<void>
  onNavigate: (section: NavSection) => void
}

export function OverviewSection({
  workspaceSubject,
  systemStatus,
  onRefreshSystem,
  onNavigate,
}: OverviewSectionProps) {
  const [contractsCount, setContractsCount] = useState<number | null>(null)
  const [proofsCount, setProofsCount] = useState<number | null>(null)
  const [docsCount, setDocsCount] = useState<number | null>(null)
  const [audits, setAudits] = useState<AuditEvent[]>([])
  const [demoState, setDemoState] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadOverview = async () => {
    setLoading(true)
    setError('')
    try {
      const demo = await apiClient.get<{ success: boolean; state: Record<string, unknown> }>('/demo/state')
      setDemoState(demo.state)

      if (systemStatus?.database === 'connected') {
        const [cRes, pRes, dRes, aRes] = await Promise.allSettled([
          platformApi.listContracts(),
          platformApi.listProofsBySubject(workspaceSubject),
          platformApi.listDocuments(),
          platformApi.listAudit(),
        ])
        const errs: string[] = []
        if (cRes.status === 'fulfilled') setContractsCount(cRes.value.length)
        else {
          setContractsCount(null)
          errs.push(`Contracts: ${cRes.reason instanceof Error ? cRes.reason.message : 'failed'}`)
        }
        if (pRes.status === 'fulfilled') setProofsCount(pRes.value.length)
        else {
          setProofsCount(null)
          errs.push(`Proofs: ${pRes.reason instanceof Error ? pRes.reason.message : 'failed'}`)
        }
        if (dRes.status === 'fulfilled') setDocsCount(dRes.value.length)
        else {
          setDocsCount(null)
          errs.push(`Documents: ${dRes.reason instanceof Error ? dRes.reason.message : 'failed'}`)
        }
        if (aRes.status === 'fulfilled') setAudits(aRes.value.slice(0, 8))
        else {
          setAudits([])
          errs.push(`Audit: ${aRes.reason instanceof Error ? aRes.reason.message : 'failed'}`)
        }
        if (errs.length > 0) setError(errs.join(' · '))
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to fetch telemetry.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadOverview()
  }, [workspaceSubject, systemStatus?.database])

  const resetDemo = async () => {
    setError('')
    try {
      const res = await apiClient.post<{ state: Record<string, unknown> }>('/demo/reset', {})
      setDemoState(res.state)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Demo reset failed.')
    }
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
        description="Real-time deterministic state, persisted verification counts, canonical simulation seeds, and immutable audit traces."
        rightSlot={
          <button
            type="button"
            onClick={() => {
              void onRefreshSystem()
              void loadOverview()
            }}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-md border border-[#0B1F3A]/25 bg-white text-xs font-medium text-[#0B1F3A] hover:bg-slate-50"
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
          value={
            contractsCount !== null
              ? String(contractsCount)
              : systemStatus?.database === 'connected'
                ? 'API err'
                : 'DB offline'
          }
          sub="Versioned financial rules"
          onClick={() => onNavigate('contracts')}
        />
        <StatCard
          label="Subject Proofs"
          value={
            proofsCount !== null
              ? String(proofsCount)
              : systemStatus?.database === 'connected'
                ? 'API err'
                : 'DB offline'
          }
          sub={`Subject: ${workspaceSubject}`}
          onClick={() => onNavigate('verification')}
        />
        <StatCard
          label="Evidence Documents"
          value={
            docsCount !== null
              ? String(docsCount)
              : systemStatus?.database === 'connected'
                ? 'API err'
                : 'DB offline'
          }
          sub="SHA-256 verified files"
          onClick={() => onNavigate('documents')}
        />
        <StatCard
          label="HTTP Requests"
          value={String(systemStatus?.metrics?.counters?.['http_requests_total'] ?? 0)}
          sub={`DB: ${systemStatus?.database ?? 'unknown'}${systemStatus?.alembic_revision ? ` · ${systemStatus.alembic_revision}` : ''}`}
          onClick={() => onNavigate('audit')}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <section className="lg:col-span-5 bg-white border border-[#0B1F3A]/20 rounded-xl p-5 distill-card space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <div>
              <div className="text-[11px] font-mono-tabular font-bold text-[#0B1F3A]">
                CANONICAL DETERMINISTIC SEED
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Live state from <code className="font-mono-tabular">/api/demo/state</code>
              </p>
            </div>
            <button
              type="button"
              onClick={() => void resetDemo()}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#0B1F3A] text-white text-xs font-medium hover:bg-[#14335c]"
            >
              <Play className="w-3.5 h-3.5" />
              Reset Seed
            </button>
          </div>

          {demoState ? (
            <div className="grid grid-cols-2 gap-2.5 text-xs font-mono-tabular">
              <div className="p-2.5 rounded bg-[#FAF9F6] border border-slate-200">
                <div className="text-slate-500">Seed</div>
                <div className="font-bold text-[#0B1F3A] mt-0.5">{String(demoState.seed)}</div>
              </div>
              <div className="p-2.5 rounded bg-[#FAF9F6] border border-slate-200">
                <div className="text-slate-500">Simulation ID</div>
                <div className="font-bold text-[#0B1F3A] mt-0.5 truncate">{String(demoState.simulation_id)}</div>
              </div>
              <div className="p-2.5 rounded bg-[#FAF9F6] border border-slate-200">
                <div className="text-slate-500">Contract ID</div>
                <div className="font-bold text-[#0B1F3A] mt-0.5 truncate">{String(demoState.contract_id)}</div>
              </div>
              <div className="p-2.5 rounded bg-[#FAF9F6] border border-slate-200">
                <div className="text-slate-500">Payment ID</div>
                <div className="font-bold text-[#0B1F3A] mt-0.5 truncate">{String(demoState.payment_id)}</div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 font-mono-tabular">Loading canonical state…</div>
          )}

          <div className="flex flex-wrap gap-2 pt-1">
            <button
              type="button"
              onClick={() => onNavigate('simulations')}
              className="px-3 py-1.5 rounded border border-[#0B1F3A]/25 text-xs font-medium text-[#0B1F3A] hover:bg-slate-50"
            >
              Open Simulations →
            </button>
            <button
              type="button"
              onClick={() => onNavigate('analysis')}
              className="px-3 py-1.5 rounded border border-[#0B1F3A]/25 text-xs font-medium text-[#0B1F3A] hover:bg-slate-50"
            >
              Blast Radius &amp; Guardian →
            </button>
          </div>
        </section>

        <section className="lg:col-span-4 bg-white border border-[#0B1F3A]/20 rounded-xl overflow-hidden distill-card">
          <div className="px-5 py-3.5 border-b border-slate-200 flex items-center justify-between">
            <h2 className="text-xs font-mono-tabular font-bold text-[#0B1F3A]">
              RECENT AUDIT STREAM
            </h2>
            <button
              type="button"
              onClick={() => onNavigate('audit')}
              className="text-xs text-[#0B1F3A] hover:underline font-medium"
            >
              View all
            </button>
          </div>
          {audits.length === 0 ? (
            <div className="p-5 text-xs text-slate-600 leading-relaxed">
              {systemStatus?.database === 'connected'
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
                      <span className="font-mono-tabular font-medium text-[#0B1F3A] truncate">
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
            note="Every platform module separates deterministic financial arithmetic from read-only advisory diagnostics."
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
      className="text-left bg-white border border-[#0B1F3A]/20 rounded-xl p-4 distill-card hover:border-[#0B1F3A] transition-colors"
    >
      <div className="text-[11px] font-mono-tabular uppercase tracking-wider text-slate-500">
        {label}
      </div>
      <div className="mt-2 text-2xl font-bold font-mono-tabular text-[#0B1F3A]">
        {value}
      </div>
      <div className="mt-1 text-xs text-slate-500 truncate">{sub}</div>
    </button>
  )
}
