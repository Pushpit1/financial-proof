import React, { useState } from 'react'
import {
  ArrowRight,
  CheckCircle2,
  FileCode2,
  Flame,
  Lock,
  Play,
  Scale,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import { platformApi, type BlastRadiusResult, type SystemStatus } from '../api/platform'
import type { NavSection } from '../components/AppShell'
import { StatusBadge } from '../components/StatusBadge'

interface LandingViewProps {
  systemStatus: SystemStatus | null
  onEnterWorkspace: (section?: NavSection) => void
}

const PIPELINE_STAGES: Array<{
  step: string
  title: string
  badge: string
  endpoint: string
  detail: string
  section: NavSection
}> = [
  {
    step: '01',
    title: 'Rule Compile',
    badge: 'AST',
    endpoint: 'POST /api/contracts/compile',
    detail:
      'Compiles business payment rules into typed Python Decimal invariants and ceiling bounds with zero ambiguity.',
    section: 'contracts',
  },
  {
    step: '02',
    title: 'Document & Recon',
    badge: 'SHA-256',
    endpoint: 'POST /api/reconciliation/run',
    detail:
      'Validates CSV/JSON/TXT/PDF uploads with checksum deduplication and computes exact ledger-to-provider drift.',
    section: 'documents',
  },
  {
    step: '03',
    title: 'Adversarial Attacks',
    badge: '8 VECTORS',
    endpoint: 'POST /api/simulations/{id}/attacks',
    detail:
      'Injects duplicate, out-of-order, delayed, retry, lost-response, partial-failure, stale-worker, and crash sequences.',
    section: 'simulations',
  },
  {
    step: '04',
    title: 'Trace Shrinker',
    badge: 'MIN WITNESS',
    endpoint: 'POST /api/simulations/{id}/counterexamples/shrink',
    detail:
      'Minimizes failing execution sequences down to the smallest deterministic counterexample that triggers the violation.',
    section: 'simulations',
  },
  {
    step: '05',
    title: 'Blast Radius',
    badge: 'DECIMAL',
    endpoint: 'POST /api/blast-radius',
    detail:
      'Quantifies direct loss, actual exposure, and maximum exposure alongside read-only advisory AI root-cause tools.',
    section: 'analysis',
  },
  {
    step: '06',
    title: 'Runtime Guardian',
    badge: 'ALLOW / BLOCK',
    endpoint: 'POST /api/guardian/evaluate',
    detail:
      'Enforces pre-settlement policy gates and exports signed JSON, CSV, and Markdown proof verification dossiers.',
    section: 'verification',
  },
]

export function LandingView({ systemStatus, onEnterWorkspace }: LandingViewProps) {
  const capturedAmount = 1000
  const [attemptedRefund, setAttemptedRefund] = useState(1250)
  const [liveResult, setLiveResult] = useState<BlastRadiusResult | null>(null)
  const [liveGuardian, setLiveGuardian] = useState<string | null>(null)
  const [checking, setChecking] = useState(false)
  const [checkError, setCheckError] = useState('')
  const [activeStage, setActiveStage] = useState(PIPELINE_STAGES[0].step)

  const margin = capturedAmount - attemptedRefund
  const isSafe = attemptedRefund <= capturedAmount
  const localExposure = isSafe ? 0 : attemptedRefund

  const selectedStage =
    PIPELINE_STAGES.find((s) => s.step === activeStage) ?? PIPELINE_STAGES[0]

  const runLiveVerification = async () => {
    setChecking(true)
    setCheckError('')
    try {
      const [br, grd] = await Promise.all([
        platformApi.analyzeBlastRadius({
          source_text: 'Customer refund must not exceed the original payment amount.',
          payment_amount: capturedAmount.toFixed(2),
          refund_amount: attemptedRefund.toFixed(2),
          currency: 'USD',
          persist: false,
        }),
        platformApi.evaluateGuardian({
          operation: 'refund',
          actor_id: 'distill-hero-probe',
          amount_minor: attemptedRefund * 100,
          payment_amount_minor: capturedAmount * 100,
          currency: 'USD',
          actor_authorized: true,
          operation_authorized: true,
          duplicate_detected: false,
          state_transition_valid: true,
          requires_manual_review: false,
          persist_audit: false,
        }),
      ])
      setLiveResult(br)
      setLiveGuardian(`${grd.decision.toUpperCase()} (${grd.rule})`)
    } catch (err) {
      setCheckError(err instanceof Error ? err.message : 'Live API verification failed.')
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="min-h-screen text-[#0B1F3A] flex flex-col">
      {/* Masthead */}
      <header className="bg-[#FAF9F6]/90 backdrop-blur border-b border-[#0B1F3A]/15 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-[#0B1F3A] text-white flex items-center justify-center text-xs font-bold font-mono-tabular">
              [FP]
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm sm:text-base font-bold tracking-tight text-[#0B1F3A]">
                  Financial Proof
                </span>
                <span className="hidden sm:inline-block px-2 py-0.5 rounded bg-white border border-[#0B1F3A]/20 text-[11px] font-mono-tabular text-slate-600">
                  SPEC v2.0
                </span>
              </div>
              <div className="text-[10px] font-mono-tabular uppercase tracking-wider text-slate-500">
                Axiomatic Journal · Deterministic Financial Verification
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {systemStatus && (
              <div className="hidden md:flex items-center gap-2 text-xs font-mono-tabular text-slate-600">
                <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800">
                  DECIMAL EXACT
                </span>
                <span>DB</span>
                <StatusBadge value={systemStatus.database} />
              </div>
            )}
            <button
              type="button"
              onClick={() => onEnterWorkspace('overview')}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-[#0B1F3A] text-white text-xs font-medium hover:bg-[#14335c] transition"
            >
              Open Workbench
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero Interactive Publication + Alloy Margin Dossier */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 pt-10 pb-12">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left / Center Essay & Live Parameter Widget */}
            <div className="lg:col-span-7 space-y-5">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-[#0B1F3A]/20 text-xs font-mono-tabular text-[#0B1F3A]">
                <ShieldCheck className="w-3.5 h-3.5 text-[#047857]" />
                ESSAY + LIVE ENGINE · ∀ <span className="math-var">e</span> ∈ Trace : Balance(<span className="math-var">e</span>) ≥ 0
              </div>

              <h1 className="font-serif-editorial text-3xl sm:text-5xl font-bold tracking-tight text-[#0B1F3A] leading-[1.12]">
                Bounded Refund Conservation: Why <span className="math-var">R(t) ≤ C(t)</span> Must Hold Deterministically.
              </h1>

              <p className="text-sm sm:text-base text-slate-700 leading-relaxed max-w-2xl">
                Let <span className="math-var font-semibold">C</span> denote cumulative captured settlement and <span className="math-var font-semibold">R</span> denote attempted refund principal across adversarial sequence <span className="math-var">k</span>. Adjust <span className="math-var font-semibold">R</span> below or run a live call against the FastAPI verification engine to observe Alloy&apos;s pre-settlement gate.
              </p>

              {/* Interactive Parameter Proof Card */}
              <div className="bg-white border border-[#0B1F3A]/25 rounded-xl p-5 distill-card space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-200">
                  <div className="text-xs font-mono-tabular font-bold text-[#0B1F3A]">
                    SECTION 1.1 // INTERACTIVE INVARIANT EVALUATOR
                  </div>
                  <StatusBadge value={isSafe ? 'allow' : 'block'} />
                </div>

                <div className="space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono-tabular">
                    <label htmlFor="refund-slider" className="text-slate-700">
                      Attempted Refund <span className="math-var font-semibold">R</span>:{' '}
                      <strong className="text-[#0B1F3A]">${attemptedRefund.toFixed(2)}</strong>{' '}
                      <span className="text-slate-500">(Captured C = ${capturedAmount.toFixed(2)})</span>
                    </label>
                    <button
                      type="button"
                      onClick={() => void runLiveVerification()}
                      disabled={checking}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#0B1F3A] text-white text-xs font-medium hover:bg-[#14335c] disabled:opacity-50"
                    >
                      <Play className="w-3 h-3" />
                      {checking ? 'Verifying via API...' : 'Verify with Live API'}
                    </button>
                  </div>

                  <input
                    id="refund-slider"
                    type="range"
                    min={100}
                    max={1600}
                    step={50}
                    value={attemptedRefund}
                    onChange={(e) => {
                      setAttemptedRefund(Number(e.target.value))
                      setLiveResult(null)
                      setLiveGuardian(null)
                    }}
                    className="w-full accent-[#0B1F3A]"
                  />
                </div>

                <div className="grid grid-cols-3 gap-3 text-xs font-mono-tabular">
                  <div className="p-2.5 rounded bg-[#FAF9F6] border border-slate-200">
                    <div className="text-slate-500">Margin (<span className="math-var">C - R</span>)</div>
                    <div
                      className={`text-sm font-bold mt-0.5 ${
                        isSafe ? 'text-emerald-700' : 'text-rose-700'
                      }`}
                    >
                      {margin < 0 ? `-$${Math.abs(margin).toFixed(2)}` : `$${margin.toFixed(2)}`}
                    </div>
                  </div>
                  <div className="p-2.5 rounded bg-[#FAF9F6] border border-slate-200">
                    <div className="text-slate-500">Direct Exposure</div>
                    <div className="text-sm font-bold mt-0.5 text-[#0B1F3A]">
                      ${liveResult ? liveResult.total_direct_loss : localExposure.toFixed(2)}
                    </div>
                  </div>
                  <div className="p-2.5 rounded bg-[#FAF9F6] border border-slate-200">
                    <div className="text-slate-500">Invariant Verdict</div>
                    <div
                      className={`text-sm font-bold mt-0.5 ${
                        isSafe ? 'text-emerald-700' : 'text-rose-700'
                      }`}
                    >
                      {isSafe ? 'VERIFIED' : 'VIOLATION'}
                    </div>
                  </div>
                </div>

                {checkError && (
                  <div className="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-800">
                    {checkError}
                  </div>
                )}

                {liveResult && (
                  <div className="rounded border border-emerald-200 bg-emerald-50/70 px-3 py-2 text-xs font-mono-tabular text-[#0B1F3A] flex flex-wrap items-center justify-between gap-2">
                    <span>
                      Live API Confirmed · analysis={liveResult.analysis_id.slice(0, 8)} · violations=
                      {liveResult.violation_count}
                    </span>
                    <span className="font-bold">Guardian: {liveGuardian}</span>
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => onEnterWorkspace('overview')}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-[#0B1F3A] text-white text-sm font-medium hover:bg-[#14335c]"
                >
                  Launch Verification Workbench
                  <ArrowRight className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => onEnterWorkspace('simulations')}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-white border border-[#0B1F3A]/30 text-[#0B1F3A] text-sm font-medium hover:bg-slate-50"
                >
                  Run Adversarial Attack
                </button>
                <button
                  type="button"
                  onClick={() => onEnterWorkspace('documents')}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-white border border-[#0B1F3A]/30 text-[#0B1F3A] text-sm font-medium hover:bg-slate-50"
                >
                  Upload &amp; Reconcile Ledger
                </button>
              </div>
            </div>

            {/* Right Column: Margin Proof Note + Alloy Assurance Card */}
            <aside className="lg:col-span-5 space-y-4">
              <div className="bg-white border border-[#0B1F3A]/25 rounded-xl p-5 distill-card space-y-3.5 text-xs">
                <div className="font-mono-tabular font-bold text-[#0B1F3A] border-b border-slate-200 pb-2.5 flex items-center justify-between">
                  <span>MARGIN PROOF NOTE // SEC. 2.1</span>
                  <StatusBadge value="verified" />
                </div>

                <div className="p-3.5 rounded-lg bg-[#0B1F3A] text-slate-100 font-mono-tabular space-y-1.5">
                  <div>∀ e ∈ Trace: Balance(e) ≥ 0</div>
                  <div className="text-emerald-300">Precision: Decimal(18, 2)</div>
                  <div className="text-amber-300">AI Override: FORBIDDEN (advisory only)</div>
                </div>

                <p className="text-slate-600 leading-relaxed">
                  <strong>Alloy Decision Integration:</strong> Every interactive proof threshold compiles directly into deterministic <code className="font-mono-tabular text-[#0B1F3A]">FinancialContract</code> constraints evaluated on pre-settlement hooks with immutable audit logging.
                </p>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 font-mono-tabular">
                  <div className="p-2 rounded bg-[#FAF9F6] border border-slate-200">
                    <span className="text-slate-500 block">Backend Suite</span>
                    <strong className="text-[#0B1F3A]">1,195 Tests Passing</strong>
                  </div>
                  <div className="p-2 rounded bg-[#FAF9F6] border border-slate-200">
                    <span className="text-slate-500 block">Report Export</span>
                    <strong className="text-[#0B1F3A]">JSON · CSV · .MD</strong>
                  </div>
                </div>
              </div>

              <div className="bg-white border-l-4 border-[#0B1F3A] border-y border-r border-slate-200 rounded-r-xl p-4 text-xs space-y-1.5">
                <div className="font-mono-tabular font-bold text-[#0B1F3A]">
                  MARGIN NOTE // DETERMINISTIC SEPARATION
                </div>
                <p className="text-slate-600 leading-relaxed">
                  Bounded AI inspection tools summarize root causes from persisted traces and evidence, while deterministic <code className="font-mono-tabular">Decimal</code> evaluators remain the sole source of financial truth.
                </p>
              </div>
            </aside>
          </div>
        </section>

        {/* Interactive 6-Stage Proof Architecture */}
        <section className="bg-white/85 border-y border-[#0B1F3A]/15 py-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 space-y-6">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <div className="text-xs font-mono-tabular font-semibold uppercase tracking-wider text-[#047857]">
                  Axiomatic Pipeline Architecture
                </div>
                <h2 className="font-serif-editorial text-2xl font-bold text-[#0B1F3A] mt-1">
                  Six Verifiable Gates From Business Rule to Audit Dossier
                </h2>
              </div>
              <span className="text-xs font-mono-tabular text-slate-500">
                Select any stage to inspect endpoint &amp; open module
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2.5">
              {PIPELINE_STAGES.map((item) => {
                const active = item.step === activeStage
                return (
                  <button
                    key={item.step}
                    type="button"
                    onClick={() => setActiveStage(item.step)}
                    className={`text-left p-3.5 rounded-lg border transition ${
                      active
                        ? 'bg-[#0B1F3A] text-white border-[#0B1F3A]'
                        : 'bg-[#FAF9F6] text-[#0B1F3A] border-slate-300 hover:bg-white'
                    }`}
                  >
                    <div
                      className={`text-[11px] font-mono-tabular ${
                        active ? 'text-emerald-300' : 'text-slate-500'
                      }`}
                    >
                      {item.step} · {item.badge}
                    </div>
                    <div className="text-xs font-semibold mt-1">{item.title}</div>
                  </button>
                )
              })}
            </div>

            <div className="bg-[#0B1F3A] text-slate-100 rounded-xl p-5 flex flex-wrap items-center justify-between gap-4">
              <div className="space-y-1 max-w-3xl">
                <div className="text-xs font-mono-tabular text-emerald-300">
                  [STAGE {selectedStage.step}] {selectedStage.endpoint}
                </div>
                <div className="text-sm text-slate-100">{selectedStage.detail}</div>
              </div>
              <button
                type="button"
                onClick={() => onEnterWorkspace(selectedStage.section)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-white text-[#0B1F3A] text-xs font-semibold hover:bg-slate-100 shrink-0"
              >
                Open {selectedStage.title}
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </section>

        {/* Core Invariant Pillars */}
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
            <span>Financial Proof — Axiomatic Deterministic Financial Verification</span>
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
              Audit &amp; Security
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
    <div className="bg-white border border-[#0B1F3A]/20 rounded-xl p-5 space-y-2 distill-card">
      <Icon className="w-5 h-5 text-[#0B1F3A]" />
      <h3 className="font-serif-editorial text-sm font-bold text-[#0B1F3A]">{title}</h3>
      <p className="text-xs text-slate-600 leading-relaxed">{body}</p>
    </div>
  )
}
