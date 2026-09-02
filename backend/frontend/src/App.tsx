import { useState } from 'react'
import {
  compileContract,
  createContract,
  getContractVersion,
} from './api/contracts'
import { ApiClientError } from './api/client'
import { createSimulation, executeAttack } from './api/simulations'
import { verifySnapshots } from './api/verification'
import type {
  AdversarialSimulation,
  Simulation,
} from './types/simulation'
import type { FinancialContract } from './types/contract'
import type {
  VerificationResponse,
  VerificationSnapshotRequest,
} from './types/verification'
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

const defaultBeforeBaseline = JSON.stringify(
  {
    final_payment_state: 'authorized',
    final_order_state: 'pending',
    trace_entries: 2,
  },
  null,
  2,
)

const defaultAfterBaseline = JSON.stringify(
  {
    final_payment_state: 'authorized',
    final_order_state: 'pending',
    trace_entries: 2,
  },
  null,
  2,
)

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

  const [attackType, setAttackType] = useState('duplicate')
  const [targetSequence, setTargetSequence] = useState(0)

  const [beforeContractVersion, setBeforeContractVersion] =
    useState('1')
  const [beforeSystemVersion, setBeforeSystemVersion] =
    useState('1.0.0')
  const [beforeBaseline, setBeforeBaseline] =
    useState(defaultBeforeBaseline)
  const [beforeViolations, setBeforeViolations] = useState('')
  const [beforeCounterexamples, setBeforeCounterexamples] =
    useState('')

  const [afterContractVersion, setAfterContractVersion] =
    useState('2')
  const [afterSystemVersion, setAfterSystemVersion] =
    useState('1.1.0')
  const [afterBaseline, setAfterBaseline] =
    useState(defaultAfterBaseline)
  const [afterViolations, setAfterViolations] = useState('')
  const [afterCounterexamples, setAfterCounterexamples] =
    useState('')

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

    try {
      const result = await createSimulation({
        seed: 42,
        amount_minor: 10000,
        currency: 'INR',
        events: [
          {
            event: 'authorize',
            occurred_at: new Date().toISOString(),
          },
          {
            event: 'capture',
            occurred_at: new Date(
              Date.now() + 1000,
            ).toISOString(),
          },
        ],
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

    setAttackRunning(true)
    clearMessages()
    setVerification(null)

    try {
      const result = await executeAttack(simulation.id, {
        attack_type: attackType,
        target_sequence: targetSequence,
      })

      setAdversarialSimulation(result)
      setSuccess('Adversarial simulation completed.')
    } catch (caught) {
      if (
        caught instanceof ApiClientError &&
        caught.message.includes('Cannot apply')
      ) {
        setAdversarialSimulation(null)
        setAfterBaseline(defaultBeforeBaseline)
        setAfterViolations('')
        setSuccess(
          'Attack was correctly rejected by the payment state machine.',
        )
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

  function parseJsonObject(
    value: string,
    label: string,
  ): Record<string, unknown> {
    let parsed: unknown

    try {
      parsed = JSON.parse(value)
    } catch {
      throw new Error(`${label} contains invalid JSON.`)
    }

    if (
      typeof parsed !== 'object' ||
      parsed === null ||
      Array.isArray(parsed)
    ) {
      throw new Error(`${label} must contain a JSON object.`)
    }

    return parsed as Record<string, unknown>
  }

  function parseList(value: string): string[] {
    return value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
  }

  async function handleVerification() {
    setVerificationRunning(true)
    clearMessages()

    try {
      const before: VerificationSnapshotRequest = {
        contract_id: compiledContract?.id,
        contract_version: beforeContractVersion.trim(),
        system_version: beforeSystemVersion.trim(),
        baseline: parseJsonObject(
          beforeBaseline,
          'Before baseline',
        ),
        violations: parseList(beforeViolations),
        counterexample_ids: parseList(beforeCounterexamples),
        simulation_id: simulation?.id,
        reproducibility_metadata: {
          source: 'frontend-workbench',
          deterministic_seed: simulation?.seed ?? 42,
        },
      }

      const after: VerificationSnapshotRequest = {
        contract_id: compiledContract?.id,
        contract_version: afterContractVersion.trim(),
        system_version: afterSystemVersion.trim(),
        baseline: parseJsonObject(
          afterBaseline,
          'After baseline',
        ),
        violations: parseList(afterViolations),
        counterexample_ids: parseList(afterCounterexamples),
        simulation_id:
          adversarialSimulation?.simulation_id ??
          simulation?.id,
        reproducibility_metadata: {
          source: 'frontend-workbench',
          deterministic_seed: simulation?.seed ?? 42,
        },
      }

      const result = await verifySnapshots({
        before,
        after,
      })

      setVerification(result)

      if (result.result.regression_detected) {
        setSuccess('Verification complete: regression detected.')
      } else {
        setSuccess('Verification complete: no regression detected.')
      }
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Failed to execute verification.',
      )
    } finally {
      setVerificationRunning(false)
    }
  }

  function goTo(section: Section) {
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
                    <span className="panel-kicker">
                      STEP 02
                    </span>
                    <h3>Establish a baseline</h3>
                  </div>

                  {simulation && (
                    <span className="panel-badge success">
                      Executed
                    </span>
                  )}
                </div>

                <p className="panel-description">
                  Run the same deterministic payment flow before
                  testing adversarial behavior.
                </p>

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
                      <span>Seed</span>
                      <strong>{simulation.seed}</strong>
                    </div>

                    <div className="detail-row">
                      <span>Amount</span>
                      <strong>
                        {simulation.amount_minor}{' '}
                        {simulation.currency}
                      </strong>
                    </div>

                    <div className="detail-row">
                      <span>Payment state</span>
                      <strong>
                        {simulation.result.final_payment_state}
                      </strong>
                    </div>

                    <div className="detail-row">
                      <span>Order state</span>
                      <strong>
                        {simulation.result.final_order_state}
                      </strong>
                    </div>
                  </div>
                )}
              </section>

              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">
                      STEP 03
                    </span>
                    <h3>Introduce an attack</h3>
                  </div>

                  {adversarialSimulation && (
                    <span className="panel-badge success">
                      Executed
                    </span>
                  )}
                </div>

                <p className="panel-description">
                  Test how the payment flow behaves when an adversarial
                  event is introduced.
                </p>

                <div className="form-grid">
                  <div>
                    <label
                      className="field-label"
                      htmlFor="attack-type"
                    >
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
                      <option value="duplicate">
                        Duplicate event
                      </option>
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
                      <option value="delayed">
                        Delayed event
                      </option>
                      <option value="retry">
                        Retry
                      </option>
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
                      onChange={(event) =>
                        setTargetSequence(
                          Number(event.target.value),
                        )
                      }
                    />
                  </div>
                </div>

                <button
                  className="primary-button"
                  disabled={
                    attackRunning ||
                    !simulation ||
                    attackType !== 'duplicate'
                  }
                  onClick={() => void handleAttack()}
                >
                  {attackRunning
                    ? 'Executing attack…'
                    : 'Execute Attack'}
                </button>

                {attackType !== 'duplicate' && (
                  <p className="hint">
                    Duplicate events are enabled in this first
                    workbench path. Other attacks require additional
                    parameters.
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
                      <span>Applied component</span>
                      <strong>
                        {adversarialSimulation.applied_components.join(
                          ', ',
                        )}
                      </strong>
                    </div>

                    <div className="outcome-list">
                      {adversarialSimulation.outcomes.map(
                        (outcome, index) => (
                          <div
                            className="outcome-row"
                            key={`${outcome.component_type}-${index}`}
                          >
                            <span>
                              {outcome.component_type}
                            </span>
                            <span>
                              sequence {outcome.target_sequence}
                            </span>
                            <strong>{outcome.status}</strong>
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                )}
              </section>

              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">
                      STEP 04
                    </span>
                    <h3>Compare before and after</h3>
                  </div>

                  {verification && (
                    <span
                      className={`panel-badge ${
                        verification.result
                          .regression_detected
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

                <p className="panel-description">
                  Compare immutable snapshots to determine whether a
                  regression was introduced.
                </p>

                <div className="verification-grid">
                  <div className="snapshot-card">
                    <div className="snapshot-heading">
                      <span className="panel-kicker">
                        BEFORE
                      </span>
                      <strong>Known-good state</strong>
                    </div>

                    <label
                      className="field-label"
                      htmlFor="before-contract-version"
                    >
                      Contract version
                    </label>
                    <input
                      id="before-contract-version"
                      className="text-input"
                      value={beforeContractVersion}
                      onChange={(event) =>
                        setBeforeContractVersion(
                          event.target.value,
                        )
                      }
                    />

                    <label
                      className="field-label"
                      htmlFor="before-system-version"
                    >
                      System version
                    </label>
                    <input
                      id="before-system-version"
                      className="text-input"
                      value={beforeSystemVersion}
                      onChange={(event) =>
                        setBeforeSystemVersion(
                          event.target.value,
                        )
                      }
                    />

                    <label
                      className="field-label"
                      htmlFor="before-baseline"
                    >
                      Baseline JSON
                    </label>
                    <textarea
                      id="before-baseline"
                      className="json-input"
                      value={beforeBaseline}
                      onChange={(event) =>
                        setBeforeBaseline(event.target.value)
                      }
                    />

                    <label
                      className="field-label"
                      htmlFor="before-violations"
                    >
                      Violations
                    </label>
                    <input
                      id="before-violations"
                      className="text-input"
                      value={beforeViolations}
                      onChange={(event) =>
                        setBeforeViolations(event.target.value)
                      }
                      placeholder="code_a, code_b"
                    />

                    <label
                      className="field-label"
                      htmlFor="before-counterexamples"
                    >
                      Counterexample IDs
                    </label>
                    <input
                      id="before-counterexamples"
                      className="text-input"
                      value={beforeCounterexamples}
                      onChange={(event) =>
                        setBeforeCounterexamples(
                          event.target.value,
                        )
                      }
                      placeholder="UUID, UUID"
                    />
                  </div>

                  <div className="snapshot-card">
                    <div className="snapshot-heading">
                      <span className="panel-kicker">
                        AFTER
                      </span>
                      <strong>Candidate state</strong>
                    </div>

                    <label
                      className="field-label"
                      htmlFor="after-contract-version"
                    >
                      Contract version
                    </label>
                    <input
                      id="after-contract-version"
                      className="text-input"
                      value={afterContractVersion}
                      onChange={(event) =>
                        setAfterContractVersion(
                          event.target.value,
                        )
                      }
                    />

                    <label
                      className="field-label"
                      htmlFor="after-system-version"
                    >
                      System version
                    </label>
                    <input
                      id="after-system-version"
                      className="text-input"
                      value={afterSystemVersion}
                      onChange={(event) =>
                        setAfterSystemVersion(
                          event.target.value,
                        )
                      }
                    />

                    <label
                      className="field-label"
                      htmlFor="after-baseline"
                    >
                      Baseline JSON
                    </label>
                    <textarea
                      id="after-baseline"
                      className="json-input"
                      value={afterBaseline}
                      onChange={(event) =>
                        setAfterBaseline(event.target.value)
                      }
                    />

                    <label
                      className="field-label"
                      htmlFor="after-violations"
                    >
                      Violations
                    </label>
                    <input
                      id="after-violations"
                      className="text-input"
                      value={afterViolations}
                      onChange={(event) =>
                        setAfterViolations(event.target.value)
                      }
                      placeholder="code_a, code_b"
                    />

                    <label
                      className="field-label"
                      htmlFor="after-counterexamples"
                    >
                      Counterexample IDs
                    </label>
                    <input
                      id="after-counterexamples"
                      className="text-input"
                      value={afterCounterexamples}
                      onChange={(event) =>
                        setAfterCounterexamples(
                          event.target.value,
                        )
                      }
                      placeholder="UUID, UUID"
                    />
                  </div>
                </div>

                <button
                  className="primary-button"
                  disabled={verificationRunning}
                  onClick={() => void handleVerification()}
                >
                  {verificationRunning
                    ? 'Comparing snapshots…'
                    : 'Run Verification'}
                </button>
              </section>

              {verification && (
                <section
                  className={`verification-result ${
                    verification.result.regression_detected
                      ? 'regression'
                      : 'passed'
                  }`}
                >
                  <div className="result-header">
                    <div>
                      <span className="panel-kicker">
                        VERIFICATION RESULT
                      </span>
                      <h3>
                        {verification.result
                          .regression_detected
                          ? 'Regression detected'
                          : 'No regression detected'}
                      </h3>
                    </div>

                    <span className="result-status">
                      {verification.result.passed
                        ? 'PASS'
                        : 'FAIL'}
                    </span>
                  </div>

                  <div className="result-summary">
                    <div>
                      <span>Reproducible</span>
                      <strong>
                        {verification.result.reproducible
                          ? 'Yes'
                          : 'No'}
                      </strong>
                    </div>

                    <div>
                      <span>Contract changed</span>
                      <strong>
                        {verification.comparison
                          .contract_version_changed
                          ? 'Yes'
                          : 'No'}
                      </strong>
                    </div>

                    <div>
                      <span>System changed</span>
                      <strong>
                        {verification.comparison
                          .system_version_changed
                          ? 'Yes'
                          : 'No'}
                      </strong>
                    </div>

                    <div>
                      <span>Changes</span>
                      <strong>
                        {verification.comparison.changes.length}
                      </strong>
                    </div>
                  </div>

                  <div className="verification-results-grid">
                    <div className="evidence-card">
                      <span className="panel-kicker">
                        VIOLATIONS
                      </span>

                      <h4>Introduced</h4>

                      {verification.comparison
                        .introduced_violations.length === 0 ? (
                        <p className="muted">
                          None introduced.
                        </p>
                      ) : (
                        <ul className="evidence-list">
                          {verification.comparison.introduced_violations.map(
                            (item) => (
                              <li key={`introduced-${item}`}>
                                <code>{item}</code>
                              </li>
                            ),
                          )}
                        </ul>
                      )}

                      <h4>Resolved</h4>

                      {verification.comparison
                        .resolved_violations.length === 0 ? (
                        <p className="muted">
                          None resolved.
                        </p>
                      ) : (
                        <ul className="evidence-list">
                          {verification.comparison.resolved_violations.map(
                            (item) => (
                              <li key={`resolved-${item}`}>
                                <code>{item}</code>
                              </li>
                            ),
                          )}
                        </ul>
                      )}
                    </div>

                    <div className="evidence-card">
                      <span className="panel-kicker">
                        BASELINE CHANGES
                      </span>

                      {verification.comparison.changes.length ===
                      0 ? (
                        <p className="muted">
                          No baseline changes.
                        </p>
                      ) : (
                        <div className="outcome-list">
                          {verification.comparison.changes.map(
                            (change, index) => (
                              <div
                                className="outcome-row"
                                key={`${change.field}-${index}`}
                              >
                                <span>{change.field}</span>
                                <code>
                                  {JSON.stringify(change.before)}
                                  {' ? '}
                                  {JSON.stringify(change.after)}
                                </code>
                              </div>
                            ),
                          )}
                        </div>
                      )}
                    </div>

                    <div className="evidence-card">
                      <span className="panel-kicker">
                        COUNTEREXAMPLES
                      </span>

                      <div className="detail-row">
                        <span>Added</span>
                        <strong>
                          {
                            verification.comparison
                              .added_counterexample_ids.length
                          }
                        </strong>
                      </div>

                      <div className="detail-row">
                        <span>Removed</span>
                        <strong>
                          {
                            verification.comparison
                              .removed_counterexample_ids.length
                          }
                        </strong>
                      </div>
                    </div>
                  </div>

                  <div className="contract-preview compact">
                    <div className="detail-row">
                      <span>Verification ID</span>
                      <code>
                        {verification.result.verification_id}
                      </code>
                    </div>

                    <div className="detail-row">
                      <span>Comparison ID</span>
                      <code>
                        {verification.result.comparison_id}
                      </code>
                    </div>

                    <div className="detail-row">
                      <span>Before snapshot</span>
                      <code>
                        {verification.before.snapshot_id}
                      </code>
                    </div>

                    <div className="detail-row">
                      <span>After snapshot</span>
                      <code>
                        {verification.after.snapshot_id}
                      </code>
                    </div>
                  </div>
                </section>
              )}
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
                    <span className="panel-kicker">MINIMAL FAILING EVIDENCE</span>
                    <h3>Counterexamples</h3>
                  </div>
                  <span className="panel-badge">
                    {verification
                      ? verification.comparison.added_counterexample_ids.length
                      : 0}
                  </span>
                </div>

                <p className="panel-description">
                  Counterexample identities are preserved by verification.
                  Detailed shrinking artifacts will appear here when exposed
                  by the backend API.
                </p>

                {!verification ||
                verification.comparison.added_counterexample_ids.length ===
                  0 ? (
                  <div className="empty-state">
                    <span className="empty-icon">CE</span>
                    <strong>No new counterexamples</strong>
                    <p>
                      The current verification result contains no newly added
                      counterexample IDs.
                    </p>
                  </div>
                ) : (
                  <div className="outcome-list">
                    {verification.comparison.added_counterexample_ids.map(
                      (id) => (
                        <div className="outcome-row" key={id}>
                          <span>Added counterexample</span>
                          <code>{id}</code>
                          <strong>NEW</strong>
                        </div>
                      ),
                    )}
                  </div>
                )}
              </section>

              <section className="panel">
                <div className="panel-header">
                  <div>
                    <span className="panel-kicker">SHRINKING</span>
                    <h3>Minimal failing sequence</h3>
                  </div>
                </div>
                <div className="capability-card">
                  <span className="capability-icon">?</span>
                  <div>
                    <strong>Backend capability exists</strong>
                    <p>
                      Counterexample shrinking is part of the verification
                      engine, but no dedicated HTTP endpoint is currently
                      exposed to this workbench.
                    </p>
                  </div>
                  <span className="panel-badge">API pending</span>
                </div>
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



