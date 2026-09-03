# Financial Proof

Financial Proof is a deterministic financial correctness and verification platform designed to answer a practical question:

> ‎ Can a financial rule be proven safe before a failure becomes a financial loss?‎ 

The system turns financial business rules into executable contracts, runs deterministic payment simulations, deliberately explores adversarial behavior, detects violations, produces reproducible counterexamples, shrinks failures, estimates financial exposure, investigates failures through a constrained AI investigation engine, enforces runtime financial policies through a Guardian layer, and generates auditable financial proof artifacts.

The project is designed as a complete verification pipeline rather than a collection of isolated payment features.

---

## 1. Problem

Financial systems can fail even when individual API operations appear valid.

Examples include:

* duplicate payment events
* invalid state transitions
* excessive refunds
* unauthorized financial actions
* inconsistent business rules
* failures that are difficult to reproduce
* failures whose financial impact is unclear

Traditional application testing generally asks:

> Does the system produce the expected output for a known input?

Financial Proof additionally asks:

> ‎ What happens when the financial system is deliberately attacked?‎ 

The platform therefore combines deterministic verification with adversarial execution, reproducible evidence, financial impact analysis, AI investigation, and runtime enforcement.

---

# 2. Solution

Financial Proof provides an end-to-end financial verification lifecycle:

text
Business Rule
     |
     v
Contract Compilation
     |
     v
Financial Contract
     |
     +--------------------+
     |                    |
     v                    v
Baseline Simulation    Adversarial Simulation
     |                    |
     +----------+---------+
                |
                v
        Contract Evaluation
                |
                v
        Violation Detection
                |
                v
         Counterexample
                |
                v
       Counterexample Shrinking
                |
                v
     Financial Blast-Radius Analysis
                |
                v
        AI Investigation
                |
                v
           Root Cause
                |
                v
             Repair
                |
                v
        Re-run Verification
                |
                v
          Zero Violations
                |
                v
       Runtime Guardian
                |
                v
      Financial Proof


The important property is that the same financial behavior can move through the entire lifecycle:

text
rule
 -> contract
 -> simulation
 -> attack
 -> violation
 -> counterexample
 -> financial impact
 -> investigation
 -> repair
 -> verification
 -> enforcement
 -> proof


---

# 3. Core Capabilities

## 3.1 Financial Contracts

Business rules are represented explicitly as versioned financial contracts instead of remaining hidden inside application logic.

A contract can contain:

* contract identity
* contract name
* contract version
* business rule
* required claim types
* financial constraints
* metadata

Contracts are designed to be explicit, deterministic, independently evaluable, and auditable.

---

## 3.2 Contract Compilation

Business-level financial rules are converted into validated financial contracts.

The canonical demonstration rule is:

> ‎ A customer refund must never exceed the original payment amount.‎ 

The corresponding financial constraint is conceptually:

text
refund_amount <= original_payment_amount


For the demonstration:

text
Original payment = INR 50.00
Refund attempt    = INR 75.00


Therefore:

text
75.00 > 50.00


and the financial constraint fails.

---

## 3.3 Deterministic Simulation

Financial behavior is modeled through deterministic payment simulations.

The simulator models lifecycle events including:

* authorization
* capture
* refund
* retry
* fulfillment

The canonical baseline is:

text
AUTHORIZE -> CAPTURE


The simulation uses an explicit seed and deterministic identifiers.

The canonical demonstration seed is:

text
20260902


Deterministic execution enables:

* replay
* regression testing
* reproducible counterexamples
* stable demonstrations
* benchmark comparisons
* investigation using the same evidence

---

# 4. Adversarial Testing

Financial Proof does not only test valid behavior.

It deliberately attacks the modeled financial system.

The canonical adversarial execution is:

text
AUTHORIZE -> AUTHORIZE -> CAPTURE


The second authorization is intentionally invalid.

This demonstrates an important property of the platform:

> The system can create a concrete financial failure rather than waiting for a production incident to discover one.

---

# 5. Verification

Verification evaluates whether an execution satisfies the financial contract.

Conceptually:

text
Contract
   +
Execution
   |
   v
Evaluation
   |
   +--> PASS
   |
   +--> Violations
   |
   +--> Counterexamples


Verification produces structured evidence rather than only a boolean.

Verification snapshots preserve information including:

* snapshot ID
* creation timestamp
* contract ID
* contract version
* system version
* baseline information
* violations
* counterexample IDs
* simulation ID
* reproducibility metadata

---

## 5.1 Before and After Verification

Financial Proof can compare verification states before and after a repair.

Before repair:

text
violations = 1
verification = FAIL


After repair:

text
violations = 0
verification = PASS


The comparison can identify:

* changed baseline fields
* introduced violations
* resolved violations

This makes repairs traceable and verifiable.

---

# 6. Counterexamples

A counterexample is a concrete execution demonstrating that a financial invariant can fail.

The canonical failure is:

text
AUTHORIZE
AUTHORIZE
CAPTURE


The duplicate authorization becomes a reproducible failure witness.

Because the simulation is deterministic, the failure can be replayed.

This is more useful than a generic assertion failure because developers receive a concrete execution that demonstrates the problem.

---

# 7. Counterexample Shrinking

A failing execution can contain events that are irrelevant to the actual failure.

The shrinking engine attempts to remove unnecessary events while preserving failure reproduction.

Canonical example:

text
Original:

AUTHORIZE
AUTHORIZE
CAPTURE


Shrunk:

text
AUTHORIZE
AUTHORIZE


The `CAPTURE` event is unnecessary for reproducing the duplicate-authorization failure.

Shrinking improves:

* debugging
* investigation
* developer comprehension
* regression testing
* proof readability

A candidate reduction is accepted only when the failure remains reproducible.

---

# 8. Financial Blast Radius

A technical failure is not always enough information for a financial system.

Financial Proof therefore translates violations into monetary exposure.

The financial blast-radius analysis can account for:

* direct loss
* duplicate-charge exposure
* duplicate-fulfillment exposure
* refund exposure
* unauthorized-action exposure
* actual exposure
* maximum exposure

For the canonical demonstration:

text
Original payment: INR 50.00
Refund attempt:   INR 75.00
Exposure:         INR 75.00


This connects technical verification with business impact.

---

# 9. AI Investigation

The AI Investigation Engine provides an evidence-based explanation layer.

It is deliberately constrained rather than being an unrestricted autonomous agent.

The architecture is:

text
Investigation Request
        |
        v
AI Investigation Engine
        |
        v
Tool Registry
        |
        v
Authorized Tool
        |
        v
Bounded Evidence
        |
        v
Investigation Result


Available investigation capabilities include:

text
inspect_contract
inspect_execution
inspect_state
inspect_violation
inspect_financial_impact
replay_scenario
compare_expected_actual


Tools are explicitly registered and authorized.

The investigation boundary controls:

* available tools
* authorization
* argument validation
* target identity
* result identity
* exception handling

Unknown arguments are rejected.

Internal tool failures are not exposed as raw application exceptions.

---

## 9.1 AI Is Not the Source of Truth

The architecture intentionally separates deterministic verification from AI explanation:

text
Deterministic verification establishes the failure.

AI investigation explains the failure.


For the canonical attack:

text
AUTHORIZE -> AUTHORIZE -> CAPTURE


the deterministic verification system establishes the violation.

The AI investigation uses bounded evidence to identify the duplicate authorization as the root cause.

This prevents an AI-generated explanation from becoming the source of financial correctness.

---

# 10. Repair and Re-verification

After investigation identifies the root cause, the system applies a repair.

For the canonical refund scenario:

text
Refund before repair = INR 75.00
Original payment     = INR 50.00


The repair caps the refund:

text
INR 75.00 -> INR 50.00


The system then re-runs verification.

Expected result:

text
violations = 0
verification = PASS


The important property is that the repair is not considered successful merely because it changed the input.

It must cause the verification failure to disappear.

---

# 11. Runtime Financial Guardian

Verification protects against modeled failures before deployment.

The Guardian provides runtime enforcement for sensitive financial actions.

The Guardian evaluates policies including:

* approval requirements
* actor authorization
* financial operation policy

For the demonstration, an unauthorized refund is attempted by:

text
demo-unauthorized-operator


The expected Guardian result is:

text
BLOCK


This creates another security boundary:

text
Financial Operation
        |
        v
Approval Policy
        |
        v
Actor Authorization
        |
        v
Guardian
        |
        v
ALLOW / BLOCK


The Guardian complements verification rather than replacing it.

---

# 12. Financial Proof

After verification and enforcement, the system can generate a financial proof artifact.

A financial proof represents verified financial claims and their evaluation state.

The proof subsystem tracks concepts including:

* financial claims
* evidence
* verification status
* confidence
* proof evaluation

The goal is to preserve financial correctness as auditable evidence rather than treating it as an ephemeral test result.

---

# 13. Security

Financial Proof applies defense-in-depth security.

Security controls include:

* authentication
* authorization
* API input validation
* secret isolation
* webhook signature verification
* replay protection
* idempotency
* AI tool authorization
* financial action authorization
* Guardian enforcement
* sensitive-data handling
* logging redaction
* correlation IDs
* auditability
* structured error handling

The security architecture contains multiple trust boundaries:

text
External Client
      |
Authentication
      |
Authorization
      |
Request Validation
      |
Application
      |
Domain
      |
Financial Gateway


AI has a separate boundary:

text
Investigation Request
      |
Tool Registry
      |
Authorization
      |
Bounded Evidence


Payment-provider webhooks have their own boundary:

text
Payment Provider
      |
Signature Verification
      |
Replay / Idempotency Controls
      |
Validated Event
      |
Application


Detailed threat analysis is available in:

text
docs/security/threat-model.md


---

# 14. API

The backend is implemented with FastAPI.

Local base URL:

text
http://127.0.0.1:8000


## Operational Endpoints

### Health

text
GET /health


The health endpoint is independent of database connectivity.

Expected response:

json
{
  "status": "ok"
}


### Readiness

text
GET /ready


The readiness endpoint checks database connectivity.

Expected response:

json
{
  "status": "ready"
}


## API Areas

The backend exposes operations for:

* financial contracts
* contract decisions
* contract compilation
* financial proofs
* simulations
* verification
* Razorpay webhooks
* deterministic demonstration

## Authentication

Protected API operations use the configured authentication boundary.

Missing or invalid credentials fail closed.

## Authorization

Authentication and authorization are separate controls.

A valid identity does not automatically grant permission for every financial operation.

## Error Handling

Request validation failures are normalized into structured API errors.

Unexpected application failures are returned without exposing internal exception details.

## Correlation IDs

Requests support:

text
X-Correlation-ID


If a client does not supply one, the application generates it.

The correlation ID is returned in responses and supports operational tracing.

## CORS

Development frontend origins are explicitly configured:

text
http://localhost:5173
http://127.0.0.1:5173


Production deployments should configure origins according to the actual trusted frontend domains.

---

# 15. Razorpay Integration

Razorpay is treated as an external payment provider.

The provider boundary is separate from financial correctness verification.

The webhook flow is:

text
Razorpay
   |
Webhook
   |
Signature Verification
   |
Replay / Idempotency Controls
   |
Validated Event
   |
Application


Provider configuration uses environment variables:

text
RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET


Real credentials must never be committed to source control.

Webhook processing accounts for:

* signature authenticity
* replay resistance
* idempotency
* request validation
* controlled errors
* sensitive-data handling

Provider communication does not itself establish financial correctness.

The architecture deliberately separates:

text
Provider communication
+
Financial verification
+
Runtime Guardian enforcement


---

# 16. Deterministic End-to-End Demo

The demo demonstrates the complete Financial Proof lifecycle.

## Canonical Business Rule

text
A customer refund must never exceed the original payment amount.


## Canonical Data

text
Payment amount: INR 50.00
Refund attempt: INR 75.00
Seed:           20260902


## Demo Sequence

text
1.  Enter business rule
2.  Compile contract
3.  Display contract
4.  Attack payment system
5.  Run adversarial execution
6.  Find violation
7.  Display counterexample
8.  Shrink counterexample
9.  Calculate financial exposure
10. AI investigates
11. Display root cause
12. Apply repair
13. Re-run verification
14. Display zero violations
15. Activate Guardian
16. Attempt unauthorized refund
17. Show BLOCKED
18. Generate financial proof


## Expected Failure

Attack:

text
AUTHORIZE -> AUTHORIZE -> CAPTURE


Violation:

text
1 violation


Counterexample:

text
3 events


Shrunk counterexample:

text
2 events


Financial exposure:

text
INR 75.00


Root cause:

text
Duplicate authorization event


## Expected Repair

text
Refund:
INR 75.00 -> INR 50.00


After repair:

text
violations = 0
verification = PASS


## Expected Guardian Result

text
decision = BLOCK


## Demo Properties

The demo is:

* deterministic
* resettable
* replayable
* testable
* reproducible

---

# 17. Local Development Setup

## Requirements

Backend:

* Python 3.11+
* virtual environment
* configured SQLAlchemy database

Frontend:

* Node.js
* npm

## Backend Installation

powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"


## Environment

Copy:

text
.env.example


to:

text
.env


Important configuration includes:

text
APP_NAME
APP_VERSION
APP_ENV
DEBUG
API_HOST
API_PORT
DATABASE_URL
API_AUTH_TOKEN
RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET
PROOF_MINIMUM_REVIEW_CONFIDENCE
PROOF_MINIMUM_READY_CONFIDENCE
PROOF_MINIMUM_SUPPORTED_CLAIM_RATIO


Never commit real secrets.

Production configuration requires:

text
APP_ENV=production
DEBUG=false
API_AUTH_TOKEN=<configured secret>


## Database

Apply migrations:

powershell
python -m alembic upgrade head


Application startup also applies pending migrations before starting the server.

## Backend

Development:

powershell
uvicorn app.main:app --reload


Production-style startup:

powershell
python -m app.startup
uvicorn app.main:app --host 0.0.0.0 --port 8000


## Frontend

powershell
cd frontend
npm ci
npm run dev


Production build:

powershell
npm run build


---

# 18. Docker

The backend Docker image:

* uses Python 3.14
* installs project dependencies
* creates a non-root application user
* runs as that user
* applies database migrations at startup
* exposes port 8000
* provides a healthcheck
* uses unbuffered Python output

The container healthcheck uses:

text
GET /health


This provides an independent liveness signal.

---

# 19. CI

The project includes CI validation for backend and frontend quality.

Backend CI checks:

text
Ruff
Python compilation
pytest
coverage


Frontend CI checks:

text
Oxlint
production build


Backend coverage is enforced with the configured project threshold.

CI also runs against pull requests and pushes to the main branch.

---

# 20. Performance

The project includes benchmarks for:

* simulation throughput
* verification
* regression evaluation
* counterexample shrinking
* memory consumption
* concurrent execution
* API latency
* database operations
* AI investigation

Representative measurements:

| Workload              |    Result |
| --------------------- | --------: |
| 1K-event simulation   |  ~0.438 s |
| 10K-event simulation  |  ~3.024 s |
| 50K-event simulation  | ~22.423 s |
| Clean verification    |  ~0.280 s |
| Regression evaluation |  ~0.190 s |
| 100-event shrinking   |  ~0.007 s |
| 1000-event shrinking  |  ~0.528 s |
| 1K-event memory peak  |  ~1.54 MB |
| 10K-event memory peak | ~15.14 MB |
| 50K-event memory peak | ~75.61 MB |

Simulation throughput was approximately:

text
1K events:  ~6.8K events/s
10K events: ~9.9K events/s
50K events: ~6.7K events/s


Representative concurrency measurements:

text
2 workers:   ~7.5K ops/s
10 workers:  ~9.7K ops/s
50 workers:  ~17.7K ops/s
100 workers: ~24.4K ops/s


Representative local API measurements:

text
GET /health:   ~4.7 ms
GET /ready:    ~3.5 ms
GET contract:  ~7.3 ms
POST contract: ~9.3 ms


Representative SQLite measurements:

text
SELECT:                ~3.8 µs
contract insert+flush: ~9.3 µs


The deterministic local AI implementation measured approximately:

text
inspect_contract: ~0.52 ms


No external provider-token or monetary AI cost was measured because the current implementation does not depend on an external token-billed model provider.

Benchmark results depend on hardware, operating system, Python version, workload shape, database, concurrency, and process configuration.

Detailed results are available in:

text
docs/benchmarks.md


---

# 21. Testing

The project includes multiple testing layers:

text
Unit Tests
    |
Integration Tests
    |
API Tests
    |
Security Tests
    |
Property Tests
    |
Chaos Tests
    |
Regression Tests
    |
Performance Benchmarks
    |
End-to-End Demo Tests


The final M24 API/deployment review and current project validation include:

text
1177 passed


with the existing dependency/deprecation warnings described by the test runner.

Backend quality commands:

powershell
python -m ruff check .
python -m compileall -q app tests
python -m pytest -q


Frontend quality commands:

powershell
npm run lint
npm run build


---

# 22. Reproducibility

Reproducibility is a core architectural requirement.

The demonstration uses:

text
Seed = 20260902


Canonical identifiers are derived deterministically from a fixed namespace.

The same scenario can therefore be:

* reset
* replayed
* simulated
* attacked
* verified
* shrunk
* investigated
* regression-tested

This is particularly important for financial failures because a failure that cannot be reproduced is difficult to investigate, repair, and audit.

---

# 23. Project Architecture

The system is organized around clear boundaries:

text
API
 |
Application Services
 |
Domain Models / Domain Services
 |
Persistence / External Integrations


Cross-cutting capabilities include:

text
Security
Observability
Auditability
Configuration
Error Handling


The design intentionally avoids putting financial correctness exclusively inside route handlers.

The same financial logic can therefore be exercised by:

* APIs
* simulations
* verification
* tests
* demonstrations
* application services

---

# 24. Design Principles

## Explicitness

Financial rules should be represented explicitly.

## Determinism

The same input should produce reproducible modeled behavior.

## Reproducibility

A failure should be replayable.

## Evidence

A verification result should preserve the information needed to understand what happened.

## Explainability

AI should explain deterministic evidence rather than replace it.

## Fail-Closed Security

Missing authorization or invalid credentials should not silently become permission.

## Transaction Ownership

Application-level transactions belong to the unit-of-work boundary.

## Observability

Financial operations should be traceable through structured logs, metrics, and correlation IDs.

## Enforcement

Critical financial policies should have a runtime enforcement boundary.

---

# 25. Limitations

Financial Proof deliberately has boundaries.

## Scenario Coverage

Deterministic simulation verifies modeled scenarios.

It cannot establish that every possible production execution has been explored.

Verification quality depends on:

* contract completeness
* simulation coverage
* adversarial scenario coverage
* financial context quality

## External Providers

External payment providers remain external dependencies.

Provider availability, latency, provider behavior, and infrastructure failures are outside the deterministic simulation boundary.

## Financial Exposure

Blast-radius analysis estimates exposure from supplied financial context.

It is not an accounting ledger or legal damages calculation.

## AI

The AI investigation engine explains evidence.

It does not establish financial correctness.

Deterministic verification remains the source of truth for whether a modeled invariant passed.

## Production Scale

Benchmark results were collected in development/test environments.

They should not be interpreted as production capacity guarantees.

Production deployments require workload-specific load testing and sizing.

## Database

SQLite is suitable for local development and testing.

Production deployments should use an appropriately managed database configuration.

## Authentication

Application-level authentication and authorization are implemented.

Production deployments additionally require operational controls such as:

* TLS
* secure secret management
* identity lifecycle management
* rate limiting where required
* monitoring

## Guardian Policies

The Guardian enforces explicitly modeled policies.

A policy that is not modeled cannot automatically be enforced.

## Demo

The demonstration intentionally uses a controlled scenario:

text
Payment = INR 50.00
Refund  = INR 75.00


It demonstrates the architecture but does not represent every real-world payment pattern.

## Universal Correctness

Financial Proof should not be interpreted as mathematically proving arbitrary financial software universally correct.

Its goal is stronger engineering assurance through:

text
explicit contracts
+
deterministic execution
+
adversarial testing
+
reproducible evidence
+
financial impact analysis
+
runtime enforcement


within the modeled system boundary.

---

# 26. Documentation Map

Detailed technical documentation is organized as follows:

| Document                        | Purpose                       |
| ------------------------------- | ----------------------------- |
| `docs/architecture.md`          | System architecture           |
| `docs/system-flow.md`           | End-to-end execution flow     |
| `docs/contract-system.md`       | Financial contract system     |
| `docs/simulator.md`             | Deterministic simulator       |
| `docs/verification.md`          | Verification and snapshots    |
| `docs/counterexamples.md`       | Counterexamples and shrinking |
| `docs/ai-investigation.md`      | AI investigation engine       |
| `docs/api.md`                   | API surface                   |
| `docs/demo.md`                  | End-to-end demonstration      |
| `docs/setup.md`                 | Setup and deployment          |
| `docs/razorpay.md`              | Razorpay integration          |
| `docs/benchmarks.md`            | Performance results           |
| `docs/limitations.md`           | Limitations                   |
| `docs/security/threat-model.md` | Security threat model         |

---

# 27. Final Design Philosophy

The central principle of Financial Proof is:

> ‎ Financial correctness should be executable, reproducible, observable, explainable, enforceable, and auditable.‎ 

A financial rule should not disappear into application code.

It should become an explicit artifact that can move through the entire lifecycle:

text
DEFINE
  |
COMPILE
  |
SIMULATE
  |
ATTACK
  |
VERIFY
  |
REPRODUCE
  |
SHRINK
  |
MEASURE FINANCIAL IMPACT
  |
INVESTIGATE
  |
REPAIR
  |
RE-VERIFY
  |
ENFORCE
  |
PROVE


Financial Proof is built around that lifecycle.
