import React, { useEffect, useState } from 'react'
import { CheckCircle2, FileCode2, Save } from 'lucide-react'
import {
  compileContract,
  createContract,
  evaluateContract,
} from '../api/contracts'
import { platformApi } from '../api/platform'
import type { FinancialContract, FinancialContractDecision } from '../types/contract'
import { MarginProofCard } from '../components/MarginProofCard'
import { SectionHeader } from '../components/SectionHeader'
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
      // ignore if DB unavailable
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
      <SectionHeader
        eyebrow="Section 2.0 // Rule Compilation & Invariant Schema"
        title={
          <>
            Financial Contracts &amp; Compiler (<span className="math-var">R(t) ≤ C(t)</span>)
          </>
        }
        description="Compile natural-language business constraints into versioned deterministic invariants and evaluate compliance against execution context."
      />

      {error && (
        <div className="p-3 rounded-lg border border-rose-200 bg-rose-50 text-rose-800 text-xs">
          {error}
        </div>
      )}
      {message && (
        <div className="p-3 rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <form
          onSubmit={handleCompile}
          className="lg:col-span-5 bg-white border border-[#C5C4B1] rounded-xl p-5 distill-card space-y-4"
        >
          <div className="text-xs font-mono-tabular font-bold text-[#191919] flex items-center gap-2 pb-2.5 border-b border-slate-200">
            <FileCode2 className="w-4 h-4 text-[#FF6170]" /> COMPILE FINANCIAL RULE
          </div>
          <textarea
            rows={5}
            value={ruleText}
            onChange={(e) => setRuleText(e.target.value)}
            required
            className="w-full px-3 py-2 rounded-lg border border-[#C5C4B1] bg-[#F5F5F3] text-sm focus:outline-none focus:border-[#191919]"
          />
          <div className="flex flex-wrap gap-2">
            <button
              type="submit"
              disabled={busy}
              className="px-4 py-2 rounded-md bg-[#191919] text-white text-xs font-medium hover:bg-[#2D2D2D] disabled:opacity-50"
            >
              Compile Rule
            </button>
            {compiled && (
              <button
                type="button"
                disabled={busy}
                onClick={() => void handlePersist()}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md border border-[#C5C4B1] bg-white text-xs font-medium text-[#191919] hover:bg-slate-50"
              >
                <Save className="w-3.5 h-3.5" />
                Save to Database
              </button>
            )}
          </div>

          {compiled && (
            <div className="p-3.5 rounded-lg bg-[#F5F5F3] border border-[#C5C4B1] text-xs space-y-1.5 font-mono-tabular">
              <div className="font-bold text-[#191919]">{compiled.name}</div>
              <div>Version: v{compiled.version}</div>
              <div>Min Confidence: {String(compiled.minimum_confidence)}</div>
              <div>Min Claim Ratio: {String(compiled.minimum_supported_claim_ratio)}</div>
              <div>Required Claims: {compiled.required_claim_types.join(', ') || 'none'}</div>
            </div>
          )}
        </form>

        <div className="lg:col-span-4 bg-white border border-[#C5C4B1] rounded-xl overflow-hidden distill-card">
          <div className="px-5 py-3.5 border-b border-slate-200 text-xs font-mono-tabular font-bold text-[#191919]">
            PERSISTED CONTRACTS ({contracts.length})
          </div>
          {contracts.length === 0 ? (
            <div className="p-6 text-xs text-slate-600 leading-relaxed">
              No persisted contracts loaded yet. Rule compilation works statelessly; saving contracts requires a connected PostgreSQL database.
            </div>
          ) : (
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F5F5F3] text-slate-500 border-b border-slate-200 font-mono-tabular">
                <tr>
                  <th className="py-2.5 px-4 font-medium">Name</th>
                  <th className="py-2.5 px-4 font-medium">Ver</th>
                  <th className="py-2.5 px-4 font-medium text-right">Evaluate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {contracts.map((c) => (
                  <tr key={c.id} className="hover:bg-[#F5F5F3]">
                    <td className="py-2.5 px-4 font-medium text-[#191919]">{c.name}</td>
                    <td className="py-2.5 px-4 font-mono-tabular">v{c.version}</td>
                    <td className="py-2.5 px-4 text-right">
                      <button
                        type="button"
                        onClick={() => void handleEvaluate(c.id)}
                        className="px-2.5 py-1 rounded bg-[#191919] text-white text-[11px] hover:bg-[#2D2D2D]"
                      >
                        Evaluate
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {decision && (
            <div className="m-4 p-3 rounded border border-slate-200 bg-[#F5F5F3] text-xs flex items-center justify-between">
              <span className="font-mono-tabular">
                Decision {decision.id.slice(0, 8)} · violations: {decision.violation_count}
              </span>
              <StatusBadge value={decision.passed ? 'passed' : 'failed'} />
            </div>
          )}
        </div>

        <aside className="lg:col-span-3">
          <MarginProofCard
            sectionCode="SEC. 2.0"
            axiomLines={
              <>
                <div>Compile(rule) → TypedAST</div>
                <div className="text-emerald-300">Ambiguity: 0 (Deterministic)</div>
                <div className="text-amber-300">Version Lock: Immutable</div>
              </>
            }
            note="Natural-language policies map deterministically to FinancialConstraint checks without probabilistic rewriting."
          />
        </aside>
      </div>
    </div>
  )
}
