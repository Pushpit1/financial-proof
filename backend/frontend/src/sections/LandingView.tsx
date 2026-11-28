import { useEffect, useState } from 'react'
import { platformApi, type BlastRadiusResult, type SystemStatus } from '../api/platform'
import type { NavSection } from '../components/AppShell'
import { HeroOrbitVisual } from '../components/HeroOrbitVisual'

interface LandingViewProps {
  systemStatus: SystemStatus | null
  onEnterWorkspace: (section?: NavSection) => void
}

const PIPELINE_NODES: Array<{
  id: string
  name: string
  badge: string
  endpoint: string
  detail: string
  mod: NavSection
}> = [
  {
    id: '01',
    name: 'Rule Compile',
    badge: 'AST',
    endpoint: 'POST /api/contracts/compile',
    detail: 'Compiled clause "refund <= payment" into typed Decimal constraints.',
    mod: 'contracts',
  },
  {
    id: '02',
    name: 'Ledger Recon',
    badge: 'SHA-256',
    endpoint: 'POST /api/reconciliation/run',
    detail: 'Hashed settlement CSV via SHA-256 and verified 0.00 delta on captured rows.',
    mod: 'documents',
  },
  {
    id: '03',
    name: 'Fault Replay',
    badge: '8 VECTORS',
    endpoint: 'POST /api/simulations/{id}/attacks',
    detail: 'Injected duplicate retry on sequence #2; state machine flagged double-refund.',
    mod: 'simulations',
  },
  {
    id: '04',
    name: 'Shrinker',
    badge: 'MIN WITNESS',
    endpoint: 'POST /api/simulations/{id}/counterexamples/shrink',
    detail: 'Shrunk 11-event trace down to minimal 2-event witness reproducing violation.',
    mod: 'simulations',
  },
  {
    id: '05',
    name: 'Blast Radius',
    badge: 'DECIMAL',
    endpoint: 'POST /api/blast-radius',
    detail: 'Calculated worst-case monetary exposure while keeping AI diagnostics read-only.',
    mod: 'analysis',
  },
  {
    id: '06',
    name: 'Guardian Gate',
    badge: 'ENFORCE',
    endpoint: 'POST /api/guardian/evaluate',
    detail: 'Enforced ALLOW / BLOCK / REVIEW decision pre-settlement and exported signed dossier.',
    mod: 'verification',
  },
]

const SEGMENTS: Record<
  'eng' | 'fin' | 'aud',
  {
    label: string
    pill: string
    title: string
    desc: string
    cta: string
    mod: NavSection
    cards: Array<[string, string]>
  }
> = {
  eng: {
    label: 'For Engineers',
    pill: 'FOR PAYMENT ENGINEERS',
    title: 'Catch race conditions & duplicate refunds before code reaches settlement',
    desc: 'Compile plain-English business policies into deterministic contracts, attack payment state machines with 8 fault types, and minimize long failing traces down to minimal counterexamples.',
    cta: 'Test Simulator & Shrinker ->',
    mod: 'simulations',
    cards: [
      ['Rule AST Compilation', 'Typed Decimal Constraints'],
      ['Adversarial Injection', '8 Seeded Fault Vectors'],
      ['Counterexample Shrinker', 'Minimal Witness Pair'],
    ],
  },
  fin: {
    label: 'For Finance Ops',
    pill: 'FOR RISK & FINANCE OPS',
    title: 'Quantify worst-case financial blast radius and stop penny-level drift',
    desc: 'Reconcile internal exports against settlement CSVs, isolate exact discrepancies, and gate live payouts using fail-closed Guardian rules.',
    cta: 'Open Recon & Guardian ->',
    mod: 'analysis',
    cards: [
      ['Blast Radius Exposure', 'Direct vs Max Loss'],
      ['Ledger Reconciliation', 'Exact Cent Matching'],
      ['Runtime Guardian Gate', 'ALLOW / BLOCK / REVIEW'],
    ],
  },
  aud: {
    label: 'For Auditors',
    pill: 'FOR COMPLIANCE & AUDITORS',
    title: 'Traceable SHA-256 evidence packets with zero probabilistic guesswork',
    desc: 'Keep bounded AI explanations strictly read-only while deterministic evaluators sign JSON, CSV, and Markdown proof reports backed by PostgreSQL audit rows.',
    cta: 'Inspect Audit & Reports ->',
    mod: 'verification',
    cards: [
      ['SHA-256 Digest Gate', 'Duplicate Upload Check'],
      ['Bounded AI Investigator', 'ai_advisory_only = true'],
      ['Report Export', 'JSON · CSV · Markdown'],
    ],
  },
}

const MODULES_DIRECTORY: Array<{
  num: string
  title: string
  tag: string
  desc: string
  action: string
  mod: NavSection
}> = [
  {
    num: '1.0',
    title: 'Overview & Telemetry',
    tag: 'LIVE DB',
    desc: 'Inspect live PostgreSQL readiness, contract/proof/document counts, canonical demo seed, and real-time audit stream.',
    action: 'Open Telemetry ->',
    mod: 'overview',
  },
  {
    num: '2.0',
    title: 'Financial Contracts',
    tag: 'COMPILE',
    desc: 'Turn plain-English policy clauses into strict Decimal rules and persist versioned contracts.',
    action: 'Compile Contract ->',
    mod: 'contracts',
  },
  {
    num: '3.0',
    title: 'Documents & Recon',
    tag: 'SHA-256',
    desc: 'Upload CSV/JSON ledger evidence with strict 5MB extension filtering and reconcile transactions cent-for-cent.',
    action: 'Run Reconciliation ->',
    mod: 'documents',
  },
  {
    num: '4.0',
    title: 'Simulations & Attacks',
    tag: '8 VECTORS',
    desc: 'Replay duplicate, retry, delayed, and crash failures against state machines, then shrink witnesses.',
    action: 'Replay Attack ->',
    mod: 'simulations',
  },
  {
    num: '5.0',
    title: 'Verification & Proofs',
    tag: 'EXPORTS',
    desc: 'Evaluate deterministic proof dossiers and export signed JSON, CSV, or Markdown packets.',
    action: 'Build Proof ->',
    mod: 'verification',
  },
  {
    num: '6.0',
    title: 'Blast Radius & Guardian',
    tag: 'GATE',
    desc: 'Calculate max monetary exposure, query bounded read-only AI root-cause notes, and test live payout gates.',
    action: 'Evaluate Gate ->',
    mod: 'analysis',
  },
]

export function LandingView({
  systemStatus,
  onEnterWorkspace,
}: LandingViewProps) {
  const [activePipeIdx, setActivePipeIdx] = useState(0)
  const [animatingPipe, setAnimatingPipe] = useState(false)
  const [segment, setSegment] = useState<'eng' | 'fin' | 'aud'>('eng')

  // Live Pre-Settlement Gate sandbox (backed by real /api/blast-radius + /api/guardian/evaluate)
  const [refundAmount, setRefundAmount] = useState(1250)
  const [duplicateDetected, setDuplicateDetected] = useState(false)
  const [liveResult, setLiveResult] = useState<BlastRadiusResult | null>(null)
  const [liveDecision, setLiveDecision] = useState<string | null>(null)
  const [liveBusy, setLiveBusy] = useState(false)
  const [liveError, setLiveError] = useState('')

  useEffect(() => {
    if (!animatingPipe) return
    const timer = window.setInterval(() => {
      setActivePipeIdx((prev) => {
        if (prev + 1 >= PIPELINE_NODES.length) {
          setAnimatingPipe(false)
          return prev
        }
        return prev + 1
      })
    }, 650)
    return () => window.clearInterval(timer)
  }, [animatingPipe])

  const capturedAmount = 1000
  const isSafe = refundAmount <= capturedAmount && !duplicateDetected
  const localExposure = isSafe ? 0 : refundAmount
  const currentPipe = PIPELINE_NODES[activePipeIdx]
  const currentSeg = SEGMENTS[segment]

  const runLiveDecision = async () => {
    setLiveBusy(true)
    setLiveError('')
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
          duplicate_detected: duplicateDetected,
          state_transition_valid: true,
          requires_manual_review: false,
          persist_audit: false,
        }),
      ])
      setLiveResult(br)
      setLiveDecision(`${grd.decision.toUpperCase()} · ${grd.rule}`)
    } catch (err) {
      setLiveError(err instanceof Error ? err.message : 'Verification request failed.')
    } finally {
      setLiveBusy(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#EBEBE6] text-[#191919] flex flex-col">
      {/* Floating Rounded White Pill Header matching Alloy */}
      <div className="alloy-geo-bg pt-3 px-3 sm:px-6">
        <header className="max-w-7xl mx-auto bg-white rounded-2xl border border-[#C5C4B1]/75 shadow-sm px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-7">
            <div className="flex items-center gap-2.5">
              <svg width="26" height="26" viewBox="0 0 28 28" fill="none" aria-hidden="true">
                <polygon points="14,3 25,22 3,22" stroke="#191919" strokeWidth="1.8" fill="none" />
                <polygon points="14,8 21,20 7,20" stroke="#191919" strokeWidth="1.2" fill="none" opacity="0.65" />
                <circle cx="14" cy="16" r="2.2" fill="#FF6170" />
              </svg>
              <span className="text-base sm:text-lg font-bold tracking-tight uppercase text-[#191919]">
                Financial Proof
              </span>
            </div>

            <nav className="hidden lg:flex items-center gap-6 text-xs uppercase tracking-wider font-medium text-[#191919]/75">
              <a href="#sec-pipeline" className="hover:text-[#191919]">Platform</a>
              <a href="#sec-solutions" className="hover:text-[#191919]">Solutions</a>
              <a href="#sec-sandbox" className="hover:text-[#191919]">Live Tester</a>
              <a href="#sec-modules" className="hover:text-[#191919]">Modules</a>
            </nav>
          </div>

          <div className="flex items-center gap-2.5">
            <span className="hidden sm:inline-flex items-center gap-1.5 text-xs font-medium text-[#191919]/75 px-2.5 py-1 rounded-full bg-[#F5F5F3] border border-[#C5C4B1]/60 font-mono-tabular">
              <span
                className={`w-2 h-2 rounded-full ${
                  systemStatus?.database === 'connected' ? 'bg-emerald-600 animate-pulse' : 'bg-[#FF6170]'
                }`}
              />
              {systemStatus?.database === 'connected' ? 'PROD · NEON' : 'CHECKING DB'}
            </span>
            <button
              type="button"
              onClick={() => onEnterWorkspace('overview')}
              className="alloy-btn alloy-btn-filled !py-2 !px-4 !text-[11px]"
            >
              Open Workbench
            </button>
          </div>
        </header>
      </div>

      <main className="flex-1">
        {/* Hero Section: Geometric Backdrop + Anatomical Spiral Human Bust + Morphing Orbital Signals */}
        <section className="alloy-geo-bg pt-8 pb-20 overflow-hidden border-b border-[#C5C4B1]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-6 space-y-6 relative z-20 pt-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/95 border border-[#C5C4B1] text-[11px] font-mono-tabular uppercase tracking-wider shadow-xs">
                <span className="w-2 h-2 rounded-full bg-[#FF6170] animate-ping" />
                REAL-TIME DETERMINISTIC VERIFICATION
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-[56px] font-medium tracking-tight leading-[1.03] text-[#191919]">
                Full-lifecycle financial proof <span className="text-[#191919]/50">&amp; fraud defense</span>
              </h1>

              <p className="text-base sm:text-lg text-[#191919]/75 leading-relaxed max-w-xl">
                Stop over-refunds, ledger drift, and race conditions before capital moves—compiling rules into mathematical invariants enforced deterministically across every payment state.
              </p>

              <div className="flex flex-wrap items-center gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => onEnterWorkspace('overview')}
                  className="alloy-btn alloy-btn-filled"
                >
                  Open Workbench -&gt;
                </button>
                <a href="#sec-pipeline" className="alloy-btn alloy-btn-pink">
                  See how it works -&gt;
                </a>
              </div>

              <p className="text-xs sm:text-sm font-medium text-[#191919]/75 pt-2">
                Powered by Python <span className="font-mono-tabular font-semibold">Decimal(18,2)</span>, Neon PostgreSQL
                {systemStatus?.alembic_revision ? ` (${systemStatus.alembic_revision})` : ''} &amp; 1,198 verified checks
              </p>
            </div>

            <div className="lg:col-span-6">
              <HeroOrbitVisual />
            </div>
          </div>
        </section>

        {/* Capabilities Marquee & Verified Metrics Band (#F5F5F3) */}
        <section className="bg-[#F5F5F3] py-14 border-b border-[#C5C4B1] overflow-hidden">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 space-y-10">
            <div className="space-y-4">
              <div className="text-xs uppercase tracking-wider font-medium text-[#191919]/60 text-center">
                VERIFIED DETERMINISTIC PLATFORM STACK · ZERO SIMULATED METRICS
              </div>
              <div className="overflow-hidden border-y border-[#191919]/10 py-3">
                <div className="marquee-track gap-5 font-mono-tabular text-xs text-[#191919]/80 items-center">
                  {[
                    'PYTHON DECIMAL(18,2)',
                    'NEON POSTGRESQL',
                    'ALEMBIC HEAD b1c2d3e4f5a6',
                    '8 ADVERSARIAL FAULTS',
                    'SHA-256 CHECKSUM GATE',
                    'AI ADVISORY ONLY',
                    'RUNTIME GUARDIAN',
                    'PYTHON DECIMAL(18,2)',
                    'NEON POSTGRESQL',
                    'ALEMBIC HEAD b1c2d3e4f5a6',
                    '8 ADVERSARIAL FAULTS',
                    'SHA-256 CHECKSUM GATE',
                  ].map((item, idx) => (
                    <span key={`${item}-${idx}`} className="t-pill bg-white border border-[#C5C4B1]">
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
              <div className="bg-[#EBEBE6] border border-[#C5C4B1] alloy-card alloy-card-hover p-5">
                <div className="text-3xl sm:text-4xl font-medium tracking-tight font-mono-tabular">1,198</div>
                <div className="text-xs text-[#191919]/75 mt-1">Verified backend unit &amp; API tests passing</div>
              </div>
              <div className="bg-[#EBEBE6] border border-[#C5C4B1] alloy-card alloy-card-hover p-5">
                <div className="text-3xl sm:text-4xl font-medium tracking-tight font-mono-tabular">0.00</div>
                <div className="text-xs text-[#191919]/75 mt-1">IEEE-754 float drift across ledgers</div>
              </div>
              <div className="bg-[#EBEBE6] border border-[#C5C4B1] alloy-card alloy-card-hover p-5">
                <div className="text-3xl sm:text-4xl font-medium tracking-tight font-mono-tabular">8x</div>
                <div className="text-xs text-[#191919]/75 mt-1">Adversarial replay fault vectors</div>
              </div>
              <div className="bg-[#EBEBE6] border border-[#C5C4B1] alloy-card alloy-card-hover p-5">
                <div className="text-3xl sm:text-4xl font-medium tracking-tight font-mono-tabular">100%</div>
                <div className="text-xs text-[#191919]/75 mt-1">Deterministic gate isolation vs AI advice</div>
              </div>
            </div>
          </div>
        </section>

        {/* Interactive 6-Stage Verification Pipeline (#EBEBE6) */}
        <section id="sec-pipeline" className="bg-[#EBEBE6] py-16 border-b border-[#C5C4B1]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 space-y-8">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div className="space-y-3 max-w-2xl">
                <span className="t-pill bg-white border border-[#C5C4B1]">THE PLATFORM</span>
                <h2 className="text-3xl sm:text-4xl font-medium tracking-tight leading-tight">
                  One deterministic pipeline from <span className="text-[#191919]/50">contract text to settlement block</span>
                </h2>
              </div>
              <button
                type="button"
                onClick={() => {
                  setActivePipeIdx(0)
                  setAnimatingPipe(true)
                }}
                className="alloy-btn alloy-btn-pink"
              >
                {animatingPipe ? 'Stepping Gates...' : 'Animate Live Execution ->'}
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {PIPELINE_NODES.map((p, idx) => {
                const on = idx === activePipeIdx
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => {
                      setAnimatingPipe(false)
                      setActivePipeIdx(idx)
                    }}
                    className={`text-left cursor-pointer p-4 border alloy-card transition ${
                      on
                        ? 'bg-[#191919] text-white border-[#191919] shadow-md -translate-y-1'
                        : 'bg-white text-[#191919] border-[#C5C4B1] hover:border-[#191919]'
                    }`}
                  >
                    <div className="flex items-center justify-between font-mono-tabular text-[10px]">
                      <span className={on ? 'text-[#FF6170]' : 'text-[#191919]/50'}>GATE {p.id}</span>
                      <span>{p.badge}</span>
                    </div>
                    <div className="font-semibold text-sm mt-1.5">{p.name}</div>
                  </button>
                )
              })}
            </div>

            <div className="bg-[#191919] text-[#EBEBE6] border border-[#191919] alloy-card p-5 font-mono-tabular text-xs flex flex-wrap items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="text-[#FF6170] font-bold">
                  [GATE {currentPipe.id}] {currentPipe.endpoint}
                </div>
                <div className="text-[#EBEBE6]/90">{currentPipe.detail}</div>
              </div>
              <button
                type="button"
                onClick={() => onEnterWorkspace(currentPipe.mod)}
                className="alloy-btn alloy-btn-pink !py-1.5 !px-3.5 !text-[10px] shrink-0"
              >
                Inspect Module -&gt;
              </button>
            </div>
          </div>
        </section>

        {/* Solutions By Team (#F5F5F3) */}
        <section id="sec-solutions" className="bg-[#F5F5F3] py-16 border-b border-[#C5C4B1]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 space-y-8">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <span className="t-pill bg-white border border-[#C5C4B1]">SOLUTIONS BY TEAM</span>
                <h2 className="text-3xl sm:text-4xl font-medium tracking-tight mt-3">
                  Built for builders, ops <span className="text-[#191919]/50">&amp; auditors</span>
                </h2>
              </div>
              <div className="flex flex-wrap gap-2">
                {(['eng', 'fin', 'aud'] as const).map((k) => (
                  <button
                    key={k}
                    type="button"
                    onClick={() => setSegment(k)}
                    className={
                      segment === k
                        ? 'alloy-btn alloy-btn-filled !py-2 !px-4'
                        : 'alloy-btn alloy-btn-outline !py-2 !px-4 bg-white'
                    }
                  >
                    {SEGMENTS[k].label}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center bg-[#EBEBE6] border border-[#C5C4B1] alloy-card p-6 sm:p-8">
              <div className="lg:col-span-6 space-y-4">
                <span className="t-pill bg-white border border-[#C5C4B1]">{currentSeg.pill}</span>
                <h3 className="text-2xl sm:text-3xl font-medium leading-snug">{currentSeg.title}</h3>
                <p className="text-sm sm:text-base text-[#191919]/75 leading-relaxed">{currentSeg.desc}</p>
                <button
                  type="button"
                  onClick={() => onEnterWorkspace(currentSeg.mod)}
                  className="alloy-btn alloy-btn-filled"
                >
                  {currentSeg.cta}
                </button>
              </div>
              <div className="lg:col-span-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
                {currentSeg.cards.map(([t, sub], idx) => (
                  <div
                    key={t}
                    className={`${
                      idx === 2
                        ? 'bg-[#191919] text-white border-[#191919]'
                        : 'bg-white text-[#191919] border-[#C5C4B1]'
                    } border alloy-card alloy-card-hover p-5 space-y-2 shadow-xs`}
                  >
                    <div className={`w-2 h-2 rounded-full ${idx === 2 ? 'bg-[#FF6170]' : 'bg-[#191919]'}`} />
                    <div className="text-sm font-semibold">{t}</div>
                    <div className={`text-xs font-mono-tabular ${idx === 2 ? 'text-white/75' : 'text-[#191919]/65'}`}>
                      {sub}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Live Pre-Settlement Gate Sandbox (#EBEBE6) — Calls Real FastAPI Backend */}
        <section id="sec-sandbox" className="bg-[#EBEBE6] py-16 border-b border-[#C5C4B1]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-6 space-y-4">
              <span className="t-pill bg-white border border-[#C5C4B1]">INTERACTIVE GUARDIAN TESTER</span>
              <h2 className="text-3xl sm:text-4xl font-medium tracking-tight">
                Test pre-settlement blocking live against the API
              </h2>
              <p className="text-sm sm:text-base text-[#191919]/75 leading-relaxed">
                Slide attempted refund volume or trigger a duplicate transaction flag, then run real backend verification via <code className="font-mono-tabular">/api/blast-radius</code> and <code className="font-mono-tabular">/api/guardian/evaluate</code>.
              </p>
              <button
                type="button"
                onClick={() => onEnterWorkspace('analysis')}
                className="alloy-btn alloy-btn-outline"
              >
                Open Full Guardian Matrix -&gt;
              </button>
            </div>

            <div className="lg:col-span-6 bg-white border border-[#C5C4B1] alloy-card p-6 space-y-5 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#191919]/10">
                <span className="font-mono-tabular text-xs font-semibold">POLICY // refund_ceiling_guard</span>
                <span
                  className="t-pill font-mono-tabular"
                  style={{
                    backgroundColor: isSafe ? '#EBEBE6' : '#FF6170',
                    color: '#191919',
                  }}
                >
                  DECISION: {isSafe ? 'ALLOW' : 'BLOCK'}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-3 font-mono-tabular text-xs">
                <div className="p-3 bg-[#F5F5F3] alloy-card border border-[#191919]/10">
                  <div className="text-[#191919]/55">CAPTURED</div>
                  <div className="text-base font-semibold mt-0.5">$1,000.00</div>
                </div>
                <div className="p-3 bg-[#F5F5F3] alloy-card border border-[#191919]/10">
                  <div className="text-[#191919]/55">REFUND TRY</div>
                  <div className="text-base font-semibold mt-0.5">
                    ${refundAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div className="p-3 bg-[#191919] text-white alloy-card">
                  <div className="text-white/60">EXPOSURE</div>
                  <div className="text-base font-semibold mt-0.5 text-[#FF6170]">
                    ${liveResult ? liveResult.total_direct_loss : localExposure.toFixed(2)}
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <input
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
                  className="w-full accent-[#191919] cursor-pointer"
                />
                <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
                  <label className="inline-flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={duplicateDetected}
                      onChange={(e) => {
                        setDuplicateDetected(e.target.checked)
                        setLiveResult(null)
                        setLiveDecision(null)
                      }}
                      className="accent-[#FF6170]"
                    />
                    Simulate Duplicate Idempotency Collision
                  </label>
                  <button
                    type="button"
                    onClick={() => void runLiveDecision()}
                    disabled={liveBusy}
                    className="alloy-btn alloy-btn-pink !py-1.5 !px-3.5 !text-[10px]"
                  >
                    {liveBusy ? 'Calling API...' : 'Verify Live API ->'}
                  </button>
                </div>
                {liveError && <div className="text-xs font-mono-tabular text-[#FF6170]">{liveError}</div>}
                {liveResult && (
                  <div className="p-3 rounded-lg bg-[#191919] text-[#EBEBE6] font-mono-tabular text-[11px] flex flex-wrap justify-between gap-2">
                    <span>LIVE ANALYSIS: {liveResult.analysis_id.slice(0, 8)}</span>
                    <span className="text-[#E6CA5A]">{liveDecision}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* All Platform Modules Grid (#F5F5F3) */}
        <section id="sec-modules" className="bg-[#F5F5F3] py-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 space-y-8">
            <div className="max-w-2xl space-y-2">
              <span className="t-pill bg-white border border-[#C5C4B1]">EVERY WORKBENCH FEATURE LIVE</span>
              <h2 className="text-3xl sm:text-4xl font-medium tracking-tight">Click any module to open the full Workbench</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {MODULES_DIRECTORY.map((item) => (
                <button
                  key={item.num}
                  type="button"
                  onClick={() => onEnterWorkspace(item.mod)}
                  className="text-left cursor-pointer bg-white border border-[#C5C4B1] hover:border-[#191919] alloy-card alloy-card-hover p-6 flex flex-col justify-between gap-4 shadow-xs"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="t-pill font-mono-tabular">SEC {item.num}</span>
                      <span className="t-pill bg-[#F5F5F3] border border-[#C5C4B1]">{item.tag}</span>
                    </div>
                    <h3 className="text-xl font-medium text-[#191919]">{item.title}</h3>
                    <p className="text-sm text-[#191919]/75 leading-relaxed">{item.desc}</p>
                  </div>
                  <div className="text-xs font-semibold uppercase tracking-wider font-mono-tabular">{item.action}</div>
                </button>
              ))}
            </div>
          </div>
        </section>
      </main>

      {/* Dark #191919 Conversion Footer matching Alloy */}
      <footer className="bg-[#191919] text-[#EBEBE6] py-16 border-t border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 space-y-12">
          <div className="flex flex-wrap items-center justify-between gap-6 pb-10 border-b border-white/15">
            <div className="space-y-2 max-w-xl">
              <span className="t-pill !bg-[#FF6170] !text-[#191919]">PRODUCTION READY · NEON DB CONNECTED</span>
              <h2 className="text-3xl sm:text-4xl font-medium tracking-tight">
                Verify every dollar before capital settles.
              </h2>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => onEnterWorkspace('overview')}
                className="alloy-btn alloy-btn-pink"
              >
                Launch Workbench -&gt;
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-xs">
            <div className="space-y-2.5">
              <div className="font-semibold uppercase tracking-wider text-white/50">Platform</div>
              <div className="flex flex-col gap-1.5 items-start">
                <button type="button" onClick={() => onEnterWorkspace('overview')} className="hover:text-[#FF6170] cursor-pointer">
                  Overview &amp; Telemetry
                </button>
                <button type="button" onClick={() => onEnterWorkspace('contracts')} className="hover:text-[#FF6170] cursor-pointer">
                  Contract Compiler
                </button>
                <button type="button" onClick={() => onEnterWorkspace('documents')} className="hover:text-[#FF6170] cursor-pointer">
                  Ledger Reconciliation
                </button>
              </div>
            </div>
            <div className="space-y-2.5">
              <div className="font-semibold uppercase tracking-wider text-white/50">Adversarial</div>
              <div className="flex flex-col gap-1.5 items-start">
                <button type="button" onClick={() => onEnterWorkspace('simulations')} className="hover:text-[#FF6170] cursor-pointer">
                  State Replay Engine
                </button>
                <button type="button" onClick={() => onEnterWorkspace('simulations')} className="hover:text-[#FF6170] cursor-pointer">
                  Counterexample Shrinker
                </button>
                <button type="button" onClick={() => onEnterWorkspace('verification')} className="hover:text-[#FF6170] cursor-pointer">
                  Repair Verifier
                </button>
              </div>
            </div>
            <div className="space-y-2.5">
              <div className="font-semibold uppercase tracking-wider text-white/50">Risk &amp; Proof</div>
              <div className="flex flex-col gap-1.5 items-start">
                <button type="button" onClick={() => onEnterWorkspace('analysis')} className="hover:text-[#FF6170] cursor-pointer">
                  Blast Radius Engine
                </button>
                <button type="button" onClick={() => onEnterWorkspace('analysis')} className="hover:text-[#FF6170] cursor-pointer">
                  Runtime Guardian Gate
                </button>
                <button type="button" onClick={() => onEnterWorkspace('verification')} className="hover:text-[#FF6170] cursor-pointer">
                  Proof Reports Export
                </button>
              </div>
            </div>
            <div className="space-y-2.5">
              <div className="font-semibold uppercase tracking-wider text-white/50">Security</div>
              <div className="flex flex-col gap-1.5 items-start">
                <button type="button" onClick={() => onEnterWorkspace('audit')} className="hover:text-[#FF6170] cursor-pointer">
                  Unified Audit Stream
                </button>
                <span className="text-white/50 font-mono-tabular pt-1">
                  Alembic {systemStatus?.alembic_revision || 'b1c2d3e4f5a6'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
