import React, { useEffect, useState } from 'react'
import { FileUp, GitCompare, ShieldAlert } from 'lucide-react'
import {
  platformApi,
  type DocumentItem,
  type DocumentUploadResponse,
  type ReconciliationResponse,
} from '../api/platform'
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
      // ignore if database unreachable; surfaced on status banner
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
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-[#0B1F3A]">
            Documents & Ledger Reconciliation
          </h2>
          <p className="text-sm text-slate-600">
            Ingest signed evidence files with SHA-256 integrity checks, exact Decimal extraction,
            and deterministic ledger-to-provider reconciliation.
          </p>
        </div>
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
          onSubmit={handleUpload}
          className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4"
        >
          <div className="flex items-center gap-2 text-[#0B1F3A] font-semibold">
            <FileUp className="w-4 h-4 text-emerald-600" />
            <span>Evidence Upload & Extraction</span>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Evidence File (.csv, .json, .txt, .pdf, max 5 MB)
            </label>
            <input
              type="file"
              accept=".csv,.json,.txt,.pdf"
              onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-slate-700 file:mr-3 file:rounded-lg file:border file:border-slate-300 file:bg-slate-50 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-slate-800 hover:file:bg-slate-100"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Optional Proof ID (attaches extracted evidence when DB is connected)
            </label>
            <input
              type="text"
              value={proofId}
              onChange={(e) => setProofId(e.target.value)}
              placeholder="UUID of existing FinancialProof"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular focus:outline-none focus:ring-2 focus:ring-[#0B1F3A]/20"
            />
          </div>
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-lg bg-[#0B1F3A] px-4 py-2 text-sm font-medium text-white hover:bg-[#132f57] disabled:opacity-50"
          >
            <FileUp className="w-4 h-4" />
            {busy ? 'Uploading...' : 'Ingest & Extract'}
          </button>

          {uploadResult && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-sm font-semibold text-[#0B1F3A]">
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
              <dl className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <dt className="text-slate-500">Extracted Rows</dt>
                  <dd className="font-mono-tabular font-semibold text-slate-900">
                    {uploadResult.extracted_row_count}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500">Total Amount</dt>
                  <dd className="font-mono-tabular font-semibold text-slate-900">
                    {uploadResult.total_amount}
                  </dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-slate-500">SHA-256 Checksum</dt>
                  <dd className="font-mono-tabular text-[11px] break-all text-slate-700">
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
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 text-left text-slate-500">
                        <th className="py-1 pr-2">#</th>
                        <th className="py-1 pr-2">Reference</th>
                        <th className="py-1 pr-2">Amount</th>
                        <th className="py-1 pr-2">Currency</th>
                        <th className="py-1">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {uploadResult.extracted_rows.slice(0, 10).map((row) => (
                        <tr key={row.row_index} className="border-b border-slate-100">
                          <td className="py-1 pr-2 font-mono-tabular">{row.row_index}</td>
                          <td className="py-1 pr-2 font-mono-tabular">{row.reference || '-'}</td>
                          <td className="py-1 pr-2 font-mono-tabular">{row.amount}</td>
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
          className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4"
        >
          <div className="flex items-center gap-2 text-[#0B1F3A] font-semibold">
            <GitCompare className="w-4 h-4 text-emerald-600" />
            <span>Deterministic Ledger Reconciliation</span>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Internal Ledger CSV (`reference,amount,currency,status`)
            </label>
            <textarea
              rows={4}
              value={internalCsv}
              onChange={(e) => setInternalCsv(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs font-mono-tabular focus:outline-none focus:ring-2 focus:ring-[#0B1F3A]/20"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Provider Settlement CSV (`reference,amount,currency,status`)
            </label>
            <textarea
              rows={4}
              value={providerCsv}
              onChange={(e) => setProviderCsv(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs font-mono-tabular focus:outline-none focus:ring-2 focus:ring-[#0B1F3A]/20"
            />
          </div>
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-lg bg-[#0B1F3A] px-4 py-2 text-sm font-medium text-white hover:bg-[#132f57] disabled:opacity-50"
          >
            <GitCompare className="w-4 h-4" />
            {busy ? 'Reconciling...' : 'Run Reconciliation'}
          </button>

          {reconResult && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-3">
              <div className="grid grid-cols-3 gap-3 text-xs">
                <div>
                  <span className="text-slate-500 block">Matched</span>
                  <span className="text-base font-semibold font-mono-tabular text-emerald-700">
                    {reconResult.matched_count}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Discrepancies</span>
                  <span className="text-base font-semibold font-mono-tabular text-rose-700">
                    {reconResult.discrepancy_count}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Total Exposure</span>
                  <span className="text-base font-semibold font-mono-tabular text-[#0B1F3A]">
                    {reconResult.total_exposure}
                  </span>
                </div>
              </div>
              {reconResult.discrepancies.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 text-left text-slate-500">
                        <th className="py-1 pr-2">Type</th>
                        <th className="py-1 pr-2">Ref</th>
                        <th className="py-1 pr-2">Expected</th>
                        <th className="py-1 pr-2">Actual</th>
                        <th className="py-1">Exposure</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reconResult.discrepancies.map((d, i) => (
                        <tr key={i} className="border-b border-slate-100">
                          <td className="py-1 pr-2">
                            <StatusBadge value="failed" />
                            <span className="ml-1.5 font-mono-tabular">{d.discrepancy_type}</span>
                          </td>
                          <td className="py-1 pr-2 font-mono-tabular">{d.reference}</td>
                          <td className="py-1 pr-2 font-mono-tabular">{d.expected}</td>
                          <td className="py-1 pr-2 font-mono-tabular">{d.actual}</td>
                          <td className="py-1 font-mono-tabular font-semibold">{d.exposure}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </form>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
        <h3 className="text-sm font-semibold text-[#0B1F3A] mb-3">
          Persisted Evidence Records ({documents.length})
        </h3>
        {documents.length === 0 ? (
          <p className="text-xs text-slate-500">
            No persisted evidence records loaded yet. Upload a document with an active database
            connection to record it here.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-left text-slate-500">
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
                    <td className="py-2 pr-3 font-medium text-slate-900">{doc.source_name}</td>
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
