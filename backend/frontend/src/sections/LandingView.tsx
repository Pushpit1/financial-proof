import React from 'react'
import {
  ArrowRight,
  CheckCircle2,
  FileCode2,
  Flame,
  Lock,
  Scale,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import type { SystemStatus } from '../api/platform'
import type { NavSection } from '../components/AppShell'
import { StatusBadge } from '../components/StatusBadge'

interface LandingViewProps {
  systemStatus: SystemStatus | null
  onEnterWorkspace: (section?: NavSection) => void
}

const PIPELINE_STEPS = [
  { step: '01', title: 'Business Rule & Contract', detail: 'Compile natural-language policies into deterministic invariants and ceiling rules.' },
  { step: '02', title: 'Document Ingestion & Recon', detail: 'Verify CSV/JSON/PDF checksums, extract Decimal rows, and reconcile provider feeds.' },
  { step: '03', title: 'Adversarial Simulation', detail: 'Inject duplicate, out-of-order, delayed, retry, and crash sequences.' },
  { step: '04', title: 'Counterexample Shrinking', detail: 'Minimize failing execution traces to the smallest reproducible witness.' },
  { step: '05', title: 'Blast Radius & AI Advisory', detail: 'Quantify exact monetary exposure and inspect grounded root causes without AI override.' },
  { step: '06', title: 'Runtime Guardian & Proof', detail: 'Enforce ALLOW/BLOCK/REVIEW boundaries and export verifiable audit reports.' },
]

export function LandingView({ systemStatus, onEnterWorkspace }: LandingViewProps) {
  return (
    <div className="min-h-screen bg-[#F9F8F5] text-slate-900 flex flex-col">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-[#1E3A5F] text-white flex items-center justify-center text-xs font-bold font-mono-tabular">
              FP
            </div>
            <div>
              <span className="text-base font-semibold tracking-tight">Financial Proof</span>
              <span className="hidden sm:inline-block ml-2.5 text-[11px] font-mono-tabular uppercase tracking-wider text-slate-500">
                Deterministic Financial Verification
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {systemStatus && (
              <div className="hidden md:flex items-center gap-2 text-xs text-slate-500 font-mono-tabular">
                <span>Engine</span>
                <StatusBadge value="ok" />
                <span>DB</span>
                <StatusBadge value={systemStatus.database} />
              </div>
            )}
            <button
              type="button"
              onClick={() => onEnterWorkspace('overview')}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-[#1E3A5F] text-white text-xs font-medium hover:bg-[#162C49]"
            >
              Open Verification Workbench
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <section className="max-w-7xl mx-auto px-4 sm:px-6 pt-14 pb-12 grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-7 space-y-5">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-slate-200 text-xs font-mono-tabular text-slate-700">
              <ShieldCheck className="w-3.5 h-3.5 text-[#047857]" />
              Deterministic verification · Zero floating-point money · Traceable evidence
            </div>

            <h1 className="text-3xl sm:text-5xl font-semibold tracking-tight text-slate-900 leading-[1.12]">
              Prove financial rules safe before a failure becomes a monetary loss.
            </h1>

            <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl">
              Financial Proof compiles explicit financial contracts, tests payment state machines against adversarial sequences, shrinks counterexamples, quantifies exact blast-radius exposure, and enforces runtime invariants with immutable audit trails.
            </p>

            <div className="flex flex-wrap gap-3 pt-2">
              <button
                type="button"
                onClick={() => onEnterWorkspace('overview')}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-[#1E3A5F] text-white text-sm font-medium hover:bg-[#162C49]"
              >
                Launch Workbench
                <ArrowRight className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => onEnterWorkspace('simulations')}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-white border border-slate-300 text-slate-800 text-sm font-medium hover:bg-slate-50"
              >
                Run Adversarial Attack
              </button>
              <button
                type="button"
                onClick={() => onEnterWorkspace('documents')}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-white border border-slate-300 text-slate-800 text-sm font-medium hover:bg-slate-50"
              >
                Upload & Reconcile Ledger
              </button>
            </div>
          </div>

          <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <div className="text-[11px] font-mono-tabular uppercase tracking-wider text-slate-500">
                  Canonical Invariant Example
                </div>
                <div className="text-sm font-semibold text-slate-900 mt-0.5">
                  Refund Ceiling Verification
                </div>
              </div>
              <StatusBadge value="failed" />
            </div>

            <div className="space-y-2 text-xs font-mono-tabular">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Contract Rule</span>
                <span className="text-slate-900">refund_amount &lt;= payment_amount</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Original Payment</span>
                <span className="text-slate-900">INR 50.00</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Refund Attempt</span>
                <span className="text-rose-700 font-semibold">INR 75.00</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Direct Exposure</span>
                <span className="text-rose-700 font-semibold">INR 75.00</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-500">Runtime Guardian</span>
                <StatusBadge value="block" />
              </div>
            </div>

            <div className="p-3 rounded bg-slate-50 border border-slate-200 text-xs text-slate-600">
              AI explanations are strictly bounded and advisory. Verification decisions are computed exclusively with deterministic <code className="font-mono-tabular">Decimal</code> rules.
            </div>
          </div>
        </section>

        <section className="bg-white border-y border-slate-200 py-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 space-y-8">
            <div className="max-w-2xl">
              <h2 className="text-xl font-semibold text-slate-900">
                End-to-End Verification Pipeline
              </h2>
              <p className="text-sm text-slate-600 mt-1">
                Every stage produces machine-readable, auditable artifacts backed by the FastAPI verification engine.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {PIPELINE_STEPS.map((item) => (
                <div
                  key={item.step}
                  className="p-5 rounded-lg border border-slate-200 bg-[#F9F8F5]"
                >
                  <div className="text-xs font-mono-tabular font-semibold text-[#1E3A5F]">
                    STAGE {item.step}
                  </div>
                  <h3 className="text-sm font-semibold text-slate-900 mt-1.5">
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                    {item.detail}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="max-w-7xl mx-auto px-4 sm:px-6 py-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <PillarCard
            icon={Scale}
            title="Decimal Monetary Math"
            body="All monetary arithmetic uses exact Python Decimal and integer minor units—never IEEE-754 floats."
          />
          <PillarCard
            icon={Sparkles}
            title="AI Never Overrides Truth"
            body="Bounded AI inspection tools summarize persisted evidence while deterministic evaluators remain authoritative."
          />
          <PillarCard
            icon={Flame}
            title="Quantified Blast Radius"
            body="Translate constraint violations into direct loss, refund exposure, and duplicate-charge risk."
          />
          <PillarCard
            icon={Lock}
            title="Fail-Closed Security"
            body="HMAC-SHA256 webhook checks, sanitized document uploads, SHA-256 checksums, and security headers."
          />
        </section>
      </main>

      <footer className="bg-white border-t border-slate-200 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#047857]" />
            <span>Financial Proof — Deterministic Financial Intelligence & Verification</span>
          </div>
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => onEnterWorkspace('contracts')}
              className="hover:text-slate-900 inline-flex items-center gap-1"
            >
              <FileCode2 className="w-3.5 h-3.5" /> Contracts
            </button>
            <button
              type="button"
              onClick={() => onEnterWorkspace('audit')}
              className="hover:text-slate-900"
            >
              Audit & Security
            </button>
          </div>
        </div>
      </footer>
    </div>
  )
}

function PillarCard({
  icon: Icon,
  title,
  body,
}: {
  icon: React.ComponentType<{ className?: string }>
  title: string
  body: string
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-2">
      <Icon className="w-5 h-5 text-[#1E3A5F]" />
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      <p className="text-xs text-slate-600 leading-relaxed">{body}</p>
    </div>
  )
}
