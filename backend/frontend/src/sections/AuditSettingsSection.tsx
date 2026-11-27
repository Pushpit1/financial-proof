import React, { useEffect, useState } from 'react'
import { History, KeyRound, RefreshCw } from 'lucide-react'
import { getAuthToken, setAuthToken } from '../api/client'
import { platformApi, type AuditEvent, type AuthStatus } from '../api/platform'
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
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-[#0B1F3A]">
            Audit Trail & Security Access
          </h2>
          <p className="text-sm text-slate-600">
            Inspect persisted contracts, simulations, guardian gates, and evidence events alongside
            live API authentication configuration.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void refreshAll()}
          disabled={busy}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-800 hover:bg-slate-50"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          {error}
        </div>
      )}
      {message && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {message}
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-[#0B1F3A] font-semibold">
            <KeyRound className="w-4 h-4 text-emerald-600" />
            <span>API Bearer Token & Auth Status</span>
          </div>
          {authStatus && (
            <StatusBadge value={authStatus.authenticated ? 'verified' : 'advisory'} />
          )}
        </div>
        {authStatus && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <span className="text-slate-500 block">Server Auth Enforced</span>
              <span className="font-mono-tabular font-semibold">
                {String(authStatus.auth_configured)}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Session Authenticated</span>
              <span className="font-mono-tabular font-semibold">
                {String(authStatus.authenticated)}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Subject</span>
              <span className="font-mono-tabular font-semibold">
                {authStatus.subject || 'anonymous'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Role</span>
              <span className="font-mono-tabular font-semibold">{authStatus.role || '-'}</span>
            </div>
          </div>
        )}
        <form onSubmit={handleSaveToken} className="flex flex-wrap gap-3">
          <input
            type="password"
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
            placeholder="Optional API Bearer token"
            className="flex-1 min-w-[240px] rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular"
          />
          <button
            type="submit"
            className="rounded-lg bg-[#0B1F3A] px-4 py-2 text-sm font-medium text-white hover:bg-[#132f57]"
          >
            Apply & Test Token
          </button>
        </form>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-[#0B1F3A] font-semibold">
            <History className="w-4 h-4 text-emerald-600" />
            <span>Unified Audit Stream ({events.length})</span>
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
                className={`rounded-md px-2.5 py-1 text-xs font-medium border ${
                  category === cat
                    ? 'bg-[#0B1F3A] text-white border-[#0B1F3A]'
                    : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
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
                <tr className="border-b border-slate-200 text-left text-slate-500">
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
                    <td className="py-2 pr-3 text-slate-800">{ev.summary}</td>
                    <td className="py-2 font-mono-tabular text-slate-500">{ev.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
