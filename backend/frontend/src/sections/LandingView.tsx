import React, { useState } from 'react'
import {
  ArrowRight,
  CheckCircle2,
  FileCheck2,
  Flame,
  GitBranch,
  Layers,
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

const PERSONAS: Record<
  'engineering' | 'risk' | 'compliance',
  {
    label: string
    headline: string
    summary: string
    section: NavSection
    cta: string
    nodes: Array<{ title: string; metric: string; accent: string }>
  }
> = {
  engineering: {
    label: 'Payment Engineers',
    headline: 'Catch race conditions & double-refund bugs before they ship.',
    summary:
      'Compile natural-language payment contracts into deterministic state checks, inject 8 fault vectors, and shrink failing traces to minimal witnesses.',
    section: 'simulations',
    cta: 'Open Adversarial Simulator',
    nodes: [
      { title: 'Rule Compiler', metric: 'Typed Decimal AST', accent: 'border-[#ff6b57]' },
      { title: 'Fault Injector', metric: '8 Replay Vectors', accent: 'border-[#f5b74b]' },
      { title: 'Trace Shrinker', metric: 'Minimal Counterexample', accent: 'border-[#047857]' },
    ],
  },
  risk: {
    label: 'Risk & Finance Ops',
    headline: 'Quantify worst-case monetary exposure and stop over-payouts.',
    summary:
      'Translate every contract breach into exact Decimal exposure bounds, reconcile internal ledgers against provider files, and block unsafe disbursements.',
    section: 'analysis',
    cta: 'Inspect Blast Radius & Guardian',
    nodes: [
      { title: 'Ledger Recon', metric: 'SHA-256 Deduplicated', accent: 'border-[#1e40af]' },
      { title: 'Blast Radius', metric: 'Direct / Max Exposure', accent: 'border-[#ff6b57]' },
      { title: 'Runtime Guardian', metric: 'ALLOW / BLOCK / REVIEW', accent: 'border-[#8e2460]' },
    ],
  },
  compliance: {
    label: 'Audit & Compliance',
    headline: 'Produce deterministic, audit-ready proof dossiers without black boxes.',
    summary:
      'Attach cryptographic checksums to every claim, enforce zero-override boundaries on AI investigation summaries, and export JSON, CSV, or Markdown packets.',
    section: 'verification',
    cta: 'Launch Proof Builder',
    nodes: [
      { title: 'Evidence Vault', metric: '5 MB Signed Allowlist', accent: 'border-[#047857]' },
      { title: 'AI Sandbox', metric: 'ai_advisory_only = true', accent: 'border-[#f5b74b]' },
      { title: 'Audit Export', metric: 'JSON · CSV · Markdown', accent: 'border-[#0a1429]' },
    ],
  },
}

const WORKFLOW_NODES: Array<{
  step: string
  title: string
  tag: string
  endpoint: string
  detail: string
  section: NavSection
}> = [
  {
    step: '01',
    title: 'Contract Rules',
    tag: 'COMPILE',
    endpoint: 'POST /api/contracts/compile',
    detail: 'Turn policy text into deterministic constraints and save versioned contracts.',
    section: 'contracts',
  },
  {
    step: '02',
    title: 'Ledger Evidence',
    tag: 'RECONCILE',
    endpoint: 'POST /api/reconciliation/run',
    detail: 'Verify CSV/JSON/PDF digests and flag exact penny-level drift automatically.',
    section: 'documents',
  },
  {
    step: '03',
    title: 'Stress Replay',
    tag: '8 ATTACKS',
    endpoint: 'POST /api/simulations/{id}/attacks',
    detail: 'Attack payment state machines with duplicate, delayed, retry, and crash faults.',
    section: 'simulations',
  },
  {
    step: '04',
    title: 'Shrink Witness',
    tag: 'MINIMIZE',
    endpoint: 'POST /api/simulations/{id}/counterexamples/shrink',
    detail: 'Isolate the smallest sequence of events that triggers a violation.',
    section: 'simulations',
  },
  {
    step: '05',
    title: 'Blast Radius & AI',
    tag: 'EXPOSURE',
    endpoint: 'POST /api/blast-radius',
    detail: 'Measure monetary exposure and run read-only advisory root-cause diagnostics.',
    section: 'analysis',
  },
  {
    step: '06',
    title: 'Guardian & Proof',
    tag: 'ENFORCE',
    endpoint: 'POST /api/guardian/evaluate',
    detail: 'Gate live transactions with ALLOW/BLOCK/REVIEW decisions and export audit reports.',
    section: 'verification',
  },
]

export function LandingView({ systemStatus, onEnterWorkspace }: LandingViewProps) {
  const capturedAmount = 1000
  const [refundAmount, setRefundAmount] = useState(1250)
  const [persona, setPersona] = useState<'engineering' | 'risk' | 'compliance'>('engineering')
  const [activeNode, setActiveNode] = useState(WORKFLOW_NODES[0].step)
  const [liveResult, setLiveResult] = useState<BlastRadiusResult | null>(null)
  const [liveDecision, setLiveDecision] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const isSafe = refundAmount <= capturedAmount
  const localExposure = isSafe ? 0 : refundAmount
  const activePersona = PERSONAS[persona]
  const currentStage = WORKFLOW_NODES.find((w) => w.step === activeNode) ?? WORKFLOW_NODES[0]

  const runLiveDecision = async () => {
    setBusy(true)
    setError('')
    try {
      const [br, grd] = await Promise.all([
        platformApi.analyzeBlastRadius({
          source_text: 'Customer refund must not exceed the original payment amount.',
          payment_amount: capturedAmount.toFixed(2),
          refund_amount: refundAmount.toFixed(2),
          currency: 'USD',
          persist: false,
        }),
        platformApi.evaluateGuardian({
          operation: 'refund',
          actor_id: 'alloy-landing-sandbox',
          amount_minor: refundAmount * 100,
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
      setLiveDecision(`${grd.decision.toUpperCase()} · ${grd.rule}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification request failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen bg-white text-[#0a1429] flex flex-col">
      {/* Alloy Clean Sticky Header */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg alloy-accent-gradient text-[#0a1429] flex items-center justify-center text-xs font-extrabold font-mono-tabular">
              FP
            </div>
            <span className="text-base font-bold tracking-tight text-[#0a1429]">
              Financial Proof
            </span>
          </div>

          <nav className="hidden md:flex items-center gap-7 text-xs font-medium text-slate-600">
            <a href="#decisioning" className="hover:text-[#0a1429]">Platform</a>
            <a href="#solutions" className="hover:text-[#0a1429]">Solutions</a>
            <a href="#workflow" className="hover:text-[#0a1429]">Workflow</a>
            <a href="#trust" className="hover:text-[#0a1429]">Assurance</a>
          </nav>

          <div className="flex items-center gap-3">
            {systemStatus && (
              <div className="hidden lg:flex items-center gap-2 text-xs font-mono-tabular text-slate-500">
                <span>DB</span>
                <StatusBadge value={systemStatus.database} />
              </div>
            )}
            <button
              type="button"
              onClick={() => onEnterWorkspace('overview')}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-[#0a1429] text-white text-xs font-semibold hover:bg-slate-800 transition"
            >
              Launch Platform
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Asymmetric Hero Section */}
        <section id="decisioning" className="max-w-7xl mx-auto px-4 sm:px-6 pt-14 pb-16">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            {/* Left Bold Storytelling */}
            <div className="lg:col-span-6 space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-50 border border-rose-200 text-xs font-semibold text-[#8e2460]">
                <span className="w-2 h-2 rounded-full bg-[#ff6b57]" />
                Deterministic Financial Decisioning &amp; Proof Engine
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-[54px] font-bold tracking-tight text-[#0a1429] leading-[1.06]">
                Take control of payment risk before settlement moves.
              </h1>

              <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-xl">
                Connect your contracts, payment traces, and ledger feeds in one deterministic decisioning platform—built for engineering teams, finance operators, and auditors who cannot afford floating-point guesses.
              </p>

              <div className="flex flex-wrap gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => onEnterWorkspace('overview')}
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-[#0a1429] text-white text-sm font-semibold hover:bg-slate-800 transition shadow-sm"
                >
                  Open Decision Workbench
                  <ArrowRight className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => onEnterWorkspace('simulations')}
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-white border border-slate-300 text-[#0a1429] text-sm font-semibold hover:bg-slate-50 transition"
                >
                  Simulate Adversarial Attack
                </button>
              </div>
            </div>

            {/* Right Multi-Layered Decision Flow Visual + Live Engine Control */}
            <div className="lg:col-span-6 relative">
              <div className="rounded-3xl p-1 alloy-accent-gradient alloy-card">
                <div className="bg-[#0a1429] text-white rounded-[22px] p-6 space-y-5">
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-slate-800">
                    <div className="flex items-center gap-2">
                      <GitBranch className="w-4 h-4 text-[#ff6b57]" />
                      <span className="text-xs font-mono-tabular font-bold uppercase tracking-wider text-slate-200">
                        Live Decision Flow // Refund Policy
                      </span>
                    </div>
                    <StatusBadge value={isSafe ? 'allow' : 'block'} />
                  </div>

                  {/* Layered Node Strip */}
                  <div className="grid grid-cols-3 gap-2.5 text-xs">
                    <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-3 space-y-1">
                      <div className="text-[10px] font-mono-tabular text-[#f5b74b]">01 INPUT</div>
                      <div className="font-semibold">Captured</div>
                      <div className="font-mono-tabular text-slate-300">${capturedAmount.toFixed(2)}</div>
                    </div>
                    <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-3 space-y-1">
                      <div className="text-[10px] font-mono-tabular text-[#ff6b57]">02 ATTEMPT</div>
                      <div className="font-semibold">Refund Tx</div>
                      <div className="font-mono-tabular text-white">${refundAmount.toFixed(2)}</div>
                    </div>
                    <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-3 space-y-1">
                      <div className="text-[10px] font-mono-tabular text-emerald-400">03 OUTCOME</div>
                      <div className="font-semibold">{isSafe ? 'Safe Move' : 'Blocked'}</div>
                      <div className="font-mono-tabular text-slate-300">
                        Exp: ${liveResult ? liveResult.total_direct_loss : localExposure.toFixed(2)}
                      </div>
                    </div>
                  </div>

                  {/* Interactive Decision Slider + Live Engine Execution */}
                  <div className="rounded-xl bg-slate-900 border border-slate-800 p-4 space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono-tabular">
                      <label htmlFor="alloy-refund-range" className="text-slate-300">
                        Adjust Attempted Refund: <strong className="text-white">${refundAmount.toFixed(2)}</strong>
                      </label>
                      <button
                        type="button"
                        onClick={() => void runLiveDecision()}
                        disabled={busy}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#ff6b57] text-[#0a1429] text-xs font-bold hover:bg-[#ff8170] disabled:opacity-50 transition"
                      >
                        <Play className="w-3 h-3" />
                        {busy ? 'Evaluating...' : 'Test Live API'}
                      </button>
                    </div>
                    <input
                      id="alloy-refund-range"
                      type="range"
                      min={100}
                      max={1600}
                      step={50}
                      value={refundAmount}
                      onChange={(e) => {
                        setRefundAmount(Number(e.target.value))
                        setLiveResult(null)
                        setLiveDecision(null)
                      }}
                      className="w-full accent-[#ff6b57]"
                    />
                    {error && (
                      <div className="text-xs text-rose-300 font-mono-tabular">{error}</div>
                    )}
                    {liveResult && (
                      <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono-tabular text-emerald-300">
                        <span>API ID: {liveResult.analysis_id.slice(0, 8)}</span>
                        <span>{liveDecision}</span>
                      </div>
                    )}
                  </div>

                  <div className="text-[11px] font-mono-tabular text-slate-400 flex items-center justify-between">
                    <span>Deterministic Python Decimal(18,2)</span>
                    <span className="text-[#f5b74b]">AI Advisory Only · Zero Override</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Verified Guarantees Bar */}
        <section className="bg-[#f8f9fc] border-y border-slate-200 py-6">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 grid grid-cols-2 md:grid-cols-5 gap-4 text-center text-xs">
            <div className="p-2">
              <div className="font-mono-tabular font-bold text-base text-[#0a1429]">1,198</div>
              <div className="text-slate-500 mt-0.5">Passing Automated Tests</div>
            </div>
            <div className="p-2">
              <div className="font-mono-tabular font-bold text-base text-[#0a1429]">Decimal</div>
              <div className="text-slate-500 mt-0.5">Zero Float Monetary Drift</div>
            </div>
            <div className="p-2">
              <div className="font-mono-tabular font-bold text-base text-[#0a1429]">8 Vectors</div>
              <div className="text-slate-500 mt-0.5">Adversarial Fault Matrix</div>
            </div>
            <div className="p-2">
              <div className="font-mono-tabular font-bold text-base text-[#0a1429]">SHA-256</div>
              <div className="text-slate-500 mt-0.5">Evidence Deduplication</div>
            </div>
            <div className="col-span-2 md:col-span-1 p-2">
              <div className="font-mono-tabular font-bold text-base text-[#047857]">PostgreSQL</div>
              <div className="text-slate-500 mt-0.5">Alembic Revision b1c2d3e4f5a6</div>
            </div>
          </div>
        </section>

        {/* Persona-Driven Solutions Switcher (Alloy Signature Pattern) */}
        <section id="solutions" className="max-w-7xl mx-auto px-4 sm:px-6 py-16 space-y-8">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div className="space-y-2 max-w-2xl">
              <div className="text-xs font-semibold uppercase tracking-wider text-[#8e2460]">
                Built for Every Verification Stakeholder
              </div>
              <h2 className="text-3xl font-bold tracking-tight text-[#0a1429]">
                One decision layer across engineering, risk, and audit.
              </h2>
            </div>

            <div className="inline-flex rounded-full bg-slate-100 p-1 border border-slate-200">
              {(['engineering', 'risk', 'compliance'] as const).map((key) => {
                const active = persona === key
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setPersona(key)}
                    className={`px-4 py-2 rounded-full text-xs font-semibold transition ${
                      active
                        ? 'bg-[#0a1429] text-white shadow-xs'
                        : 'text-slate-600 hover:text-[#0a1429]'
                    }`}
                  >
                    {PERSONAS[key].label}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="rounded-3xl bg-[#f8f9fc] border border-slate-200 p-6 sm:p-8 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-5 space-y-4">
              <h3 className="text-2xl font-bold text-[#0a1429] leading-snug">
                {activePersona.headline}
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                {activePersona.summary}
              </p>
              <button
                type="button"
                onClick={() => onEnterWorkspace(activePersona.section)}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#0a1429] text-white text-xs font-semibold hover:bg-slate-800 transition"
              >
                {activePersona.cta}
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-3 gap-4">
              {activePersona.nodes.map((node) => (
                <div
                  key={node.title}
                  className={`bg-white border border-slate-200 border-t-4 ${node.accent} rounded-2xl p-5 alloy-card space-y-2`}
                >
                  <Layers className="w-4 h-4 text-[#0a1429]" />
                  <div className="text-sm font-bold text-[#0a1429]">{node.title}</div>
                  <div className="text-xs font-mono-tabular text-slate-600">{node.metric}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Alloy Deep-Gradient Multi-Step Verification Workflow */}
        <section id="workflow" className="alloy-gradient-band text-white py-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 space-y-8">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div className="max-w-2xl space-y-2">
                <div className="text-xs font-mono-tabular uppercase tracking-wider text-[#f5b74b]">
                  End-to-End Decision Architecture
                </div>
                <h2 className="text-3xl font-bold tracking-tight">
                  Inspect any verification node in the execution chain.
                </h2>
              </div>
              <button
                type="button"
                onClick={() => onEnterWorkspace(currentStage.section)}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#ff6b57] text-[#0a1429] text-xs font-bold hover:bg-[#ff8170] transition"
              >
                Open {currentStage.title}
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {WORKFLOW_NODES.map((item) => {
                const active = item.step === activeNode
                return (
                  <button
                    key={item.step}
                    type="button"
                    onClick={() => setActiveNode(item.step)}
                    className={`text-left p-4 rounded-2xl border transition ${
                      active
                        ? 'bg-white text-[#0a1429] border-white shadow-lg'
                        : 'bg-white/10 text-white border-white/15 hover:bg-white/15'
                    }`}
                  >
                    <div
                      className={`text-[11px] font-mono-tabular font-bold ${
                        active ? 'text-[#8e2460]' : 'text-[#f5b74b]'
                      }`}
                    >
                      {item.step} · {item.tag}
                    </div>
                    <div className="text-sm font-bold mt-1">{item.title}</div>
                  </button>
                )
              })}
            </div>

            <div className="rounded-2xl bg-slate-950/50 border border-white/15 p-5 flex flex-wrap items-center justify-between gap-4">
              <div className="space-y-1 max-w-3xl">
                <div className="text-xs font-mono-tabular text-[#ff6b57]">
                  {currentStage.endpoint}
                </div>
                <p className="text-sm text-slate-200">{currentStage.detail}</p>
              </div>
              <button
                type="button"
                onClick={() => onEnterWorkspace(currentStage.section)}
                className="px-4 py-2 rounded-full border border-white/25 text-xs font-semibold hover:bg-white/10"
              >
                Launch Module -&gt;
              </button>
            </div>
          </div>
        </section>

        {/* Assurance Pillars */}
        <section id="trust" className="max-w-7xl mx-auto px-4 sm:px-6 py-16 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <FeatureCard
            icon={Scale}
            accent="text-[#1e40af]"
            title="Decimal Monetary Math"
            body="All monetary arithmetic runs on Python Decimal and integer minor units—never IEEE-754 floats."
          />
          <FeatureCard
            icon={Sparkles}
            accent="text-[#8e2460]"
            title="AI Never Overrides Truth"
            body="Bounded AI inspection tools summarize persisted traces while deterministic contracts hold final authority."
          />
          <FeatureCard
            icon={Flame}
            accent="text-[#ff6b57]"
            title="Quantified Blast Radius"
            body="Translate constraint breaches directly into direct loss, refund overage, and duplicate-charge risk."
          />
          <FeatureCard
            icon={Lock}
            accent="text-[#047857]"
            title="Fail-Closed Security"
            body="Strict extension allowlists, SHA-256 deduplication, Bearer auth guards, and HTTP security headers."
          />
        </section>
      </main>

      <footer className="bg-[#0a1429] text-slate-300 border-t border-slate-800 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span className="font-semibold text-white">Financial Proof</span>
            <span className="text-slate-400">· Deterministic Financial Verification &amp; Decisioning</span>
          </div>
          <div className="flex items-center gap-5">
            <button
              type="button"
              onClick={() => onEnterWorkspace('contracts')}
              className="hover:text-white inline-flex items-center gap-1"
            >
              <ShieldCheck className="w-3.5 h-3.5" /> Contracts
            </button>
            <button
              type="button"
              onClick={() => onEnterWorkspace('verification')}
              className="hover:text-white inline-flex items-center gap-1"
            >
              <FileCheck2 className="w-3.5 h-3.5" /> Proof Export
            </button>
            <button
              type="button"
              onClick={() => onEnterWorkspace('audit')}
              className="hover:text-white"
            >
              Audit &amp; Access
            </button>
          </div>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({
  icon: Icon,
  accent,
  title,
  body,
}: {
  icon: React.ComponentType<{ className?: string }>
  accent: string
  title: string
  body: string
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 space-y-2.5 alloy-card">
      <Icon className={`w-5 h-5 ${accent}`} />
      <h3 className="text-sm font-bold text-[#0a1429]">{title}</h3>
      <p className="text-xs text-slate-600 leading-relaxed">{body}</p>
    </div>
  )
}
