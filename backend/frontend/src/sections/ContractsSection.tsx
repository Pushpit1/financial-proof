import React, { useEffect, useState } from 'react'
import { CheckCircle2, FileCode2, Save } from 'lucide-react'
import {
  compileContract,
  createContract,
  evaluateContract,
} from '../api/contracts'
import { platformApi } from '../api/platform'
import type { FinancialContract, FinancialContractDecision } from '../types/contract'
import { StatusBadge } from '../components/StatusBadge'

export function ContractsSection() {
  const [ruleText, setRuleText] = useState(
    'Customer refund must not exceed the original payment amount.',
  )
  const [compiled, setCompiled] = useState<FinancialContract | null>(null)
  const [contracts, setContracts] = useState<FinancialContract[]>([])
  const [decision, setDecision] = useState<FinancialContractDecision | null>(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const loadContracts = async () => {
    try {
      setContracts(await platformApi.listContracts())
    } catch {
      // ignore if DB unavailable; error banner handles status
    }
  }

  useEffect(() => {
    void loadContracts()
  }, [])

  const handleCompile = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const res = await compileContract({ source_text: ruleText.trim() })
      setCompiled(res.contract)
      setMessage('Contract rule compiled deterministically.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Compilation failed.')
    } finally {
      setBusy(false)
    }
  }

  const handlePersist = async () => {
    if (!compiled) return
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const saved = await createContract({
        name: compiled.name,
        version: compiled.version,
        minimum_confidence: Number(compiled.minimum_confidence),
        minimum_supported_claim_ratio: Number(compiled.minimum_supported_claim_ratio),
        required_claim_types:
          compiled.required_claim_types.length > 0
            ? compiled.required_claim_types
            : ['transaction'],
      })
      setCompiled(saved)
      setMessage(`Persisted contract ${saved.name} v${saved.version}.`)
      await loadContracts()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to persist contract.')
    } finally {
      setBusy(false)
    }
  }

  const handleEvaluate = async (contractId: string) => {
    setError('')
    setMessage('')
    try {
      const res = await evaluateContract(contractId, {
        context: { transaction_present: true, confidence: 0.9 },
      })
      setDecision(res)
      setMessage(`Evaluated contract decision: ${res.passed ? 'PASSED' : 'FAILED'}.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Contract evaluation failed.')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-slate-900">
          Financial Contracts & Deterministic Compiler
        </h1>
        <p className="text-sm text-slate-600 mt-0.5">
          Compile natural-language business rules into immutable versioned contracts and evaluate compliance.
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-md border border-rose-200 bg-rose-50 text-rose-800 text-xs">
          {error}
        </div>
      )}
      {message && (
        <div className="p-3 rounded-md border border-emerald-200 bg-emerald-50 text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <form
          onSubmit={handleCompile}
          className="lg:col-span-5 bg-white border border-slate-200 rounded-lg p-5 space-y-4"
        >
          <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <FileCode2 className="w-4 h-4 text-[#1E3A5F]" /> Compile Financial Rule
          </h2>
          <textarea
            rows={5}
            value={ruleText}
            onChange={(e) => setRuleText(e.target.value)}
            required
            className="w-full px-3 py-2 rounded border border-slate-300 text-sm focus:outline-none focus:border-[#1E3A5F]"
          />
          <div className="flex flex-wrap gap-2">
            <button
              type="submit"
              disabled={busy}
              className="px-4 py-2 rounded bg-[#1E3A5F] text-white text-xs font-medium hover:bg-[#162C49] disabled:opacity-50"
            >
              Compile Rule
            </button>
            {compiled && (
              <button
                type="button"
                disabled={busy}
                onClick={() => void handlePersist()}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded border border-slate-300 bg-white text-xs font-medium text-slate-800 hover:bg-slate-50"
              >
                <Save className="w-3.5 h-3.5" />
                Save to Database
              </button>
            )}
          </div>

          {compiled && (
            <div className="p-3.5 rounded bg-slate-50 border border-slate-200 text-xs space-y-1.5 font-mono-tabular">
              <div className="font-semibold text-slate-900">{compiled.name}</div>
              <div>Version: v{compiled.version}</div>
              <div>Min Confidence: {String(compiled.minimum_confidence)}</div>
              <div>Min Claim Ratio: {String(compiled.minimum_supported_claim_ratio)}</div>
              <div>Required Claims: {compiled.required_claim_types.join(', ') || 'none'}</div>
            </div>
          )}
        </form>

        <div className="lg:col-span-7 bg-white border border-slate-200 rounded-lg overflow-hidden">
          <div className="px-5 py-3.5 border-b border-slate-200 text-sm font-semibold">
            Persisted Contracts ({contracts.length})
          </div>
          {contracts.length === 0 ? (
            <div className="p-6 text-xs text-slate-500">
              No persisted contracts loaded yet. Compile and save a rule (requires connected database).
            </div>
          ) : (
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4 font-medium">Name</th>
                  <th className="py-2.5 px-4 font-medium">Ver</th>
                  <th className="py-2.5 px-4 font-medium">Min Conf</th>
                  <th className="py-2.5 px-4 font-medium text-right">Evaluate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {contracts.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50">
                    <td className="py-2.5 px-4 font-medium text-slate-900">{c.name}</td>
                    <td className="py-2.5 px-4 font-mono-tabular">v{c.version}</td>
                    <td className="py-2.5 px-4 font-mono-tabular">{String(c.minimum_confidence)}</td>
                    <td className="py-2.5 px-4 text-right">
                      <button
                        type="button"
                        onClick={() => void handleEvaluate(c.id)}
                        className="px-2.5 py-1 rounded bg-[#1E3A5F] text-white text-[11px] hover:bg-[#162C49]"
                      >
                        Evaluate Decision
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {decision && (
            <div className="m-4 p-3 rounded border border-slate-200 bg-slate-50 text-xs flex items-center justify-between">
              <span className="font-mono-tabular">
                Decision {decision.id.slice(0, 8)} · violations: {decision.violation_count}
              </span>
              <StatusBadge value={decision.passed ? 'passed' : 'failed'} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
