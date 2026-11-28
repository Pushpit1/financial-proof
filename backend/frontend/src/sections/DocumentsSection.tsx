import React, { useEffect, useState } from 'react'
import { FileUp, GitCompare, ShieldAlert } from 'lucide-react'
import {
  platformApi,
  type DocumentItem,
  type DocumentUploadResponse,
  type ReconciliationResponse,
} from '../api/platform'
import { MarginProofCard } from '../components/MarginProofCard'
import { SectionHeader } from '../components/SectionHeader'
import { StatusBadge } from '../components/StatusBadge'

interface LedgerRecordInput {
  reference: string
  amount: string
  currency: string
  status: string
}

function parseLedgerCsv(raw: string): LedgerRecordInput[] {
  const lines = raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
  const rows: LedgerRecordInput[] = []
  for (let i = 0; i < lines.length; i++) {
    const parts = lines[i].split(',').map((p) => p.trim())
    if (parts.length < 3) continue
    if (i === 0 && parts[0].toLowerCase() === 'reference') continue
    rows.push({
      reference: parts[0],
      amount: parts[1],
      currency: parts[2].toUpperCase(),
      status: parts[3] || 'captured',
    })
  }
  return rows
}

const DEFAULT_INTERNAL_CSV = `reference,amount,currency,status
txn_1001,1250.00,USD,captured
txn_1002,840.50,USD,captured
txn_1003,310.00,USD,refunded`

const DEFAULT_PROVIDER_CSV = `reference,amount,currency,status
txn_1001,1250.00,USD,captured
txn_1002,800.50,USD,captured
txn_1004,199.00,USD,captured`

export function DocumentsSection() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [proofId, setProofId] = useState('')
  const [uploadResult, setUploadResult] = useState<DocumentUploadResponse | null>(null)
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [internalCsv, setInternalCsv] = useState(DEFAULT_INTERNAL_CSV)
  const [providerCsv, setProviderCsv] = useState(DEFAULT_PROVIDER_CSV)
  const [reconResult, setReconResult] = useState<ReconciliationResponse | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const loadDocuments = async () => {
    try {
      setDocuments(await platformApi.listDocuments())
    } catch {
      // ignore if database unreachable
    }
  }

  useEffect(() => {
    void loadDocuments()
  }, [])

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFile) {
      setError('Select a CSV, JSON, TXT, or PDF evidence file first.')
      return
    }
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      if (proofId.trim()) {
        formData.append('proof_id', proofId.trim())
      }
      const res = await platformApi.uploadDocument(formData)
      setUploadResult(res)
      setMessage(
        `Processed ${res.filename} (${res.extracted_row_count} extracted ledger rows, SHA-256 ${res.checksum_sha256.slice(0, 12)}...).`,
      )
      await loadDocuments()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Document upload failed.')
    } finally {
      setBusy(false)
    }
  }

  const handleReconcile = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const internalRecords = parseLedgerCsv(internalCsv)
      const providerRecords = parseLedgerCsv(providerCsv)
      if (internalRecords.length === 0 || providerRecords.length === 0) {
        setError('Both internal and provider CSV inputs need at least one valid row.')
        setBusy(false)
        return
      }
      const res = await platformApi.runReconciliation({
        internal_records: internalRecords,
        provider_records: providerRecords,
      })
      setReconResult(res)
      setMessage(
        `Reconciliation complete: ${res.matched_count} matched, ${res.discrepancy_count} discrepancies.`,
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reconciliation failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Section 3.0 // Cryptographic Evidence & Reconciliation"
        title={
          <>
            Document Ingestion &amp; Ledger Delta (<span className="math-var">ΔL</span>)
          </>
        }
        description="Ingest signed evidence files with SHA-256 checksum deduplication, extract exact Decimal ledger rows, and reconcile against provider settlements."
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
        <form
          onSubmit={handleUpload}
          className="lg:col-span-5 bg-white border border-[#C5C4B1] rounded-xl p-5 distill-card space-y-4"
        >
          <div className="flex items-center gap-2 text-xs font-mono-tabular font-bold text-[#191919] pb-2.5 border-b border-slate-200">
            <FileUp className="w-4 h-4 text-[#FF6170]" />
            <span>EVIDENCE UPLOAD &amp; EXTRACTION</span>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Evidence File (.csv, .json, .txt, .pdf, max 5 MB)
            </label>
            <input
              type="file"
              accept=".csv,.json,.txt,.pdf"
              onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
              className="block w-full text-xs text-slate-700 file:mr-3 file:rounded file:border file:border-[#C5C4B1] file:bg-[#F5F5F3] file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-[#191919] hover:file:bg-slate-100"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Optional Proof ID (attaches evidence when DB connected)
            </label>
            <input
              type="text"
              value={proofId}
              onChange={(e) => setProofId(e.target.value)}
              placeholder="UUID of existing FinancialProof"
              className="w-full rounded-lg border border-[#C5C4B1] bg-[#F5F5F3] px-3 py-2 text-xs font-mono-tabular focus:outline-none focus:border-[#191919]"
            />
          </div>
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-md bg-[#191919] px-4 py-2 text-xs font-medium text-white hover:bg-[#2D2D2D] disabled:opacity-50"
          >
            <FileUp className="w-3.5 h-3.5" />
            {busy ? 'Uploading...' : 'Ingest & Extract'}
          </button>

          {uploadResult && (
            <div className="rounded-lg border border-[#C5C4B1] bg-[#F5F5F3] p-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs font-bold font-mono-tabular text-[#191919]">
                  {uploadResult.filename}
                </span>
                <div className="flex items-center gap-2">
                  <StatusBadge
                    value={uploadResult.persisted ? 'verified' : 'advisory'}
                  />
                  {uploadResult.duplicate_checksum_detected && (
                    <StatusBadge value="review" />
                  )}
                </div>
              </div>
              <dl className="grid grid-cols-2 gap-2 text-xs font-mono-tabular">
                <div>
                  <dt className="text-slate-500">Extracted Rows</dt>
                  <dd className="font-bold text-[#191919]">
                    {uploadResult.extracted_row_count}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500">Total Amount</dt>
                  <dd className="font-bold text-[#191919]">
                    {uploadResult.total_amount}
                  </dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-slate-500">SHA-256 Checksum</dt>
                  <dd className="text-[11px] break-all text-slate-700">
                    {uploadResult.checksum_sha256}
                  </dd>
                </div>
              </dl>
              {uploadResult.warnings.length > 0 && (
                <ul className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded p-2 space-y-1">
                  {uploadResult.warnings.map((w, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <ShieldAlert className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                      <span>{w}</span>
                    </li>
                  ))}
                </ul>
              )}
              {uploadResult.extracted_rows.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs font-mono-tabular">
                    <thead>
                      <tr className="border-b border-slate-200 text-left text-slate-500">
                        <th className="py-1 pr-2">#</th>
                        <th className="py-1 pr-2">Ref</th>
                        <th className="py-1 pr-2">Amount</th>
                        <th className="py-1 pr-2">CCY</th>
                        <th className="py-1">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {uploadResult.extracted_rows.slice(0, 10).map((row) => (
                        <tr key={row.row_index} className="border-b border-slate-100">
                          <td className="py-1 pr-2">{row.row_index}</td>
                          <td className="py-1 pr-2">{row.reference || '-'}</td>
                          <td className="py-1 pr-2">{row.amount}</td>
                          <td className="py-1 pr-2">{row.currency}</td>
                          <td className="py-1">{row.status || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </form>

        <form
          onSubmit={handleReconcile}
          className="lg:col-span-4 bg-white border border-[#C5C4B1] rounded-xl p-5 distill-card space-y-4"
        >
          <div className="flex items-center gap-2 text-xs font-mono-tabular font-bold text-[#191919] pb-2.5 border-b border-slate-200">
            <GitCompare className="w-4 h-4 text-[#FF6170]" />
            <span>DETERMINISTIC RECONCILIATION</span>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Internal Ledger CSV
            </label>
            <textarea
              rows={4}
              value={internalCsv}
              onChange={(e) => setInternalCsv(e.target.value)}
              className="w-full rounded-lg border border-[#C5C4B1] bg-[#F5F5F3] px-3 py-2 text-xs font-mono-tabular focus:outline-none focus:border-[#191919]"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Provider Settlement CSV
            </label>
            <textarea
              rows={4}
              value={providerCsv}
              onChange={(e) => setProviderCsv(e.target.value)}
              className="w-full rounded-lg border border-[#C5C4B1] bg-[#F5F5F3] px-3 py-2 text-xs font-mono-tabular focus:outline-none focus:border-[#191919]"
            />
          </div>
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-md bg-[#191919] px-4 py-2 text-xs font-medium text-white hover:bg-[#2D2D2D] disabled:opacity-50"
          >
            <GitCompare className="w-3.5 h-3.5" />
            {busy ? 'Reconciling...' : 'Run Reconciliation'}
          </button>

          {reconResult && (
            <div className="rounded-lg border border-[#C5C4B1] bg-[#F5F5F3] p-4 space-y-3">
              <div className="grid grid-cols-3 gap-2 text-xs font-mono-tabular">
                <div>
                  <span className="text-slate-500 block">Matched</span>
                  <span className="text-sm font-bold text-emerald-700">
                    {reconResult.matched_count}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Delta</span>
                  <span className="text-sm font-bold text-rose-700">
                    {reconResult.discrepancy_count}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Exposure</span>
                  <span className="text-sm font-bold text-[#191919]">
                    {reconResult.total_exposure}
                  </span>
                </div>
              </div>
              {reconResult.discrepancies.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-[11px] font-mono-tabular">
                    <thead>
                      <tr className="border-b border-slate-200 text-left text-slate-500">
                        <th className="py-1 pr-2">Ref</th>
                        <th className="py-1 pr-2">Exp</th>
                        <th className="py-1 pr-2">Act</th>
                        <th className="py-1">Delta</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reconResult.discrepancies.map((d, i) => (
                        <tr key={i} className="border-b border-slate-100">
                          <td className="py-1 pr-2 font-bold text-rose-700">{d.reference}</td>
                          <td className="py-1 pr-2">{d.expected}</td>
                          <td className="py-1 pr-2">{d.actual}</td>
                          <td className="py-1 font-bold">{d.exposure}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </form>

        <aside className="lg:col-span-3">
          <MarginProofCard
            sectionCode="SEC. 3.0"
            axiomLines={
              <>
                <div>ΔL = Σ Internal − Σ Provider</div>
                <div className="text-emerald-300">Digest: SHA-256 Deduplicated</div>
                <div className="text-amber-300">Max Upload: 5.0 MB Allowlist</div>
              </>
            }
            note="Uploads neutralize path traversal and reject unallowlisted extensions before exact Decimal extraction."
          />
        </aside>
      </div>

      <div className="bg-white border border-[#C5C4B1] rounded-xl p-5 distill-card">
        <h3 className="text-xs font-mono-tabular font-bold text-[#191919] mb-3">
          PERSISTED EVIDENCE RECORDS ({documents.length})
        </h3>
        {documents.length === 0 ? (
          <p className="text-xs text-slate-500">
            No persisted evidence records loaded yet. Upload a document with an active PostgreSQL connection to record it here.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-left font-mono-tabular text-slate-500">
                  <th className="py-2 pr-3">Source Name</th>
                  <th className="py-2 pr-3">Type</th>
                  <th className="py-2 pr-3">Status</th>
                  <th className="py-2 pr-3">Checksum</th>
                  <th className="py-2">Received</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id} className="border-b border-slate-100">
                    <td className="py-2 pr-3 font-medium text-[#191919]">{doc.source_name}</td>
                    <td className="py-2 pr-3 font-mono-tabular">{doc.evidence_type}</td>
                    <td className="py-2 pr-3">
                      <StatusBadge value={doc.status} />
                    </td>
                    <td className="py-2 pr-3 font-mono-tabular text-[11px] text-slate-600">
                      {doc.checksum ? `${doc.checksum.slice(0, 16)}...` : '-'}
                    </td>
                    <td className="py-2 font-mono-tabular text-slate-600">{doc.received_at}</td>
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
