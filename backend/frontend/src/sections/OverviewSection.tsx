import { useEffect, useState } from 'react'
import { Play, RefreshCw } from 'lucide-react'
import { apiClient } from '../api/client'
import { platformApi, type AuditEvent, type SystemStatus } from '../api/platform'
import type { NavSection } from '../components/AppShell'
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
        const [c, p, d, a] = await Promise.all([
          platformApi.listContracts(),
          platformApi.listProofsBySubject(workspaceSubject),
          platformApi.listDocuments(),
          platformApi.listAudit(),
        ])
        setContractsCount(c.length)
        setProofsCount(p.length)
        setDocsCount(d.length)
        setAudits(a.slice(0, 8))
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
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">
            Platform Overview
          </h1>
          <p className="text-sm text-slate-600 mt-0.5">
            Real-time deterministic verification telemetry for <code className="font-mono-tabular">{workspaceSubject}</code>.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            void onRefreshSystem()
            void loadOverview()
          }}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-slate-200 bg-white text-xs font-medium text-slate-700 hover:bg-slate-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh State
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-md border border-rose-200 bg-rose-50 text-rose-800 text-xs">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Persisted Contracts"
          value={contractsCount === null ? 'DB offline' : String(contractsCount)}
          sub="Versioned financial rules"
          onClick={() => onNavigate('contracts')}
        />
        <StatCard
          label="Subject Proofs"
          value={proofsCount === null ? 'DB offline' : String(proofsCount)}
          sub={`Subject: ${workspaceSubject}`}
          onClick={() => onNavigate('verification')}
        />
        <StatCard
          label="Evidence Documents"
          value={docsCount === null ? 'DB offline' : String(docsCount)}
          sub="SHA-256 verified files"
          onClick={() => onNavigate('documents')}
        />
        <StatCard
          label="HTTP Requests"
          value={String(systemStatus?.metrics?.counters?.['http_requests_total'] ?? 0)}
          sub={`DB status: ${systemStatus?.database ?? 'unknown'}`}
          onClick={() => onNavigate('audit')}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <section className="lg:col-span-6 bg-white border border-slate-200 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">
                Canonical Deterministic Seed
              </h2>
              <p className="text-xs text-slate-500">
                Live state from <code className="font-mono-tabular">/api/demo/state</code>
              </p>
            </div>
            <button
              type="button"
              onClick={() => void resetDemo()}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#1E3A5F] text-white text-xs font-medium hover:bg-[#162C49]"
            >
              <Play className="w-3.5 h-3.5" />
              Reset Seed
            </button>
          </div>

          {demoState ? (
            <div className="grid grid-cols-2 gap-2.5 text-xs font-mono-tabular">
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <div className="text-slate-500">Seed</div>
                <div className="font-semibold mt-0.5">{String(demoState.seed)}</div>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <div className="text-slate-500">Simulation ID</div>
                <div className="font-semibold mt-0.5 truncate">{String(demoState.simulation_id)}</div>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <div className="text-slate-500">Contract ID</div>
                <div className="font-semibold mt-0.5 truncate">{String(demoState.contract_id)}</div>
              </div>
              <div className="p-2.5 rounded bg-slate-50 border border-slate-200">
                <div className="text-slate-500">Payment ID</div>
                <div className="font-semibold mt-0.5 truncate">{String(demoState.payment_id)}</div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-500">Loading canonical state…</div>
          )}

          <div className="flex flex-wrap gap-2 pt-1">
            <button
              type="button"
              onClick={() => onNavigate('simulations')}
              className="px-3 py-1.5 rounded border border-slate-200 text-xs font-medium hover:bg-slate-50"
            >
              Open Simulations →
            </button>
            <button
              type="button"
              onClick={() => onNavigate('analysis')}
              className="px-3 py-1.5 rounded border border-slate-200 text-xs font-medium hover:bg-slate-50"
            >
              Run Blast Radius & Guardian →
            </button>
          </div>
        </section>

        <section className="lg:col-span-6 bg-white border border-slate-200 rounded-lg overflow-hidden">
          <div className="px-5 py-3.5 border-b border-slate-200 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-900">Recent Persisted Audit Events</h2>
            <button
              type="button"
              onClick={() => onNavigate('audit')}
              className="text-xs text-[#1E3A5F] hover:underline font-medium"
            >
              View all
            </button>
          </div>
          {audits.length === 0 ? (
            <div className="p-5 text-xs text-slate-500">
              {systemStatus?.database === 'connected'
                ? 'No audit events recorded yet. Run a Guardian check, Contract decision, or Proof evaluation.'
                : 'Audit persistence requires a connected database.'}
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {audits.map((ev) => (
                <div key={ev.id} className="px-5 py-2.5 flex items-center justify-between gap-2 text-xs">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <StatusBadge value={ev.category} />
                      <span className="font-mono-tabular font-medium text-slate-900 truncate">
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
      className="text-left bg-white border border-slate-200 rounded-lg p-4 hover:border-slate-300 transition-colors"
    >
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div className="mt-2 text-2xl font-semibold font-mono-tabular text-slate-900">
        {value}
      </div>
      <div className="mt-1 text-xs text-slate-500 truncate">{sub}</div>
    </button>
  )
}
