import React, { useState } from 'react'
import { getAuthToken, setAuthToken } from '../api/client'
import { platformApi, type AuthStatus } from '../api/platform'

interface SignInModalProps {
  open: boolean
  initialEmail: string
  onClose: () => void
  onSignedIn: (email: string, authStatus?: AuthStatus) => void
}

export function SignInModal({ open, initialEmail, onClose, onSignedIn }: SignInModalProps) {
  const [email, setEmail] = useState(initialEmail || 'principal@financialproof.dev')
  const [token, setToken] = useState(() => getAuthToken())
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  if (!open) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      setAuthToken(token.trim())
      let status: AuthStatus | undefined
      try {
        status = await platformApi.authStatus()
      } catch {
        // Proceed smoothly if running offline or guest mode without server token requirement
      }
      onSignedIn(email.trim() || 'operator@financialproof.dev', status)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to apply session credentials.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/45 backdrop-blur-xs flex items-center justify-center p-4">
      <form
        onSubmit={(e) => void handleSubmit(e)}
        className="bg-white border border-[#C5C4B1] alloy-card p-6 max-w-md w-full space-y-4 shadow-2xl"
      >
        <div className="flex items-center justify-between pb-3 border-b border-[#191919]/10">
          <div>
            <span className="t-pill">OPERATOR ACCESS</span>
            <h3 className="text-xl font-medium mt-1.5 text-[#191919]">Sign in to Financial Proof</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-2.5 py-1 text-xs font-mono-tabular border border-[#C5C4B1] rounded cursor-pointer hover:border-[#191919]"
          >
            ESC
          </button>
        </div>

        <div className="space-y-3 text-xs">
          <div>
            <label className="block font-medium mb-1 text-[#191919]">Operator Email / Subject</label>
            <input
              type="text"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="alloy-input font-mono-tabular"
              placeholder="principal@financialproof.dev"
            />
          </div>
          <div>
            <label className="block font-medium mb-1 text-[#191919]">
              Bearer API Token <span className="text-[#191919]/50">(Optional · leave blank for open demo)</span>
            </label>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              className="alloy-input font-mono-tabular"
              placeholder="fp_live_..."
            />
          </div>
          {error && <div className="text-xs text-[#FF6170] font-mono-tabular">{error}</div>}
        </div>

        <div className="flex flex-wrap gap-2 pt-2">
          <button type="submit" disabled={busy} className="alloy-btn alloy-btn-filled flex-1">
            {busy ? 'Verifying...' : 'Sign In & Launch ->'}
          </button>
          <button type="button" onClick={onClose} className="alloy-btn alloy-btn-outline">
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
