import { useEffect, useState } from 'react'
import { History, RefreshCw } from 'lucide-react'
import { platformApi, type AuditEvent } from '../api/platform'
import { MarginProofCard } from '../components/MarginProofCard'
import { SectionHeader } from '../components/SectionHeader'
import { StatusBadge } from '../components/StatusBadge'

const CATEGORIES = ['', 'contract', 'simulation', 'guardian', 'evidence', 'proof']

export function AuditSettingsSection() {
  const [category, setCategory] = useState('')
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const refreshAll = async (selectedCategory = category) => {
    setBusy(true)
    setError('')
    try {
      const auditRes = await platformApi.listAudit(selectedCategory || undefined)
      setEvents(auditRes)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit stream.')
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    void refreshAll()
  }, [])

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Section 7.0 // Fail-Closed Security & Audit Governance"
        title="Unified Audit Stream"
        description="Inspect persisted contracts, simulations, Guardian gates, proof evaluations, and evidence events from PostgreSQL."
        rightSlot={
          <button
            type="button"
            onClick={() => void refreshAll()}
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-md border border-[#C5C4B1] bg-white px-3.5 py-2 text-xs font-medium text-[#191919] hover:bg-slate-50 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${busy ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        }
      />

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-xs text-rose-800">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-12 items-start">
        <div className="lg:col-span-9">
          <div className="bg-white border border-[#C5C4B1] rounded-xl p-5 distill-card space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-2.5 border-b border-slate-200">
              <div className="flex items-center gap-2 text-xs font-mono-tabular font-bold text-[#191919]">
                <History className="w-4 h-4 text-[#FF6170]" />
                <span>UNIFIED AUDIT STREAM ({events.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat || 'all'}
                    type="button"
                    onClick={() => {
                      setCategory(cat)
                      void refreshAll(cat)
                    }}
                    className={`rounded px-2.5 py-1 text-xs font-mono-tabular border cursor-pointer ${
                      category === cat
                        ? 'bg-[#191919] text-white border-[#191919]'
                        : 'bg-[#F5F5F3] text-[#191919] border-[#C5C4B1] hover:bg-slate-100'
                    }`}
                  >
                    {cat || 'all'}
                  </button>
                ))}
              </div>
            </div>

            {events.length === 0 ? (
              <p className="text-xs text-slate-500">
                No persisted audit events match this filter yet.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-left font-mono-tabular text-slate-500">
                      <th className="py-2 pr-3">Category</th>
                      <th className="py-2 pr-3">Action</th>
                      <th className="py-2 pr-3">Summary</th>
                      <th className="py-2">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {events.map((ev) => (
                      <tr key={`${ev.category}-${ev.id}`} className="border-b border-slate-100">
                        <td className="py-2 pr-3">
                          <StatusBadge value={ev.category} />
                        </td>
                        <td className="py-2 pr-3 font-mono-tabular">{ev.action}</td>
                        <td className="py-2 pr-3 text-[#191919]">{ev.summary}</td>
                        <td className="py-2 font-mono-tabular text-slate-500">{ev.created_at}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        <aside className="lg:col-span-3">
          <MarginProofCard
            sectionCode="SEC. 7.0"
            badge="verified"
            axiomLines={
              <>
                <div>Audit: Append-Only Trace</div>
                <div className="text-emerald-300">CSP / X-Frame: DENY</div>
                <div className="text-amber-300">Secrets: Server-Side Only</div>
              </>
            }
            note="All contract compilations, evidence hashes, proof evaluations, and Guardian gates write immutable PostgreSQL audit records."
          />
        </aside>
      </div>
    </div>
  )
}
