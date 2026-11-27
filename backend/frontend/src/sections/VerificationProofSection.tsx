import React, { useState } from 'react'
import { Download, FileCheck2, Scale } from 'lucide-react'
import { verifySnapshots } from '../api/verification'
import { createProof, evaluateProof } from '../api/proofs'
import { platformApi } from '../api/platform'
import type { VerificationResponse } from '../types/verification'
import type { FinancialProofAggregate } from '../types/proof'
import { StatusBadge } from '../components/StatusBadge'

export function VerificationProofSection() {
  const [beforeNet, setBeforeNet] = useState(500)
  const [afterNet, setAfterNet] = useState(400)
  const [beforeRefunded, setBeforeRefunded] = useState(0)
  const [afterRefunded, setAfterRefunded] = useState(100)
  const [capturedAmount, setCapturedAmount] = useState(500)
  const [beforeViolations, setBeforeViolations] = useState('refund_ceiling_breach')
  const [afterViolations, setAfterViolations] = useState('')
  const [verifyResult, setVerifyResult] = useState<VerificationResponse | null>(null)

  const [subject, setSubject] = useState('merchant-settlement-q1')
  const [claimType, setClaimType] = useState('balance')
  const [claimAmount, setClaimAmount] = useState(12500)
  const [currency, setCurrency] = useState('USD')
  const [evidenceType, setEvidenceType] = useState('accounting_record')
  const [evidenceSource, setEvidenceSource] = useState('stripe_settlement_batch_01.csv')
  const [proofAgg, setProofAgg] = useState<FinancialProofAggregate | null>(null)
  const [exportedReport, setExportedReport] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const handleVerifySnapshots = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const parseCsv = (s: string) =>
        s
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean)

      const res = await verifySnapshots({
        before: {
          contract_version: 'v1',
          system_version: '1.0.0',
          baseline: {
            ledger_net_balance_minor: beforeNet,
            total_refunded_minor: beforeRefunded,
            captured_amount_minor: capturedAmount,
          },
          violations: parseCsv(beforeViolations),
          counterexample_ids: [],
          reproducibility_metadata: { seed: 42 },
        },
        after: {
          contract_version: 'v1',
          system_version: '1.0.1',
          baseline: {
            ledger_net_balance_minor: afterNet,
            total_refunded_minor: afterRefunded,
            captured_amount_minor: capturedAmount,
          },
          violations: parseCsv(afterViolations),
          counterexample_ids: [],
          reproducibility_metadata: { seed: 42 },
        },
      })
      setVerifyResult(res)
      setMessage(
        `Repair verification completed (${res.result.passed ? 'PASSED' : 'FAILED'}).`,
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification request failed.')
    } finally {
      setBusy(false)
    }
  }

  const handleCreateAndEvaluateProof = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const claimId = crypto.randomUUID()
      const evidenceId = crypto.randomUUID()
      const created = await createProof({
        subject: subject.trim(),
        claims: [
          {
            id: claimId,
            claim_type: claimType,
            subject: subject.trim(),
            amount: claimAmount,
            currency,
            verification_status: 'verified',
            confidence: 0.96,
            confidence_level: 'high',
          },
        ],
        evidence: [
          {
            id: evidenceId,
            evidence_type: evidenceType,
            source_name: evidenceSource.trim(),
            received_at: new Date().toISOString().slice(0, 10),
            status: 'verified',
          },
        ],
        evidence_links: [
          {
            claim_id: claimId,
            evidence_id: evidenceId,
            verification_status: 'supported',
            confidence: 0.96,
            explanation: 'Matched ledger entry against settlement batch.',
          },
        ],
      })
      const evaluated = await evaluateProof(created.proof.id)
      setProofAgg(evaluated)
      setMessage(
        `Proof ${evaluated.proof.id.slice(0, 8)} created and evaluated (${evaluated.proof.status}).`,
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Proof creation/evaluation failed.')
    } finally {
      setBusy(false)
    }
  }

  const handleExport = async (format: 'json' | 'csv' | 'markdown') => {
    if (!proofAgg) return
    setError('')
    try {
      const text = await platformApi.exportProofReport(proofAgg.proof.id, format)
      setExportedReport(text)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed.')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[#0B1F3A]">
          Deterministic Verification & Proof Builder
        </h2>
        <p className="text-sm text-slate-600">
          Compare before/after repair snapshots for zero regressions, bind claims to cryptographic
          evidence, and export signed audit packets.
        </p>
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

      <div className="grid gap-6 lg:grid-cols-2">
        <form
          onSubmit={handleVerifySnapshots}
          className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4"
        >
          <div className="flex items-center gap-2 text-[#0B1F3A] font-semibold">
            <Scale className="w-4 h-4 text-emerald-600" />
            <span>Repair Snapshot Regression Check</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Before Net Balance (minor)
              </label>
              <input
                type="number"
                value={beforeNet}
                onChange={(e) => setBeforeNet(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                After Net Balance (minor)
              </label>
              <input
                type="number"
                value={afterNet}
                onChange={(e) => setAfterNet(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Before Refunded (minor)
              </label>
              <input
                type="number"
                value={beforeRefunded}
                onChange={(e) => setBeforeRefunded(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                After Refunded (minor)
              </label>
              <input
                type="number"
                value={afterRefunded}
                onChange={(e) => setAfterRefunded(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Captured Amount (minor)
              </label>
              <input
                type="number"
                value={capturedAmount}
                onChange={(e) => setCapturedAmount(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Before Violations (CSV)
              </label>
              <input
                type="text"
                value={beforeViolations}
                onChange={(e) => setBeforeViolations(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular"
              />
            </div>
            <div className="col-span-2">
              <label className="block text-xs font-medium text-slate-700 mb-1">
                After Violations (CSV)
              </label>
              <input
                type="text"
                value={afterViolations}
                onChange={(e) => setAfterViolations(e.target.value)}
                placeholder="Empty when all violations are resolved"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-lg bg-[#0B1F3A] px-4 py-2 text-sm font-medium text-white hover:bg-[#132f57] disabled:opacity-50"
          >
            <Scale className="w-4 h-4" />
            Verify Repair
          </button>

          {verifyResult && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-[#0B1F3A]">Verification Verdict</span>
                <StatusBadge value={verifyResult.result.passed ? 'passed' : 'failed'} />
              </div>
              <p className="font-mono-tabular text-slate-700">
                Regression Detected: {String(verifyResult.result.regression_detected)} | Resolved:{' '}
                {verifyResult.comparison.resolved_violations.length} | Introduced:{' '}
                {verifyResult.comparison.introduced_violations.length}
              </p>
              {verifyResult.result.violations.map((v, i) => (
                <div
                  key={i}
                  className="rounded border border-rose-200 bg-rose-50 p-2 text-rose-800 font-mono-tabular"
                >
                  {v}
                </div>
              ))}
            </div>
          )}
        </form>

        <form
          onSubmit={handleCreateAndEvaluateProof}
          className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4"
        >
          <div className="flex items-center gap-2 text-[#0B1F3A] font-semibold">
            <FileCheck2 className="w-4 h-4 text-emerald-600" />
            <span>Financial Proof Builder & Export</span>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Subject</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Claim Type</label>
              <select
                value={claimType}
                onChange={(e) => setClaimType(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              >
                <option value="balance">balance</option>
                <option value="transaction">transaction</option>
                <option value="income">income</option>
                <option value="expense">expense</option>
                <option value="cash_flow">cash_flow</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Evidence Type
              </label>
              <select
                value={evidenceType}
                onChange={(e) => setEvidenceType(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              >
                <option value="accounting_record">accounting_record</option>
                <option value="bank_statement">bank_statement</option>
                <option value="payment_record">payment_record</option>
                <option value="invoice">invoice</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Claim Amount</label>
              <input
                type="number"
                value={claimAmount}
                onChange={(e) => setClaimAmount(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Currency</label>
              <input
                type="text"
                value={currency}
                onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                maxLength={3}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Supporting Evidence Source
            </label>
            <input
              type="text"
              value={evidenceSource}
              onChange={(e) => setEvidenceSource(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular"
            />
          </div>
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-lg bg-[#0B1F3A] px-4 py-2 text-sm font-medium text-white hover:bg-[#132f57] disabled:opacity-50"
          >
            <FileCheck2 className="w-4 h-4" />
            Create & Evaluate Proof
          </button>

          {proofAgg && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-mono-tabular font-semibold text-[#0B1F3A]">
                  Proof {proofAgg.proof.id}
                </span>
                <StatusBadge value={proofAgg.proof.status} />
              </div>
              <div className="font-mono-tabular text-slate-700">
                Confidence: {Number(proofAgg.proof.overall_confidence).toFixed(2)} | Claims:{' '}
                {proofAgg.claims.length} | Evidence: {proofAgg.evidence.length}
              </div>
              <div className="flex flex-wrap gap-2">
                {(['json', 'csv', 'markdown'] as const).map((fmt) => (
                  <button
                    key={fmt}
                    type="button"
                    onClick={() => void handleExport(fmt)}
                    className="inline-flex items-center gap-1.5 rounded border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Export {fmt.toUpperCase()}
                  </button>
                ))}
              </div>
              {exportedReport && (
                <pre className="rounded bg-white border border-slate-200 p-3 overflow-x-auto max-h-56 font-mono-tabular text-[11px]">
                  {exportedReport}
                </pre>
              )}
            </div>
          )}
        </form>
      </div>
    </div>
  )
}
