import { useState } from 'react'
import {
  compileContract,
  createContract,
  getContractVersion,
} from './api/contracts'
import { ApiClientError } from './api/client'
import { createSimulation, executeAttack } from './api/simulations'
import { shrinkCounterexample } from './api/counterexamples'
import { verifySnapshots } from './api/verification'
import { createProof, evaluateProof } from './api/proofs'
import type {
  AdversarialSimulation,
  AttackRequest,
  Simulation,
} from './types/simulation'
import type { FinancialContract } from './types/contract'
import type { Counterexample } from './types/counterexample'
import type {
  VerificationResponse,
  VerificationSnapshotRequest,
} from './types/verification'
import type { FinancialProofAggregate } from './types/proof'
import './App.css'

type Section =
  | 'overview'
  | 'contracts'
  | 'verification'
  | 'violations'
  | 'counterexamples'
  | 'blast-radius'
  | 'investigation'
  | 'comparison'
  | 'guardian'
  | 'certificate'
  | 'audit'

const navigation: Array<{
  group: string
  items: Array<{ id: Section; label: string }>
}> = [
  {
    group: 'Workspace',
    items: [
      { id: 'overview', label: 'Overview' },
      { id: 'contracts', label: 'Contracts' },
    ],
  },
  {
    group: 'Verify',
    items: [
      { id: 'verification', label: 'Run Verification' },
      { id: 'violations', label: 'Violations' },
      { id: 'counterexamples', label: 'Counterexamples' },
    ],
  },
  {
    group: 'Analyze',
    items: [
      { id: 'blast-radius', label: 'Blast Radius' },
      { id: 'investigation', label: 'AI Investigation' },
      { id: 'comparison', label: 'Before / After' },
    ],
  },
  {
    group: 'Evidence',
    items: [
      { id: 'guardian', label: 'Runtime Guardian' },
      { id: 'certificate', label: 'Proof Certificate' },
      { id: 'audit', label: 'Audit Trail' },
    ],
  },
]

function App() {
  const [activeSection, setActiveSection] =
    useState<Section>('overview')

  const [ruleText, setRuleText] = useState(
    'Customer refund must not exceed the original payment amount.',
  )

  const [compiledContract, setCompiledContract] =
    useState<FinancialContract | null>(null)

  const [compiling, setCompiling] = useState(false)
  const [saving, setSaving] = useState(false)
  const [simulationRunning, setSimulationRunning] = useState(false)
  const [attackRunning, setAttackRunning] = useState(false)
  const [verificationRunning, setVerificationRunning] =
    useState(false)

  const [simulation, setSimulation] =
    useState<Simulation | null>(null)

  const [adversarialSimulation, setAdversarialSimulation] =
    useState<AdversarialSimulation | null>(null)

  const [verification, setVerification] =
    useState<VerificationResponse | null>(null)
  const [counterexample, setCounterexample] =
    useState<Counterexample | null>(null)
  const [counterexampleRunning, setCounterexampleRunning] =
    useState(false)
  const [financialProof, setFinancialProof] =
    useState<FinancialProofAggregate | null>(null)
  const [proofRunning, setProofRunning] = useState(false)


  const [attackType, setAttackType] = useState('duplicate')
  const [targetSequence, setTargetSequence] = useState(0)
  const [sourceSequence, setSourceSequence] = useState(1)
  const [retryCount, setRetryCount] = useState(2)
  const [delaySeconds, setDelaySeconds] = useState(1)
  const [workerSequence, setWorkerSequence] = useState(0)
  const [incomingSequence, setIncomingSequence] = useState(1)
  const [scenarioSeed, setScenarioSeed] = useState(42)
  const [scenarioAmountMinor, setScenarioAmountMinor] = useState(10000)
  const [scenarioCurrency, setScenarioCurrency] = useState('INR')
  const [scenarioEvents, setScenarioEvents] = useState('authorize\ncapture')

  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const hasContract = Boolean(compiledContract)
  const hasSimulation = Boolean(simulation)
  const hasAttack = Boolean(adversarialSimulation)
  const hasVerification = Boolean(verification)

  function clearMessages() {
    setError('')
    setSuccess('')
  }

  async function handleCompile() {
    setCompiling(true)
    clearMessages()

    try {
      const response = await compileContract({
        source_text: ruleText.trim(),
      })

      setCompiledContract(response.contract)
      setSuccess('Rule compiled successfully.')
      setActiveSection('contracts')
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Failed to compile the financial rule.',
      )
    } finally {
      setCompiling(false)
    }
  }

  async function handleSaveContract() {
    if (!compiledContract) {
      setError('Compile a rule before saving the contract.')
      return
    }

    setSaving(true)
    clearMessages()

    try {
      try {
        const existing = await getContractVersion(
          compiledContract.name,
          compiledContract.version,
        )

        setCompiledContract(existing)
        setSuccess(
          'Contract already exists. Loaded the existing contract.',
        )
        return
      } catch (caught) {
        if (
          !(caught instanceof ApiClientError) ||
          caught.status !== 404
        ) {
          throw caught
        }
      }

      const saved = await createContract({
        id: compiledContract.id,
        name: compiledContract.name,
        version: compiledContract.version,
        minimum_confidence: Number(
          compiledContract.minimum_confidence,
        ),
        minimum_supported_claim_ratio: Number(
          compiledContract.minimum_supported_claim_ratio,
        ),
        required_claim_types:
          compiledContract.required_claim_types.length > 0
            ? compiledContract.required_claim_types
            : ['transaction'],
      })

      setCompiledContract(saved)
      setSuccess('Contract saved successfully.')
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Failed to save the contract.',
      )
    } finally {
      setSaving(false)
    }
  }

  async function handleRunSimulation() {
    setSimulationRunning(true)
    clearMessages()
    setAdversarialSimulation(null)
    setVerification(null)
    setCounterexample(null)
    setFinancialProof(null)

    try {
      const events = scenarioEvents
        .split(/\r?\n/)
        .map((event) => event.trim())
        .filter(Boolean)

      if (events.length === 0) {
        throw new Error('Add at least one simulation event.')
      }

      if (!scenarioCurrency.trim()) {
        throw new Error('Currency is required.')
      }

      if (scenarioAmountMinor <= 0) {
        throw new Error('Amount must be greater than zero.')
      }

      const result = await createSimulation({
        seed: scenarioSeed,
        amount_minor: scenarioAmountMinor,
        currency: scenarioCurrency.trim().toUpperCase(),
        events: events.map((event, index) => ({
          event,
          occurred_at: new Date(
            Date.now() + index * 1000,
          ).toISOString(),
        })),
      })

      setSimulation(result)
      setSuccess('Baseline simulation completed.')
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Failed to run simulation.',
      )
    } finally {
      setSimulationRunning(false)
    }
  }

  async function handleAttack() {
    if (!simulation) {
      setError('Run a baseline simulation first.')
      return
    }

    if (targetSequence < 0 || targetSequence >= simulation.events.length) {
      setError(
        `Target sequence must be between 0 and ${
          simulation.events.length - 1
        }.`,
      )
      return
    }

    if (
      attackType === 'out_of_order' &&
      (sourceSequence < 0 || sourceSequence >= simulation.events.length)
    ) {
      setError(
        `Source sequence must be between 0 and ${
          simulation.events.length - 1
        }.`,
      )
      return
    }

    if (attackType === 'retry' && retryCount < 1) {
      setError('Retry count must be at least 1.')
      return
    }

    if (attackType === 'delayed' && delaySeconds < 0) {
      setError('Delay seconds cannot be negative.')
      return
    }

    if (
      (attackType === 'worker_crash' ||
        attackType === 'stale_worker') &&
      (workerSequence < 0 ||
        workerSequence >= simulation.events.length)
    ) {
      setError(
        `Worker sequence must be between 0 and ${
          simulation.events.length - 1
        }.`,
      )
      return
    }

    if (
      attackType === 'stale_worker' &&
      (incomingSequence < 0 ||
        incomingSequence >= simulation.events.length)
    ) {
      setError(
        `Incoming sequence must be between 0 and ${
          simulation.events.length - 1
        }.`,
      )
      return
    }

    const request: AttackRequest = {
      attack_type: attackType,
      target_sequence: targetSequence,
    }

    if (attackType === 'out_of_order') {
      request.source_sequence = sourceSequence
    }

    if (attackType === 'retry') {
      request.retry_count = retryCount
    }

    if (attackType === 'delayed') {
      request.delay_seconds = delaySeconds
    }

    if (
      attackType === 'worker_crash' ||
      attackType === 'stale_worker'
    ) {
      request.worker_sequence = workerSequence
    }

    if (attackType === 'stale_worker') {
      request.incoming_sequence = incomingSequence
    }

    setAttackRunning(true)
    setCounterexampleRunning(false)
    setCounterexample(null)
    setFinancialProof(null)
    clearMessages()
    setVerification(null)

    try {
      const result = await executeAttack(simulation.id, request)

      setAdversarialSimulation(result)

      if (result.adversarial_status === 'failed') {
        setCounterexampleRunning(true)

        try {
          const minimized = await shrinkCounterexample(
            simulation.id,
            request,
          )

          setCounterexample(minimized)

          setSuccess(
            `Attack replay failed and the counterexample was automatically minimized from ${
              minimized.original_event_count
            } to ${minimized.minimized_event_count} event(s).`,
          )
        } catch (counterexampleError) {
          setSuccess(
            `Attack applied, but adversarial replay failed: ${
              result.failure?.message ?? 'unknown failure'
            }`,
          )

          setError(
            counterexampleError instanceof Error
              ? `Counterexample generation failed: ${counterexampleError.message}`
              : 'Counterexample generation failed.',
          )
        } finally {
          setCounterexampleRunning(false)
        }

        return
      }

      setSuccess('Adversarial simulation completed.')
    } catch (caught) {
      if (
        caught instanceof ApiClientError &&
        caught.message.includes('Cannot apply')
      ) {
        setCounterexampleRunning(true)

        try {
          const minimized = await shrinkCounterexample(
            simulation.id,
            request,
          )

          setCounterexample(minimized)

          setAdversarialSimulation({
            simulation_id: simulation.id,
            attack_count: 1,
            applied_components: [],
            outcomes: [],
            baseline: simulation.result,
            adversarial: null,
            adversarial_status: 'failed',
            failure: {
              failure_type: 'InvalidPaymentTransition',
              message: caught.message,
            },
          })

          setSuccess(
            `Attack was correctly rejected by the payment state machine. Counterexample automatically minimized from ${
              minimized.original_event_count
            } to ${minimized.minimized_event_count} event(s).`,
          )
        } catch (counterexampleError) {
          setAdversarialSimulation({
            simulation_id: simulation.id,
            attack_count: 1,
            applied_components: [],
            outcomes: [],
            baseline: simulation.result,
            adversarial: null,
            adversarial_status: 'failed',
            failure: {
              failure_type: 'InvalidPaymentTransition',
              message: caught.message,
            },
          })

          setError(
            counterexampleError instanceof Error
              ? `Attack was rejected correctly, but counterexample generation failed: ${counterexampleError.message}`
              : 'Attack was rejected correctly, but counterexample generation failed.',
          )
        } finally {
          setCounterexampleRunning(false)
        }

        return
      }

      setError(
        caught instanceof Error
          ? caught.message
          : 'Failed to execute attack.',
      )
    } finally {
      setAttackRunning(false)
    }
  }

  async function handleShrinkCounterexample() {
    if (!simulation) {
      setError('Run a baseline simulation first.')
      return
    }

    setCounterexampleRunning(true)
    clearMessages()

    try {
      const request: AttackRequest = {
        attack_type: attackType,
        target_sequence: targetSequence,
      }

      if (attackType === 'out_of_order') {
        request.source_sequence = sourceSequence
      }

      if (attackType === 'retry') {
        request.retry_count = retryCount
      }

      if (attackType === 'delayed') {
        request.delay_seconds = delaySeconds
      }

      if (
        attackType === 'worker_crash' ||
        attackType === 'stale_worker'
      ) {
        request.worker_sequence = workerSequence
      }

      if (attackType === 'stale_worker') {
        request.incoming_sequence = incomingSequence
      }

      const result = await shrinkCounterexample(
        simulation.id,
        request,
      )

      setCounterexample(result)
      setSuccess(
        `Counterexample shrunk from ${
          result.original_event_count
        } to ${result.minimized_event_count} event(s).`,
      )
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Failed to shrink counterexample.',
      )
    } finally {
      setCounterexampleRunning(false)
    }
  }

  function buildSimulationEvidence(
    currentSimulation: Simulation,
    stage: 'baseline' | 'adversarial',
  ): Record<string, unknown> {
    return {
      simulation_id: currentSimulation.id,
      seed: currentSimulation.seed,
      amount_minor: currentSimulation.amount_minor,
      currency: currentSimulation.currency,
      event_count: currentSimulation.events.length,
      trace_count: currentSimulation.result.trace.length,
      final_payment_state:
        currentSimulation.result.final_payment_state,
      final_order_state:
        currentSimulation.result.final_order_state,
      trace: currentSimulation.result.trace,
      snapshots: currentSimulation.result.snapshots,
      stage,
    }
  }

  async function handleVerification() {
    if (!simulation || !adversarialSimulation) {
      setError(
        'Run a baseline simulation and an adversarial simulation first.',
      )
      return
    }

    const hasAdversarialResult =
      adversarialSimulation.adversarial_status !== 'failed' &&
      Boolean(adversarialSimulation.adversarial)

    if (!hasAdversarialResult && !counterexample) {
      setError(
        'The adversarial replay failed. A reproducible counterexample is required before verification can continue.',
      )
      return
    }

    setVerificationRunning(true)
    setProofRunning(false)
    clearMessages()

    try {
      const contractVersion =
        compiledContract?.version != null
          ? String(compiledContract.version)
          : 'unknown'

      const contractId =
        compiledContract?.id != null
          ? String(compiledContract.id)
          : undefined

      const systemVersion = '0.1.0'

      const before: VerificationSnapshotRequest = {
        ...(contractId ? { contract_id: contractId } : {}),
        contract_version: contractVersion,
        system_version: systemVersion,
        baseline: buildSimulationEvidence(simulation, 'baseline'),
        violations: [],
        counterexample_ids: [],
        simulation_id: simulation.id,
        reproducibility_metadata: {
          seed: simulation.seed,
          amount_minor: simulation.amount_minor,
          currency: simulation.currency,
          event_count: simulation.events.length,
          stage: 'baseline',
          attack_type: null,
          reproducible: true,
        },
      }

      const after: VerificationSnapshotRequest = hasAdversarialResult
        ? {
            ...(contractId ? { contract_id: contractId } : {}),
            contract_version: contractVersion,
            system_version: systemVersion,
            baseline: {
              simulation_id:
                adversarialSimulation.adversarial!.simulation_id,
              seed: adversarialSimulation.adversarial!.seed,
              amount_minor: simulation.amount_minor,
              currency: simulation.currency,
              event_count: simulation.events.length,
              trace_count:
                adversarialSimulation.adversarial!.trace.length,
              final_payment_state:
                adversarialSimulation.adversarial!.final_payment_state,
              final_order_state:
                adversarialSimulation.adversarial!.final_order_state,
              trace: adversarialSimulation.adversarial!.trace,
              snapshots: adversarialSimulation.adversarial!.snapshots,
              stage: 'adversarial',
            },
            violations: [],
            counterexample_ids: counterexample
              ? [counterexample.simulation_id]
              : [],
            simulation_id:
              adversarialSimulation.adversarial!.simulation_id,
            reproducibility_metadata: {
              seed: adversarialSimulation.adversarial!.seed,
              amount_minor: simulation.amount_minor,
              currency: simulation.currency,
              event_count: simulation.events.length,
              stage: 'adversarial',
              attack_type: attackType,
              target_sequence: targetSequence,
              source_sequence:
                attackType === 'out_of_order'
                  ? sourceSequence
                  : null,
              retry_count:
                attackType === 'retry' ? retryCount : null,
              delay_seconds:
                attackType === 'delayed' ? delaySeconds : null,
              worker_sequence:
                attackType === 'worker_crash' ||
                attackType === 'stale_worker'
                  ? workerSequence
                  : null,
              incoming_sequence:
                attackType === 'stale_worker'
                  ? incomingSequence
                  : null,
              reproducible: Boolean(counterexample),
            },
          }
        : {
            ...(contractId ? { contract_id: contractId } : {}),
            contract_version: contractVersion,
            system_version: systemVersion,
            baseline: {
              simulation_id: simulation.id,
              seed: simulation.seed,
              amount_minor: simulation.amount_minor,
              currency: simulation.currency,
              event_count: counterexample!.minimized_event_count,
              trace_count: 0,
              final_payment_state: 'FAILED',
              final_order_state: 'FAILED',
              trace: [],
              snapshots: counterexample!.events,
              stage: 'adversarial-failure',
              failure: adversarialSimulation.failure,
              counterexample: counterexample!.events,
            },
            violations: [
              adversarialSimulation.failure?.failure_type ??
                'InvalidPaymentTransition',
            ],
            counterexample_ids: [
              counterexample!.simulation_id,
            ],
            simulation_id: simulation.id,
            reproducibility_metadata: {
              seed: simulation.seed,
              amount_minor: simulation.amount_minor,
              currency: simulation.currency,
              event_count: counterexample!.minimized_event_count,
              stage: 'adversarial-failure',
              attack_type: attackType,
              target_sequence: targetSequence,
              source_sequence:
                attackType === 'out_of_order'
                  ? sourceSequence
                  : null,
              retry_count:
                attackType === 'retry' ? retryCount : null,
              delay_seconds:
                attackType === 'delayed' ? delaySeconds : null,
              worker_sequence:
                attackType === 'worker_crash' ||
                attackType === 'stale_worker'
                  ? workerSequence
                  : null,
              incoming_sequence:
                attackType === 'stale_worker'
                  ? incomingSequence
                  : null,
              reproducible: true,
            },
          }

      const result = await verifySnapshots({
        before,
        after,
      })

      setVerification(result)

      setProofRunning(true)

      const claimId = crypto.randomUUID()
      const evidenceId = crypto.randomUUID()
      const evidenceLinkId = crypto.randomUUID()

      const passed = result.result.passed
      const confidence = passed ? 1 : 0

      const proof = await createProof({
        subject: simulation.id,
        claims: [
          {
            id: claimId,
            claim_type: 'transaction',
            subject: simulation.id,
            amount: simulation.amount_minor,
            currency: simulation.currency,
            verification_status: passed
              ? 'verified'
              : 'contradicted',
            confidence,
            confidence_level: passed
              ? 'very_high'
              : 'very_low',
          },
        ],
        evidence: [
          {
            id: evidenceId,
            evidence_type: 'payment_record',
            source_name: 'Financial Proof Workbench V2',
            received_at: new Date().toISOString().slice(0, 10),
            status: passed ? 'verified' : 'rejected',
            source_reference: result.result.verification_id,
          },
        ],
        evidence_links: [
          {
            id: evidenceLinkId,
            claim_id: claimId,
            evidence_id: evidenceId,
            verification_status: passed
              ? 'verified'
              : 'contradicted',
            confidence,
            explanation:
              `Deterministic verification ${result.result.verification_id} ` +
              `compared baseline and adversarial evidence. ` +
              `Regression detected: ${result.result.regression_detected}.`,
          },
        ],
      })

      const evaluatedProof = await evaluateProof(proof.proof.id)

      setFinancialProof(evaluatedProof)

      if (result.result.passed) {
        setSuccess(
          'Verification passed and the Financial Proof was created and evaluated successfully.',
        )
      } else {
        setError(
          `Verification detected a regression${
            result.comparison.introduced_violations.length > 0
              ? `: ${result.comparison.introduced_violations.join(', ')}`
              : '.'
          } Financial Proof evaluation completed.`,
        )
      }
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Failed to verify simulation evidence and create the Financial Proof.',
      )
    } finally {
      setProofRunning(false)
      setVerificationRunning(false)
    }
  }  function goTo(section: Section) {
    clearMessages()
    setActiveSection(section)
  }

  const activeLabel =
    navigation
      .flatMap((group) => group.items)
      .find((item) => item.id === activeSection)?.label ??
    'Overview'

  return (
    <div className="app-shell">
      <header className="topbar">
        <button
          className="brand"
          onClick={() => goTo('overview')}
          aria-label="Go to overview"
        >
          <span className="eyebrow">FINANCIAL PROOF</span>
          <h1>Verification Workbench</h1>
        </button>

        <div className="system-status">
          <span className="status-dot" />
          <span>Backend connected</span>
        </div>
      </header>

      <div className="app-body">
        <aside className="sidebar">
          <div className="sidebar-intro">
            <span>WORKFLOW</span>
            <p>Prove financial invariants with deterministic evidence.</p>
          </div>

          {navigation.map((group) => (
            <nav className="nav-group" key={group.group}>
              <span className="nav-group-title">
                {group.group}
              </span>

              {group.items.map((item) => (
                <button
                  className={`nav-item ${
                    activeSection === item.id ? 'active' : ''
                  }`}
                  key={item.id}
                  onClick={() => goTo(item.id)}
                >
                  <span>{item.label}</span>
                </button>
              ))}
            </nav>
          ))}
        </aside>

        <main className="workspace">
          <div className="workspace-heading">
            <div>
              <span className="eyebrow">{activeSection}</span>
              <h2>{activeLabel}</h2>
            </div>
          </div>

          {error && (
            <div className="feedback error" role="alert">
              <strong>Something went wrong</strong>
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="feedback success" role="status">
              <strong>Completed</strong>
              <span>{success}</span>
            </div>
          )}

          {activeSection === 'overview' && (
            <div className="overview-stack">
              <section className="hero-card">
                <span className="eyebrow">
                  DETERMINISTIC FINANCIAL VERIFICATION
                </span>
                <h3>Turn a financial rule into proof.</h3>
                <p>
                  Define the invariant, compile it into a contract,
                  simulate the system, introduce adversarial behavior,
                  and compare before and after evidence.
                </p>

                <div className="hero-actions">
                  <button
                    className="primary-button"
                    onClick={() => goTo('contracts')}
                  >
                    Define a contract
                  </button>

                  <button
                    className="secondary-button"
                    onClick={() => goTo('verification')}
                  >
                    Run verification
                  </button>
                </div>
              </section>

              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">PROCESS</span>
                    <h3>Five steps to evidence</h3>
                  </div>
                </div>

                <div className="workflow-steps">
                  <button
                    className={`workflow-step ${
                      hasContract ? 'complete' : ''
                    }`}
                    onClick={() => goTo('contracts')}
                  >
                    <span>01</span>
                    <strong>Contract</strong>
                    <small>
                      {hasContract
                        ? 'Compiled'
                        : 'Define the invariant'}
                    </small>
                  </button>

                  <button
                    className={`workflow-step ${
                      hasSimulation ? 'complete' : ''
                    }`}
                    onClick={() => goTo('verification')}
                  >
                    <span>02</span>
                    <strong>Simulation</strong>
                    <small>
                      {hasSimulation
                        ? 'Executed'
                        : 'Establish baseline'}
                    </small>
                  </button>

                  <button
                    className={`workflow-step ${
                      hasAttack ? 'complete' : ''
                    }`}
                    onClick={() => goTo('verification')}
                  >
                    <span>03</span>
                    <strong>Attack</strong>
                    <small>
                      {hasAttack
                        ? 'Executed'
                        : 'Test adversarial behavior'}
                    </small>
                  </button>

                  <button
                    className={`workflow-step ${
                      hasVerification ? 'complete' : ''
                    }`}
                    onClick={() => goTo('verification')}
                  >
                    <span>04</span>
                    <strong>Verify</strong>
                    <small>
                      {hasVerification
                        ? 'Compared'
                        : 'Compare snapshots'}
                    </small>
                  </button>

                  <button
                    className="workflow-step"
                    onClick={() => goTo('certificate')}
                  >
                    <span>05</span>
                    <strong>Evidence</strong>
                    <small>Inspect proof artifacts</small>
                  </button>
                </div>
              </section>

              <div className="metric-grid">
                <div className="metric-card">
                  <span>Contract</span>
                  <strong>
                    {hasContract ? 'Ready' : 'Pending'}
                  </strong>
                </div>

                <div className="metric-card">
                  <span>Baseline</span>
                  <strong>
                    {hasSimulation ? 'Ready' : 'Pending'}
                  </strong>
                </div>

                <div className="metric-card">
                  <span>Adversarial</span>
                  <strong>
                    {hasAttack ? 'Ready' : 'Pending'}
                  </strong>
                </div>

                <div className="metric-card">
                  <span>Proof</span>
                  <strong>
                    {!hasVerification
                      ? 'Pending'
                      : verification?.result
                          .regression_detected
                        ? 'Regression'
                        : 'Passed'}
                  </strong>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'contracts' && (
            <div className="workspace-grid">
              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">
                      STEP 01
                    </span>
                    <h3>Define the invariant</h3>
                  </div>
                </div>

                <p className="panel-description">
                  Describe the financial rule in plain language.
                  The backend compiles it into a deterministic contract.
                </p>

                <label className="field-label" htmlFor="rule">
                  Financial rule
                </label>

                <textarea
                  id="rule"
                  className="rule-input"
                  value={ruleText}
                  onChange={(event) =>
                    setRuleText(event.target.value)
                  }
                  placeholder="Describe the financial invariant..."
                />

                <button
                  className="primary-button"
                  disabled={compiling || !ruleText.trim()}
                  onClick={() => void handleCompile()}
                >
                  {compiling ? 'Compiling…' : 'Compile Rule'}
                </button>
              </section>

              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">
                      CONTRACT
                    </span>
                    <h3>Compiled contract</h3>
                  </div>

                  {compiledContract && (
                    <span className="panel-badge success">
                      Ready
                    </span>
                  )}
                </div>

                {!compiledContract ? (
                  <div className="empty-state">
                    <span className="empty-icon">01</span>
                    <strong>No contract yet</strong>
                    <p>
                      Compile a rule to see the resulting contract.
                    </p>
                  </div>
                ) : (
                  <div className="contract-preview">
                    <div className="detail-row">
                      <span>Name</span>
                      <strong>{compiledContract.name}</strong>
                    </div>

                    <div className="detail-row">
                      <span>Version</span>
                      <strong>
                        v{compiledContract.version}
                      </strong>
                    </div>

                    <div className="detail-row">
                      <span>Contract ID</span>
                      <code>{compiledContract.id}</code>
                    </div>

                    <div className="detail-row">
                      <span>Minimum confidence</span>
                      <strong>
                        {String(
                          compiledContract.minimum_confidence,
                        )}
                      </strong>
                    </div>

                    <div className="detail-row">
                      <span>Supported claim ratio</span>
                      <strong>
                        {String(
                          compiledContract.minimum_supported_claim_ratio,
                        )}
                      </strong>
                    </div>

                    <div className="detail-row">
                      <span>Required claim types</span>
                      <strong>
                        {compiledContract.required_claim_types
                          .length === 0
                          ? 'None returned by compiler'
                          : compiledContract.required_claim_types.join(
                              ', ',
                            )}
                      </strong>
                    </div>

                    <button
                      className="secondary-button"
                      disabled={saving}
                      onClick={() => void handleSaveContract()}
                    >
                      {saving
                        ? 'Saving…'
                        : 'Save Contract'}
                    </button>

                    <button
                      className="link-button"
                      onClick={() => goTo('verification')}
                    >
                      Continue to verification ?
                    </button>
                  </div>
                )}
              </section>
            </div>
          )}

          {activeSection === 'verification' && (
            <div className="verification-stack">
              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">STEP 02</span>
                    <h3>Establish a baseline</h3>
                  </div>
                  <span
                    className={`panel-badge ${
                      simulation ? 'success' : ''
                    }`}
                  >
                    {simulation ? 'EXECUTED' : 'WAITING'}
                  </span>
                </div>

                <p className="panel-description">
                  Configure real deterministic payment data. Nothing is
                  fabricated for verification.
                </p>

                <div className="form-grid">
                  <div>
                    <label className="field-label" htmlFor="scenario-seed">
                      Seed
                    </label>
                    <input
                      id="scenario-seed"
                      className="text-input"
                      min={0}
                      type="number"
                      value={scenarioSeed}
                      onChange={(event) =>
                        setScenarioSeed(Number(event.target.value))
                      }
                    />
                  </div>

                  <div>
                    <label className="field-label" htmlFor="scenario-amount">
                      Amount (minor units)
                    </label>
                    <input
                      id="scenario-amount"
                      className="text-input"
                      min={1}
                      type="number"
                      value={scenarioAmountMinor}
                      onChange={(event) =>
                        setScenarioAmountMinor(
                          Number(event.target.value),
                        )
                      }
                    />
                  </div>

                  <div>
                    <label
                      className="field-label"
                      htmlFor="scenario-currency"
                    >
                      Currency
                    </label>
                    <input
                      id="scenario-currency"
                      className="text-input"
                      maxLength={3}
                      value={scenarioCurrency}
                      onChange={(event) =>
                        setScenarioCurrency(event.target.value)
                      }
                    />
                  </div>

                  <div>
                    <label
                      className="field-label"
                      htmlFor="scenario-events"
                    >
                      Event sequence
                    </label>
                    <textarea
                      id="scenario-events"
                      className="json-input"
                      rows={5}
                      value={scenarioEvents}
                      onChange={(event) =>
                        setScenarioEvents(event.target.value)
                      }
                      placeholder={"authorize\ncapture"}
                    />
                    <p className="hint">
                      One event per line. The order is preserved.
                    </p>
                  </div>
                </div>

                <button
                  className="primary-button"
                  disabled={simulationRunning}
                  onClick={() => void handleRunSimulation()}
                >
                  {simulationRunning
                    ? 'Running simulation…'
                    : 'Run Baseline Simulation'}
                </button>

                {simulation && (
                  <div className="contract-preview compact">
                    <div className="detail-row">
                      <span>Simulation</span>
                      <code>{simulation.id}</code>
                    </div>
                    <div className="detail-row">
                      <span>Result</span>
                      <strong>
                        {simulation.result.final_payment_state}
                      </strong>
                    </div>
                    <div className="detail-row">
                      <span>Events</span>
                      <strong>{simulation.events.length}</strong>
                    </div>
                  </div>
                )}
              </section>

              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">STEP 03</span>
                    <h3>Attack the payment system</h3>
                  </div>
                  <span
                    className={`panel-badge ${
                      adversarialSimulation ? 'success' : ''
                    }`}
                  >
                    {adversarialSimulation ? 'EXECUTED' : 'WAITING'}
                  </span>
                </div>

                <p className="panel-description">
                  Every configured attack is sent to the real adversarial
                  simulation API.
                </p>

                <div className="form-grid">
                  <div>
                    <label className="field-label" htmlFor="attack-type">
                      Attack type
                    </label>
                    <select
                      id="attack-type"
                      className="select-input"
                      value={attackType}
                      onChange={(event) =>
                        setAttackType(event.target.value)
                      }
                    >
                      <option value="duplicate">Duplicate event</option>
                      <option value="out_of_order">
                        Out-of-order event
                      </option>
                      <option value="partial_failure">
                        Partial failure
                      </option>
                      <option value="lost_response">
                        Lost response
                      </option>
                      <option value="worker_crash">
                        Worker crash
                      </option>
                      <option value="delayed">Delayed event</option>
                      <option value="retry">Retry</option>
                      <option value="stale_worker">
                        Stale worker
                      </option>
                    </select>
                  </div>

                  <div>
                    <label
                      className="field-label"
                      htmlFor="target-sequence"
                    >
                      Target sequence
                    </label>
                    <input
                      id="target-sequence"
                      className="text-input"
                      min={0}
                      type="number"
                      value={targetSequence}
                      onFocus={(event) => event.currentTarget.select()}
                      onChange={(event) =>
                        setTargetSequence(
                          Number(event.target.value),
                        )
                      }
                    />
                  </div>

                  {attackType === 'out_of_order' && (
                    <div>
                      <label
                        className="field-label"
                        htmlFor="source-sequence"
                      >
                        Source sequence
                      </label>
                      <input
                        id="source-sequence"
                        className="text-input"
                        min={0}
                        type="number"
                        value={sourceSequence}
                        onFocus={(event) => event.currentTarget.select()}
                        onChange={(event) =>
                          setSourceSequence(
                            Number(event.target.value),
                          )
                        }
                      />
                    </div>
                  )}

                  {attackType === 'retry' && (
                    <div>
                      <label
                        className="field-label"
                        htmlFor="retry-count"
                      >
                        Retry count
                      </label>
                      <input
                        id="retry-count"
                        className="text-input"
                        min={1}
                        type="number"
                        value={retryCount}
                        onFocus={(event) => event.currentTarget.select()}
                        onChange={(event) =>
                          setRetryCount(Number(event.target.value))
                        }
                      />
                    </div>
                  )}

                  {attackType === 'delayed' && (
                    <div>
                      <label
                        className="field-label"
                        htmlFor="delay-seconds"
                      >
                        Delay seconds
                      </label>
                      <input
                        id="delay-seconds"
                        className="text-input"
                        min={0}
                        step="0.1"
                        type="number"
                        value={delaySeconds}
                        onFocus={(event) => event.currentTarget.select()}
                        onChange={(event) =>
                          setDelaySeconds(
                            Number(event.target.value),
                          )
                        }
                      />
                    </div>
                  )}

                  {(attackType === 'worker_crash' ||
                    attackType === 'stale_worker') && (
                    <div>
                      <label
                        className="field-label"
                        htmlFor="worker-sequence"
                      >
                        Worker sequence
                      </label>
                      <input
                        id="worker-sequence"
                        className="text-input"
                        min={0}
                        type="number"
                        value={workerSequence}
                        onFocus={(event) => event.currentTarget.select()}
                        onChange={(event) =>
                          setWorkerSequence(
                            Number(event.target.value),
                          )
                        }
                      />
                    </div>
                  )}

                  {attackType === 'stale_worker' && (
                    <div>
                      <label
                        className="field-label"
                        htmlFor="incoming-sequence"
                      >
                        Incoming sequence
                      </label>
                      <input
                        id="incoming-sequence"
                        className="text-input"
                        min={0}
                        type="number"
                        value={incomingSequence}
                        onFocus={(event) => event.currentTarget.select()}
                        onChange={(event) =>
                          setIncomingSequence(
                            Number(event.target.value),
                          )
                        }
                      />
                    </div>
                  )}
                </div>

                <button
                  className="primary-button"
                  disabled={attackRunning || !simulation}
                  onClick={() => void handleAttack()}
                >
                  {attackRunning
                    ? 'Executing attack…'
                    : 'Execute Attack'}
                </button>

                {!simulation && (
                  <p className="hint">
                    Run the baseline simulation before executing an attack.
                  </p>
                )}

                {adversarialSimulation && (
                  <div className="attack-result">
                    <div className="detail-row">
                      <span>Attack count</span>
                      <strong>
                        {adversarialSimulation.attack_count}
                      </strong>
                    </div>

                    <div className="detail-row">
                      <span>Status</span>
                      <strong>
                        {adversarialSimulation.adversarial_status}
                      </strong>
                    </div>

                    {adversarialSimulation.failure && (
                      <div className="error-banner">
                        <strong>
                          {adversarialSimulation.failure.failure_type}
                        </strong>
                        <span>
                          {adversarialSimulation.failure.message}
                        </span>
                      </div>
                    )}

                    {adversarialSimulation.outcomes.map(
                      (outcome, index) => (
                        <div
                          className="outcome-row"
                          key={`${outcome.component_type}-${index}`}
                        >
                          <span>{outcome.component_type}</span>
                          <strong>{outcome.status}</strong>
                        </div>
                      ),
                    )}
                  </div>
                )}
              </section>

              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">STEP 04</span>
                    <h3>Verify real evidence</h3>
                  </div>
                  <span
                    className={`panel-badge ${
                      verification
                        ? verification.result.passed
                          ? 'success'
                          : 'error'
                        : ''
                    }`}
                  >
                    {verification
                      ? verification.result.passed
                        ? 'PASS'
                        : 'REGRESSION'
                      : 'WAITING'}
                  </span>
                </div>

                <p className="panel-description">
                  Before/after evidence is generated directly from the
                  executed simulation and attack. No manual JSON or IDs.
                </p>

                <div className="verification-grid">
                  <div className="snapshot-card">
                    <div className="snapshot-heading">
                      <span className="panel-kicker">BEFORE</span>
                      <strong>Baseline evidence</strong>
                    </div>

                    {!simulation ? (
                      <p className="muted">
                        Run a baseline simulation first.
                      </p>
                    ) : (
                      <div className="outcome-list">
                        <div className="outcome-row">
                          <span>Simulation ID</span>
                          <code>{simulation.id}</code>
                        </div>
                        <div className="outcome-row">
                          <span>Seed</span>
                          <strong>{simulation.seed}</strong>
                        </div>
                        <div className="outcome-row">
                          <span>Payment</span>
                          <strong>
                            {simulation.result.final_payment_state}
                          </strong>
                        </div>
                        <div className="outcome-row">
                          <span>Order</span>
                          <strong>
                            {simulation.result.final_order_state}
                          </strong>
                        </div>
                        <div className="outcome-row">
                          <span>Trace entries</span>
                          <strong>
                            {simulation.result.trace.length}
                          </strong>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="snapshot-card">
                    <div className="snapshot-heading">
                      <span className="panel-kicker">AFTER</span>
                      <strong>Adversarial evidence</strong>
                    </div>

                    {!adversarialSimulation ? (
                      <p className="muted">
                        Execute an attack first.
                      </p>
                    ) : adversarialSimulation.adversarial_status ===
                      'failed' ? (
                      <div className="error-banner">
                        <strong>Replay failed</strong>
                        <span>
                          {adversarialSimulation.failure?.message ??
                            'Adversarial result unavailable.'}
                        </span>
                      </div>
                    ) : adversarialSimulation.adversarial ? (
                      <div className="outcome-list">
                        <div className="outcome-row">
                          <span>Simulation ID</span>
                          <code>
                            {adversarialSimulation.simulation_id}
                          </code>
                        </div>
                        <div className="outcome-row">
                          <span>Payment</span>
                          <strong>
                            {
                              adversarialSimulation.adversarial
                                .final_payment_state
                            }
                          </strong>
                        </div>
                        <div className="outcome-row">
                          <span>Order</span>
                          <strong>
                            {
                              adversarialSimulation.adversarial
                                .final_order_state
                            }
                          </strong>
                        </div>
                        <div className="outcome-row">
                          <span>Trace entries</span>
                          <strong>
                            {
                              adversarialSimulation.adversarial
                                .trace.length
                            }
                          </strong>
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>

                <button
                  className="primary-button"
                  disabled={
                    verificationRunning || proofRunning ||
                    !simulation ||
                    !adversarialSimulation ||
                    (adversarialSimulation.adversarial_status ===
                      'failed' &&
                      !counterexample)
                  }
                  onClick={() => void handleVerification()}
                >
                  {verificationRunning
                    ? 'Comparing evidence?'
                    : 'Run Verification'}
                </button>

                {verification && (
                  <div className="verification-result">
                    <div className="detail-row">
                      <span>Verification</span>
                      <strong>
                        {verification.result.passed
                          ? 'PASSED'
                          : 'FAILED'}
                      </strong>
                    </div>

                    <div className="detail-row">
                      <span>Regression</span>
                      <strong>
                        {verification.result.regression_detected
                          ? 'Detected'
                          : 'None'}
                      </strong>
                    </div>

                    <div className="detail-row">
                      <span>Reproducible</span>
                      <strong>
                        {verification.result.reproducible
                          ? 'Yes'
                          : 'No'}
                      </strong>
                    </div>

                    {verification.result.violations.length > 0 && (
                      <div className="outcome-list">
                        {verification.result.violations.map(
                          (violation) => (
                            <div
                              className="outcome-row"
                              key={violation}
                            >
                              <span>Introduced violation</span>
                              <code>{violation}</code>
                            </div>
                          ),
                        )}
                      </div>
                    )}
                  </div>
                )}
              </section>
            </div>
          )}

          {activeSection === 'violations' && (
            <div className="evidence-page">
              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">VERIFICATION EVIDENCE</span>
                    <h3>Violations</h3>
                  </div>
                  <span
                    className={`panel-badge ${
                      verification?.result.regression_detected
                        ? 'error'
                        : 'success'
                    }`}
                  >
                    {verification
                      ? verification.result.regression_detected
                        ? `${verification.result.violations.length} detected`
                        : 'None detected'
                      : 'Awaiting verification'}
                  </span>
                </div>

                <p className="panel-description">
                  Violations are derived directly from the deterministic
                  before/after verification result.
                </p>

                {!verification ? (
                  <div className="empty-state">
                    <span className="empty-icon">01</span>
                    <strong>No verification evidence yet</strong>
                    <p>
                      Run verification first. Introduced violations will
                      appear here automatically.
                    </p>
                    <button
                      className="secondary-button"
                      onClick={() => goTo('verification')}
                    >
                      Run verification ?
                    </button>
                  </div>
                ) : verification.result.violations.length === 0 ? (
                  <div className="evidence-success">
                    <strong>System remained within the verified boundary.</strong>
                    <span>
                      No violations were introduced by the comparison.
                    </span>
                  </div>
                ) : (
                  <div className="outcome-list">
                    {verification.result.violations.map((violation) => (
                      <div className="outcome-row" key={violation}>
                        <span>Violation</span>
                        <code>{violation}</code>
                        <strong>INTRODUCED</strong>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>
          )}

          {activeSection === 'counterexamples' && (
            <div className="evidence-page">
              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">
                      MINIMAL FAILING EVIDENCE
                    </span>
                    <h3>Counterexample Shrinker</h3>
                  </div>
                  <span
                    className={`panel-badge ${
                      counterexample ? 'success' : ''
                    }`}
                  >
                    {counterexample ? 'MINIMIZED' : 'READY'}
                  </span>
                </div>

                <p className="panel-description">
                  The backend removes the largest possible suffix while
                  deterministically preserving the replay failure.
                </p>

                {!simulation ? (
                  <div className="empty-state">
                    <span className="empty-icon">CE</span>
                    <strong>No simulation yet</strong>
                    <p>
                      Run a baseline simulation and configure an attack
                      first.
                    </p>
                    <button
                      className="secondary-button"
                      onClick={() => goTo('verification')}
                    >
                      Open Workbench
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      className="primary-button"
                      disabled={
                        counterexampleRunning ||
                        !simulation
                      }
                      onClick={() =>
                        void handleShrinkCounterexample()
                      }
                    >
                      {counterexampleRunning
                        ? 'Shrinking?'
                        : 'Shrink Counterexample'}
                    </button>

                    {counterexample && (
                      <div className="counterexample-timeline">
                        <div className="metric-grid">
                          <div className="metric-card">
                            <span>Violation</span>
                            <strong>
                              {counterexample.violation_code}
                            </strong>
                          </div>
                          <div className="metric-card">
                            <span>Original</span>
                            <strong>
                              {counterexample.original_event_count}
                            </strong>
                          </div>
                          <div className="metric-card">
                            <span>Minimal</span>
                            <strong>
                              {counterexample.minimized_event_count}
                            </strong>
                          </div>
                        </div>

                        <div className="outcome-list">
                          {counterexample.events.map((event) => (
                            <div
                              className="outcome-row"
                              key={event.id}
                            >
                              <span>
                                {event.sequence}: {event.event}
                              </span>
                              <code>{event.id}</code>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </section>
            </div>
          )}

          {activeSection === 'blast-radius' && (
            <div className="evidence-page">
              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">FINANCIAL IMPACT</span>
                    <h3>Blast Radius</h3>
                  </div>
                  <span className="panel-badge">Evidence only</span>
                </div>

                <p className="panel-description">
                  Financial blast-radius analysis is deterministic and
                  contract-aware. This console will only display calculated
                  exposure when the backend exposes its analysis result.
                </p>

                <div className="capability-card">
                  <span className="capability-icon">?</span>
                  <div>
                    <strong>Analyzer available in the domain</strong>
                    <p>
                      Exposure can include direct loss, duplicate-charge,
                      duplicate-fulfillment, refund, and unauthorized-action
                      exposure. No synthetic amount is displayed here.
                    </p>
                  </div>
                  <span className="panel-badge">API pending</span>
                </div>
              </section>

              {verification && (
                <section className="panel">
                  <div className="panel-header">
                    <div>
                      <span className="panel-kicker">CURRENT SIGNAL</span>
                      <h3>Verification impact signal</h3>
                    </div>
                  </div>

                  <div className="metric-grid">
                    <div className="metric-card">
                      <span>Introduced violations</span>
                      <strong>
                        {verification.comparison.introduced_violations.length}
                      </strong>
                    </div>
                    <div className="metric-card">
                      <span>Resolved violations</span>
                      <strong>
                        {verification.comparison.resolved_violations.length}
                      </strong>
                    </div>
                    <div className="metric-card">
                      <span>Counterexamples added</span>
                      <strong>
                        {verification.comparison.added_counterexample_ids.length}
                      </strong>
                    </div>
                    <div className="metric-card">
                      <span>Regression</span>
                      <strong>
                        {verification.result.regression_detected
                          ? 'Detected'
                          : 'Clear'}
                      </strong>
                    </div>
                  </div>
                </section>
              )}
            </div>
          )}

          {activeSection === 'investigation' && (
            <div className="evidence-page">
              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">DETERMINISTIC AI</span>
                    <h3>AI Investigation</h3>
                  </div>
                  <span className="panel-badge">Grounded</span>
                </div>

                <p className="panel-description">
                  Financial Proof uses bounded investigation tools rather than
                  an unrestricted autonomous agent.
                </p>

                <div className="investigation-tools">
                  <div className="capability-card">
                    <span className="capability-icon">01</span>
                    <div>
                      <strong>Inspect contract</strong>
                      <p>
                        Inspect persisted contract definition data without
                        inventing execution facts.
                      </p>
                    </div>
                    <span className="panel-badge success">Available</span>
                  </div>

                  <div className="capability-card">
                    <span className="capability-icon">02</span>
                    <div>
                      <strong>Inspect execution</strong>
                      <p>
                        Deterministic execution inspection exists in the
                        investigation architecture.
                      </p>
                    </div>
                    <span className="panel-badge">API pending</span>
                  </div>

                  <div className="capability-card">
                    <span className="capability-icon">03</span>
                    <div>
                      <strong>Root cause / repair recommendation</strong>
                      <p>
                        No fabricated recommendation is shown until an
                        evidence-backed investigation endpoint is exposed.
                      </p>
                    </div>
                    <span className="panel-badge">API pending</span>
                  </div>
                </div>
              </section>
            </div>
          )}

          {activeSection === 'comparison' && (
            <div className="evidence-page">
              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">BEFORE / AFTER</span>
                    <h3>Verification Comparison</h3>
                  </div>

                  {verification && (
                    <span
                      className={`panel-badge ${
                        verification.result.regression_detected
                          ? 'error'
                          : 'success'
                      }`}
                    >
                      {verification.result.regression_detected
                        ? 'Regression'
                        : 'Passed'}
                    </span>
                  )}
                </div>

                {!verification ? (
                  <div className="empty-state">
                    <span className="empty-icon">?</span>
                    <strong>No comparison yet</strong>
                    <p>
                      Execute the verification workflow to generate immutable
                      before/after evidence.
                    </p>
                    <button
                      className="secondary-button"
                      onClick={() => goTo('verification')}
                    >
                      Open verification ?
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="metric-grid">
                      <div className="metric-card">
                        <span>Contract changed</span>
                        <strong>
                          {verification.comparison.contract_version_changed
                            ? 'Yes'
                            : 'No'}
                        </strong>
                      </div>
                      <div className="metric-card">
                        <span>System changed</span>
                        <strong>
                          {verification.comparison.system_version_changed
                            ? 'Yes'
                            : 'No'}
                        </strong>
                      </div>
                      <div className="metric-card">
                        <span>Changes</span>
                        <strong>
                          {verification.comparison.changes.length}
                        </strong>
                      </div>
                      <div className="metric-card">
                        <span>Reproducible</span>
                        <strong>
                          {verification.result.reproducible ? 'Yes' : 'No'}
                        </strong>
                      </div>
                    </div>

                    <div className="outcome-list">
                      {verification.comparison.changes.length === 0 ? (
                        <div className="empty-inline">
                          No field-level changes detected.
                        </div>
                      ) : (
                        verification.comparison.changes.map((change, index) => (
                          <div
                            className="outcome-row"
                            key={`${change.field}-${index}`}
                          >
                            <span>{change.change_type}</span>
                            <strong>{change.field}</strong>
                            <code>
                              {JSON.stringify(change.before)} ?{' '}
                              {JSON.stringify(change.after)}
                            </code>
                          </div>
                        ))
                      )}
                    </div>
                  </>
                )}
              </section>
            </div>
          )}

          {activeSection === 'guardian' && (
            <div className="evidence-page">
              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">RUNTIME SAFETY</span>
                    <h3>Runtime Guardian</h3>
                  </div>
                  <span className="panel-badge success">Backend ready</span>
                </div>

                <p className="panel-description">
                  The runtime Guardian is a decision boundary for financial
                  actions. This dashboard does not fabricate a runtime
                  decision without an actual Guardian evaluation.
                </p>

                <div className="guardian-grid">
                  <div className="capability-card">
                    <span className="capability-icon">ALLOW</span>
                    <div>
                      <strong>Allow</strong>
                      <p>Authorized financial operations can proceed.</p>
                    </div>
                  </div>

                  <div className="capability-card">
                    <span className="capability-icon">BLOCK</span>
                    <div>
                      <strong>Block</strong>
                      <p>Unsafe or unauthorized financial operations can be prevented.</p>
                    </div>
                  </div>

                  <div className="capability-card">
                    <span className="capability-icon">REVIEW</span>
                    <div>
                      <strong>Review</strong>
                      <p>Operations requiring additional evidence can be held.</p>
                    </div>
                  </div>
                </div>

                <div className="empty-inline">
                  Guardian evaluation and audit endpoints are not currently
                  exposed by the frontend API surface.
                </div>
              </section>
            </div>
          )}

          {activeSection === 'certificate' && (
            <div className="evidence-page">
              <section className="panel certificate-panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">PROOF ARTIFACT</span>
                    <h3>Proof Certificate</h3>
                  </div>

                  <span
                    className={`panel-badge ${
                      verification?.result.passed
                        ? 'success'
                        : verification
                          ? 'error'
                          : ''
                    }`}
                  >
                    {verification
                      ? verification.result.passed
                        ? 'PASS'
                        : 'FAIL'
                      : 'Pending'}
                  </span>
                </div>

                {!verification ? (
                  <div className="empty-state">
                    <span className="empty-icon">?</span>
                    <strong>No certificate yet</strong>
                    <p>
                      A certificate should be grounded in an executed
                      verification result.
                    </p>
                    <button
                      className="secondary-button"
                      onClick={() => goTo('verification')}
                    >
                      Generate verification evidence ?
                    </button>
                  </div>
                ) : (
                  <>
                    {financialProof && (
                      <div className="contract-preview compact">
                        <div className="detail-row">
                          <span>Financial Proof</span>
                          <strong>{financialProof.proof.status}</strong>
                        </div>
                        <div className="detail-row">
                          <span>Proof ID</span>
                          <code>{financialProof.proof.id}</code>
                        </div>
                        <div className="detail-row">
                          <span>Subject</span>
                          <code>{financialProof.proof.subject}</code>
                        </div>
                        <div className="detail-row">
                          <span>Overall confidence</span>
                          <strong>
                            {financialProof.proof.overall_confidence}
                          </strong>
                        </div>
                      </div>
                    )}
                    <div className="certificate-seal">
                      <span>{verification.result.passed ? '?' : '!'}</span>
                      <strong>
                        {verification.result.passed
                          ? 'Verification Passed'
                          : 'Verification Failed'}
                      </strong>
                      <small>
                        Deterministic before/after comparison
                      </small>
                    </div>

                    <div className="contract-preview compact">
                      <div className="detail-row">
                        <span>Verification ID</span>
                        <code>{verification.result.verification_id}</code>
                      </div>
                      <div className="detail-row">
                        <span>Comparison ID</span>
                        <code>{verification.result.comparison_id}</code>
                      </div>
                      <div className="detail-row">
                        <span>Before snapshot</span>
                        <code>{verification.before.snapshot_id}</code>
                      </div>
                      <div className="detail-row">
                        <span>After snapshot</span>
                        <code>{verification.after.snapshot_id}</code>
                      </div>
                      <div className="detail-row">
                        <span>Reproducible</span>
                        <strong>
                          {verification.result.reproducible ? 'Yes' : 'No'}
                        </strong>
                      </div>
                    </div>
                  </>
                )}
              </section>
            </div>
          )}

          {activeSection === 'audit' && (
            <div className="evidence-page">
              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">TRACEABILITY</span>
                    <h3>Audit Trail</h3>
                  </div>
                  <span className="panel-badge">Immutable IDs</span>
                </div>

                <p className="panel-description">
                  Evidence identities provide a traceable chain from the
                  verification operation to its snapshots and comparison.
                </p>

                {!verification ? (
                  <div className="empty-state">
                    <span className="empty-icon">ID</span>
                    <strong>No audit evidence yet</strong>
                    <p>
                      Run verification to create the evidence identifiers
                      shown here.
                    </p>
                  </div>
                ) : (
                  <div className="audit-list">
                    <div className="audit-row">
                      <span>Verification</span>
                      <code>{verification.result.verification_id}</code>
                    </div>
                    <div className="audit-row">
                      <span>Comparison</span>
                      <code>{verification.result.comparison_id}</code>
                    </div>
                    <div className="audit-row">
                      <span>Before snapshot</span>
                      <code>{verification.before.snapshot_id}</code>
                    </div>
                    <div className="audit-row">
                      <span>After snapshot</span>
                      <code>{verification.after.snapshot_id}</code>
                    </div>
                    <div className="audit-row">
                      <span>Simulation</span>
                      <code>
                        {verification.after.simulation_id ??
                          verification.before.simulation_id ??
                          'Not linked'}
                      </code>
                    </div>
                  </div>
                )}

                <div className="empty-inline">
                  Detailed persisted audit-event retrieval is not currently
                  exposed by the frontend API.
                </div>
              </section>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
