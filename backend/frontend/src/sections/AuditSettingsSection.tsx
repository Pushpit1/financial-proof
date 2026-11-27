import React, { useEffect, useState } from 'react'
import { History, KeyRound, RefreshCw } from 'lucide-react'
import { getAuthToken, setAuthToken } from '../api/client'
import { platformApi, type AuditEvent, type AuthStatus } from '../api/platform'
import { MarginProofCard } from '../components/MarginProofCard'
import { SectionHeader } from '../components/SectionHeader'
import { StatusBadge } from '../components/StatusBadge'

const CATEGORIES = ['', 'contract', 'simulation', 'guardian', 'evidence']

export function AuditSettingsSection() {
  const [category, setCategory] = useState('')
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null)
  const [tokenInput, setTokenInput] = useState(() => getAuthToken())
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const refreshAll = async (selectedCategory = category) => {
    setBusy(true)
    setError('')
    try {
      const [auditRes, authRes] = await Promise.all([
        platformApi.listAudit(selectedCategory || undefined),
        platformApi.authStatus(),
      ])
      setEvents(auditRes)
      setAuthStatus(authRes)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit and auth state.')
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    void refreshAll()
  }, [])

  const handleSaveToken = async (e: React.FormEvent) => {
    e.preventDefault()
    setAuthToken(tokenInput)
    setMessage(
      tokenInput.trim()
        ? 'Bearer token updated in browser session.'
        : 'Bearer token cleared from browser session.',
    )
    await refreshAll()
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Section 7.0 // Fail-Closed Security & Audit Governance"
        title="Unified Audit Stream & Access Controls"
        description="Inspect persisted contracts, simulations, Guardian gates, and evidence events alongside live Bearer authentication status."
        rightSlot={
          <button
            type="button"
            onClick={() => void refreshAll()}
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-md border border-[#0B1F3A]/25 bg-white px-3.5 py-2 text-xs font-medium text-[#0B1F3A] hover:bg-slate-50"
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
      {message && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs text-emerald-800">
          {message}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-12 items-start">
        <div className="lg:col-span-9 space-y-6">
          <div className="bg-white border border-[#0B1F3A]/20 rounded-xl p-5 distill-card space-y-4">
            <div className="flex items-center justify-between pb-2.5 border-b border-slate-200">
              <div className="flex items-center gap-2 text-xs font-mono-tabular font-bold text-[#0B1F3A]">
                <KeyRound className="w-4 h-4 text-[#047857]" />
                <span>API BEARER TOKEN &amp; AUTH STATUS</span>
              </div>
              {authStatus && (
                <StatusBadge value={authStatus.authenticated ? 'verified' : 'advisory'} />
              )}
            </div>
            {authStatus && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono-tabular">
                <div className="p-2.5 rounded bg-[#FAF9F6] border border-slate-200">
                  <span className="text-slate-500 block">Auth Enforced</span>
                  <span className="font-bold text-[#0B1F3A]">
                    {String(authStatus.auth_configured)}
                  </span>
                </div>
                <div className="p-2.5 rounded bg-[#FAF9F6] border border-slate-200">
                  <span className="text-slate-500 block">Authenticated</span>
                  <span className="font-bold text-[#0B1F3A]">
                    {String(authStatus.authenticated)}
                  </span>
                </div>
                <div className="p-2.5 rounded bg-[#FAF9F6] border border-slate-200">
                  <span className="text-slate-500 block">Subject</span>
                  <span className="font-bold text-[#0B1F3A]">
                    {authStatus.subject || 'anonymous'}
                  </span>
                </div>
                <div className="p-2.5 rounded bg-[#FAF9F6] border border-slate-200">
                  <span className="text-slate-500 block">Role</span>
                  <span className="font-bold text-[#0B1F3A]">{authStatus.role || '-'}</span>
                </div>
              </div>
            )}
            <form onSubmit={handleSaveToken} className="flex flex-wrap gap-3">
              <input
                type="password"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder="Optional API Bearer token"
                className="flex-1 min-w-[240px] rounded-lg border border-[#0B1F3A]/25 bg-[#FAF9F6] px-3 py-2 text-xs font-mono-tabular"
              />
              <button
                type="submit"
                className="rounded-md bg-[#0B1F3A] px-4 py-2 text-xs font-medium text-white hover:bg-[#14335c]"
              >
                Apply &amp; Test Token
              </button>
            </form>
          </div>

          <div className="bg-white border border-[#0B1F3A]/20 rounded-xl p-5 distill-card space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-2.5 border-b border-slate-200">
              <div className="flex items-center gap-2 text-xs font-mono-tabular font-bold text-[#0B1F3A]">
                <History className="w-4 h-4 text-[#047857]" />
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
                    className={`rounded px-2.5 py-1 text-xs font-mono-tabular border ${
                      category === cat
                        ? 'bg-[#0B1F3A] text-white border-[#0B1F3A]'
                        : 'bg-[#FAF9F6] text-[#0B1F3A] border-[#0B1F3A]/25 hover:bg-slate-100'
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
                        <td className="py-2 pr-3 text-[#0B1F3A]">{ev.summary}</td>
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
            badge={authStatus?.auth_configured ? 'verified' : 'advisory'}
            axiomLines={
              <>
                <div>Auth: Fail-Closed Bearer</div>
                <div className="text-emerald-300">CSP / X-Frame: DENY</div>
                <div className="text-amber-300">Secrets: Server-Side Only</div>
              </>
            }
            note="Tokens entered here remain strictly in your session header and are never persisted into source artifacts."
          />
        </aside>
      </div>
    </div>
  )
}
