import React, { useEffect, useState } from 'react'
import { Bot, ShieldCheck, TriangleAlert } from 'lucide-react'
import {
  platformApi,
  type BlastRadiusResult,
  type GuardianAuditRecord,
  type GuardianEvaluateResponse,
  type InvestigationResponse,
} from '../api/platform'
import { MarginProofCard } from '../components/MarginProofCard'
import { SectionHeader } from '../components/SectionHeader'
import { StatusBadge } from '../components/StatusBadge'

interface AnalysisGuardianSectionProps {
  persistResults?: boolean
}

export function AnalysisGuardianSection({
  persistResults = true,
}: AnalysisGuardianSectionProps) {
  const [sourceText, setSourceText] = useState(
    'Customer refund must not exceed the original payment amount.',
  )
  const [paymentAmount, setPaymentAmount] = useState('1000.00')
  const [refundAmount, setRefundAmount] = useState('1450.00')
  const [currency, setCurrency] = useState('USD')
  const [blastResult, setBlastResult] = useState<BlastRadiusResult | null>(null)

  const [violationSummary, setViolationSummary] = useState(
    'Refund exceeded original captured payment by 450.00 USD due to duplicate retry without idempotency key.',
  )
  const [investigation, setInvestigation] = useState<InvestigationResponse | null>(null)

  const [operation, setOperation] = useState('refund')
  const [actorId, setActorId] = useState('ops-service-01')
  const [amountMinor, setAmountMinor] = useState(25000)
  const [paymentAmountMinor, setPaymentAmountMinor] = useState(50000)
  const [duplicateDetected, setDuplicateDetected] = useState(false)
  const [guardianRes, setGuardianRes] = useState<GuardianEvaluateResponse | null>(null)
  const [guardianAudits, setGuardianAudits] = useState<GuardianAuditRecord[]>([])

  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const loadAudits = async () => {
    try {
      setGuardianAudits(await platformApi.listGuardianAudit())
    } catch {
      // ignore if database unreachable
    }
  }

  useEffect(() => {
    void loadAudits()
  }, [])

  const handleBlastRadius = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const res = await platformApi.analyzeBlastRadius({
        source_text: sourceText,
        payment_amount: paymentAmount,
        refund_amount: refundAmount,
        currency,
        persist: persistResults,
      })
      setBlastResult(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Blast radius calculation failed.')
    } finally {
      setBusy(false)
    }
  }

  const handleInvestigation = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const res = await platformApi.runInvestigation({
        violation_summary: violationSummary,
      })
      setInvestigation(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Investigation failed.')
    } finally {
      setBusy(false)
    }
  }

  const handleGuardianEvaluate = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const res = await platformApi.evaluateGuardian({
        operation,
        actor_id: actorId,
        amount_minor: amountMinor,
        payment_amount_minor: paymentAmountMinor,
        currency,
        actor_authorized: true,
        operation_authorized: true,
        duplicate_detected: duplicateDetected,
        state_transition_valid: true,
        requires_manual_review: false,
        persist_audit: persistResults,
      })
      setGuardianRes(res)
      await loadAudits()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Guardian evaluation failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Section 6.0 // Monetary Exposure, AI Advisory & Runtime Policy"
        title={
          <>
            Blast Radius, AI Investigation &amp; Guardian (<span className="math-var">E<sub>max</sub></span>)
          </>
        }
        description="Quantify exact Decimal exposure, execute read-only AI root-cause inspection (advisory only), and enforce pre-settlement ALLOW / BLOCK / REVIEW boundaries."
      />

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-xs text-rose-800">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-12 items-start">
        <form
          onSubmit={handleBlastRadius}
          className="lg:col-span-5 bg-white border border-[#0B1F3A]/20 rounded-xl p-5 distill-card space-y-4"
        >
          <div className="flex items-center gap-2 text-xs font-mono-tabular font-bold text-[#0B1F3A] pb-2.5 border-b border-slate-200">
            <TriangleAlert className="w-4 h-4 text-rose-600" />
            <span>FINANCIAL BLAST RADIUS</span>
          </div>
          <div>
            <label className="block text-[11px] font-mono-tabular text-slate-600 mb-1">
              Contract Policy Rule
            </label>
            <input
              type="text"
              value={sourceText}
              onChange={(e) => setSourceText(e.target.value)}
              className="w-full rounded-lg border border-[#0B1F3A]/25 bg-[#FAF9F6] px-3 py-2 text-xs"
            />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] font-mono-tabular text-slate-600 mb-1">
                Payment
              </label>
              <input
                type="text"
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value)}
                className="w-full rounded-lg border border-[#0B1F3A]/25 bg-[#FAF9F6] px-3 py-2 text-xs font-mono-tabular"
              />
            </div>
            <div>
              <label className="block text-[11px] font-mono-tabular text-slate-600 mb-1">
                Refund
              </label>
              <input
                type="text"
                value={refundAmount}
                onChange={(e) => setRefundAmount(e.target.value)}
                className="w-full rounded-lg border border-[#0B1F3A]/25 bg-[#FAF9F6] px-3 py-2 text-xs font-mono-tabular"
              />
            </div>
            <div>
              <label className="block text-[11px] font-mono-tabular text-slate-600 mb-1">Currency</label>
              <input
                type="text"
                value={currency}
                onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                maxLength={3}
                className="w-full rounded-lg border border-[#0B1F3A]/25 bg-[#FAF9F6] px-3 py-2 text-xs font-mono-tabular"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-md bg-[#0B1F3A] px-4 py-2 text-xs font-medium text-white hover:bg-[#14335c] disabled:opacity-50"
          >
            Calculate Exposure
          </button>

          {blastResult && (
            <div className="rounded-lg border border-[#0B1F3A]/20 bg-[#FAF9F6] p-4 space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-mono-tabular font-bold text-[#0B1F3A]">EXPOSURE VERDICT</span>
                <StatusBadge value={blastResult.passed ? 'passed' : 'failed'} />
              </div>
              <div className="grid grid-cols-3 gap-2 font-mono-tabular">
                <div>
                  <span className="text-slate-500 block">Direct Loss</span>
                  <span className="text-sm font-bold text-rose-700">
                    {blastResult.total_direct_loss} {blastResult.currency}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Actual</span>
                  <span className="text-sm font-bold text-amber-700">
                    {blastResult.total_actual_exposure} {blastResult.currency}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Max</span>
                  <span className="text-sm font-bold text-[#0B1F3A]">
                    {blastResult.total_maximum_exposure} {blastResult.currency}
                  </span>
                </div>
              </div>
              {blastResult.exposures.map((exp) => (
                <div key={exp.id} className="rounded border border-slate-200 bg-white p-2">
                  <div className="font-mono-tabular font-semibold text-[#0B1F3A]">
                    {exp.field || 'contract'}: {exp.amount} {exp.currency}
                  </div>
                  <div className="text-slate-600">{exp.explanation}</div>
                </div>
              ))}
            </div>
          )}
        </form>

        <form
          onSubmit={handleInvestigation}
          className="lg:col-span-4 bg-white border border-[#0B1F3A]/20 rounded-xl p-5 distill-card space-y-4"
        >
          <div className="flex items-center justify-between pb-2.5 border-b border-slate-200">
            <div className="flex items-center gap-2 text-xs font-mono-tabular font-bold text-[#0B1F3A]">
              <Bot className="w-4 h-4 text-[#047857]" />
              <span>BOUNDED AI INVESTIGATION</span>
            </div>
            <StatusBadge value="advisory" />
          </div>
          <div>
            <label className="block text-[11px] font-mono-tabular text-slate-600 mb-1">
              Violation / Anomaly Summary
            </label>
            <textarea
              rows={3}
              value={violationSummary}
              onChange={(e) => setViolationSummary(e.target.value)}
              className="w-full rounded-lg border border-[#0B1F3A]/25 bg-[#FAF9F6] px-3 py-2 text-xs"
            />
          </div>
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-md bg-[#0B1F3A] px-4 py-2 text-xs font-medium text-white hover:bg-[#14335c] disabled:opacity-50"
          >
            Run Read-Only Investigation
          </button>

          {investigation && (
            <div className="rounded-lg border border-[#0B1F3A]/20 bg-[#FAF9F6] p-4 space-y-3 text-xs">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-mono-tabular font-bold text-[#0B1F3A]">
                  Investigation {investigation.investigation_id.slice(0, 8)}
                </span>
                <span className="rounded bg-amber-100 px-2 py-0.5 text-[10px] font-mono-tabular font-semibold text-amber-900">
                  ai_advisory_only={String(investigation.ai_advisory_only)}
                </span>
              </div>
              <p className="text-slate-800">{investigation.summary}</p>
              <div className="rounded border border-slate-200 bg-white p-2.5">
                <div className="font-mono-tabular font-bold text-[#0B1F3A] mb-1">Root Cause Hypothesis</div>
                <p className="text-slate-600">{investigation.root_cause_hypothesis}</p>
              </div>
              <ul className="list-disc pl-4 space-y-1 text-slate-700">
                {investigation.recommended_actions.map((action, idx) => (
                  <li key={idx}>{action}</li>
                ))}
              </ul>
            </div>
          )}
        </form>

        <aside className="lg:col-span-3">
          <MarginProofCard
            sectionCode="SEC. 6.0"
            badge="advisory"
            axiomLines={
              <>
                <div>ai_advisory_only = true</div>
                <div className="text-emerald-300">override_truth = false</div>
                <div className="text-amber-300">Tools: Read-Only Sandbox</div>
              </>
            }
            note="Investigation tools never mutate ledger records or override deterministic Guardian evaluations."
          />
        </aside>
      </div>

      <div className="bg-white border border-[#0B1F3A]/20 rounded-xl p-5 distill-card space-y-4">
        <div className="flex items-center gap-2 text-xs font-mono-tabular font-bold text-[#0B1F3A] pb-2.5 border-b border-slate-200">
          <ShieldCheck className="w-4 h-4 text-[#047857]" />
          <span>RUNTIME GUARDIAN POLICY GATE</span>
        </div>
        <form onSubmit={handleGuardianEvaluate} className="grid gap-3 sm:grid-cols-5 items-end">
          <div>
            <label className="block text-[11px] font-mono-tabular text-slate-600 mb-1">Operation</label>
            <input
              type="text"
              value={operation}
              onChange={(e) => setOperation(e.target.value)}
              className="w-full rounded-lg border border-[#0B1F3A]/25 bg-[#FAF9F6] px-3 py-2 text-xs font-mono-tabular"
            />
          </div>
          <div>
            <label className="block text-[11px] font-mono-tabular text-slate-600 mb-1">Actor ID</label>
            <input
              type="text"
              value={actorId}
              onChange={(e) => setActorId(e.target.value)}
              className="w-full rounded-lg border border-[#0B1F3A]/25 bg-[#FAF9F6] px-3 py-2 text-xs font-mono-tabular"
            />
          </div>
          <div>
            <label className="block text-[11px] font-mono-tabular text-slate-600 mb-1">
              Amount (minor)
            </label>
            <input
              type="number"
              value={amountMinor}
              onChange={(e) => setAmountMinor(Number(e.target.value))}
              className="w-full rounded-lg border border-[#0B1F3A]/25 bg-[#FAF9F6] px-3 py-2 text-xs font-mono-tabular"
            />
          </div>
          <div>
            <label className="block text-[11px] font-mono-tabular text-slate-600 mb-1">
              Original Payment
            </label>
            <input
              type="number"
              value={paymentAmountMinor}
              onChange={(e) => setPaymentAmountMinor(Number(e.target.value))}
              className="w-full rounded-lg border border-[#0B1F3A]/25 bg-[#FAF9F6] px-3 py-2 text-xs font-mono-tabular"
            />
          </div>
          <div className="flex items-center gap-3">
            <label className="inline-flex items-center gap-1.5 text-xs text-slate-700 font-mono-tabular">
              <input
                type="checkbox"
                checked={duplicateDetected}
                onChange={(e) => setDuplicateDetected(e.target.checked)}
                className="accent-[#0B1F3A]"
              />
              Dup
            </label>
            <button
              type="submit"
              disabled={busy}
              className="rounded-md bg-[#0B1F3A] px-4 py-2 text-xs font-medium text-white hover:bg-[#14335c] disabled:opacity-50"
            >
              Evaluate
            </button>
          </div>
        </form>

        {guardianRes && (
          <div className="rounded-lg border border-[#0B1F3A]/20 bg-[#FAF9F6] p-3 flex flex-wrap items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2">
              <StatusBadge value={guardianRes.decision} />
              <span className="font-mono-tabular font-bold text-[#0B1F3A]">
                {guardianRes.rule}
              </span>
              <span className="text-slate-600">{guardianRes.reason}</span>
            </div>
            <span className="font-mono-tabular text-slate-500">
              persisted={String(guardianRes.persisted)}
            </span>
          </div>
        )}

        {guardianAudits.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-left font-mono-tabular text-slate-500">
                  <th className="py-2 pr-3">Actor</th>
                  <th className="py-2 pr-3">Operation</th>
                  <th className="py-2 pr-3">Decision</th>
                  <th className="py-2 pr-3">Rule</th>
                  <th className="py-2">Reason</th>
                </tr>
              </thead>
              <tbody>
                {guardianAudits.slice(0, 10).map((rec) => (
                  <tr key={rec.id} className="border-b border-slate-100">
                    <td className="py-2 pr-3 font-mono-tabular">{rec.actor_id || '-'}</td>
                    <td className="py-2 pr-3 font-mono-tabular">{rec.operation}</td>
                    <td className="py-2 pr-3">
                      <StatusBadge value={rec.decision} />
                    </td>
                    <td className="py-2 pr-3 font-mono-tabular">{rec.rule}</td>
                    <td className="py-2 text-slate-600">{rec.reason}</td>
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
