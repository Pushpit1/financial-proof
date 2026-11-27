import React, { useEffect, useState } from 'react'
import { Bug, Minimize2, Play, Zap } from 'lucide-react'
import { createSimulation, executeAttack, listSimulations } from '../api/simulations'
import { shrinkCounterexample } from '../api/counterexamples'
import type { AdversarialSimulation, Simulation } from '../types/simulation'
import type { Counterexample } from '../types/counterexample'
import { StatusBadge } from '../components/StatusBadge'

const ATTACK_TYPES = [
  'duplicate',
  'out_of_order',
  'delayed',
  'retry',
  'lost_response',
  'partial_failure',
  'stale_worker_state',
  'worker_crash',
] as const

export function SimulationsSection() {
  const [seed, setSeed] = useState(42)
  const [amountMinor, setAmountMinor] = useState(10000)
  const [currency, setCurrency] = useState('USD')
  const [simulation, setSimulation] = useState<Simulation | null>(null)
  const [recentSimulations, setRecentSimulations] = useState<Simulation[]>([])
  const [attackType, setAttackType] = useState<string>('duplicate')
  const [targetSequence, setTargetSequence] = useState(1)
  const [retryCount, setRetryCount] = useState(1)
  const [adversarial, setAdversarial] = useState<AdversarialSimulation | null>(null)
  const [counterexample, setCounterexample] = useState<Counterexample | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const loadSimulations = async () => {
    try {
      setRecentSimulations(await listSimulations())
    } catch {
      // ignore if database unreachable
    }
  }

  useEffect(() => {
    void loadSimulations()
  }, [])

  const handleRunSimulation = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')
    setAdversarial(null)
    setCounterexample(null)
    try {
      const base = Date.now()
      const events = [
        { event: 'payment_authorized', occurred_at: new Date(base).toISOString() },
        { event: 'payment_captured', occurred_at: new Date(base + 1000).toISOString() },
        { event: 'refund_requested', occurred_at: new Date(base + 2000).toISOString() },
      ]
      const sim = await createSimulation({
        seed,
        amount_minor: amountMinor,
        currency,
        events,
      })
      setSimulation(sim)
      setMessage(`Deterministic simulation ${sim.id.slice(0, 8)} completed.`)
      await loadSimulations()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Simulation failed.')
    } finally {
      setBusy(false)
    }
  }

  const handleRunAttack = async () => {
    if (!simulation) return
    setBusy(true)
    setError('')
    setMessage('')
    setCounterexample(null)
    try {
      const res = await executeAttack(simulation.id, {
        attack_type: attackType,
        target_sequence: targetSequence,
        retry_count: retryCount,
      })
      setAdversarial(res)
      setMessage(`Injected ${attackType} attack against simulation ${simulation.id.slice(0, 8)}.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Adversarial injection failed.')
    } finally {
      setBusy(false)
    }
  }

  const handleShrink = async () => {
    if (!simulation) return
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const res = await shrinkCounterexample(simulation.id, {
        attack_type: attackType,
        target_sequence: targetSequence,
        retry_count: retryCount,
      })
      setCounterexample(res)
      setMessage(
        `Shrunk counterexample from ${res.original_event_count} to ${res.minimized_event_count} events.`,
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Counterexample shrinking failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[#0B1F3A]">
          Simulations & Adversarial Stress Engine
        </h2>
        <p className="text-sm text-slate-600">
          Execute deterministic payment state transitions, inject race/duplicate/crash faults, and
          shrink failing traces to minimal reproducible counterexamples.
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
          onSubmit={handleRunSimulation}
          className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4"
        >
          <div className="flex items-center gap-2 text-[#0B1F3A] font-semibold">
            <Play className="w-4 h-4 text-emerald-600" />
            <span>1. Deterministic Baseline Simulation</span>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Seed</label>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Amount (minor)
              </label>
              <input
                type="number"
                value={amountMinor}
                onChange={(e) => setAmountMinor(Number(e.target.value))}
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
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-lg bg-[#0B1F3A] px-4 py-2 text-sm font-medium text-white hover:bg-[#132f57] disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            {busy ? 'Running...' : 'Run Simulation'}
          </button>

          {simulation && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-mono-tabular font-semibold text-[#0B1F3A]">
                  {simulation.id}
                </span>
                <StatusBadge value={simulation.result.final_payment_state} />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-slate-500">Order State:</span>{' '}
                  <span className="font-mono-tabular font-medium">
                    {simulation.result.final_order_state}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">Snapshots:</span>{' '}
                  <span className="font-mono-tabular font-medium">
                    {simulation.result.snapshots.length}
                  </span>
                </div>
              </div>
              <div className="border-t border-slate-200 pt-2">
                <span className="text-slate-500 block mb-1">
                  Execution Trace ({simulation.result.trace.length} steps)
                </span>
                <ul className="space-y-1 font-mono-tabular">
                  {simulation.result.trace.map((step) => (
                    <li key={step.sequence} className="flex justify-between gap-2">
                      <span>
                        #{step.sequence} {step.event}
                      </span>
                      <span className="text-slate-600">{step.occurred_at}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </form>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-[#0B1F3A] font-semibold">
            <Zap className="w-4 h-4 text-amber-600" />
            <span>2. Adversarial Fault Injection & Shrinking</span>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Attack Type</label>
              <select
                value={attackType}
                onChange={(e) => setAttackType(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-2.5 py-2 text-sm bg-white"
              >
                {ATTACK_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Target Seq</label>
              <input
                type="number"
                min={1}
                value={targetSequence}
                onChange={(e) => setTargetSequence(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Retry Count</label>
              <input
                type="number"
                min={1}
                value={retryCount}
                onChange={(e) => setRetryCount(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono-tabular"
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              disabled={!simulation || busy}
              onClick={() => void handleRunAttack()}
              className="inline-flex items-center gap-2 rounded-lg bg-[#0B1F3A] px-4 py-2 text-sm font-medium text-white hover:bg-[#132f57] disabled:opacity-50"
            >
              <Bug className="w-4 h-4" />
              Inject Attack
            </button>
            <button
              type="button"
              disabled={!simulation || busy}
              onClick={() => void handleShrink()}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:opacity-50"
            >
              <Minimize2 className="w-4 h-4" />
              Shrink Counterexample
            </button>
          </div>

          {adversarial && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-[#0B1F3A]">Adversarial Result</span>
                <StatusBadge value={adversarial.failure ? 'failed' : 'passed'} />
              </div>
              <p className="font-mono-tabular text-slate-700">
                Status: {adversarial.adversarial_status} | Attacks: {adversarial.attack_count} |
                Baseline: {adversarial.baseline.final_payment_state}
                {adversarial.adversarial
                  ? ` -> Adversarial: ${adversarial.adversarial.final_payment_state}`
                  : ''}
              </p>
              {adversarial.failure && (
                <div className="rounded border border-rose-200 bg-rose-50 p-2 text-rose-800 font-mono-tabular">
                  {adversarial.failure.failure_type}: {adversarial.failure.message}
                </div>
              )}
              {adversarial.outcomes.length > 0 && (
                <ul className="space-y-1 font-mono-tabular text-slate-600">
                  {adversarial.outcomes.map((o, idx) => (
                    <li key={idx}>
                      {o.component_type} (seq {o.target_sequence ?? '-'}): {o.status}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {counterexample && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-amber-900">Minimized Counterexample</span>
                <span className="font-mono-tabular font-semibold">
                  {counterexample.original_event_count} -&gt; {counterexample.minimized_event_count}{' '}
                  events
                </span>
              </div>
              <div className="font-mono-tabular text-amber-900">
                Violation: {counterexample.violation_code || 'none'}
              </div>
              <pre className="rounded bg-white/80 p-2 overflow-x-auto font-mono-tabular text-[11px]">
                {JSON.stringify(counterexample.events, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>

      {recentSimulations.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <h3 className="text-sm font-semibold text-[#0B1F3A] mb-3">
            Persisted Simulations ({recentSimulations.length})
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-left text-slate-500">
                  <th className="py-2 pr-3">ID</th>
                  <th className="py-2 pr-3">Seed</th>
                  <th className="py-2 pr-3">Amount</th>
                  <th className="py-2 pr-3">Final Payment</th>
                  <th className="py-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {recentSimulations.slice(0, 10).map((s) => (
                  <tr key={s.id} className="border-b border-slate-100">
                    <td className="py-2 pr-3 font-mono-tabular">{s.id.slice(0, 12)}...</td>
                    <td className="py-2 pr-3 font-mono-tabular">{s.seed}</td>
                    <td className="py-2 pr-3 font-mono-tabular">
                      {s.amount_minor} {s.currency}
                    </td>
                    <td className="py-2 pr-3">
                      <StatusBadge value={s.result.final_payment_state} />
                    </td>
                    <td className="py-2">
                      <button
                        type="button"
                        onClick={() => setSimulation(s)}
                        className="text-[#0B1F3A] font-medium hover:underline"
                      >
                        Load into injector
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
