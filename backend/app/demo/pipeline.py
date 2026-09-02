"""Deterministic end-to-end demo contract and attack pipeline."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from typing import Any
from uuid import uuid5

from app.application.ai_investigation.contracts import (
    InvestigationTool,
    InvestigationToolRequest,
    InvestigationToolResult,
    ToolExecutionStatus,
)
from app.application.ai_investigation.engine import AIInvestigationEngine
from app.application.ai_investigation.registry import (
    build_investigation_tool_registry,
)
from app.application.ports.financial_contract_compiler import (
    ContractCompilationResult,
    FinancialContractCompilerPort,
)
from app.application.services.deterministic_contract_compiler import (
    DeterministicFinancialContractCompiler,
)
from app.application.services.financial_contract_compiler import (
    FinancialContractCompilerService,
)
from app.demo.seed import DemoSeed, build_demo_seed
from app.domain.enums.financial import ContractOperator
from app.domain.models.counterexample import Counterexample
from app.domain.models.financial import FinancialContract
from app.domain.models.financial_blast_radius import FinancialBlastRadius
from app.domain.models.payment_simulation import PaymentSimulation
from app.domain.models.verification_comparison import VerificationComparison
from app.domain.models.verification_result import VerificationResult
from app.domain.services.adversarial_scenario_composer import (
    AdversarialScenarioComposer,
)
from app.domain.services.adversarial_scenario_executor import (
    AdversarialExecutionResult,
    AdversarialScenarioExecutor,
)
from app.domain.services.contract_evaluation import ContractEvaluationResult
from app.domain.services.contract_evaluator import ContractEvaluator
from app.domain.services.counterexample_shrinker import CounterexampleShrinker
from app.domain.services.financial_blast_radius import (
    FinancialBlastRadiusAnalyzer,
)
from app.domain.services.payment_simulation_runner import PaymentSimulationRunner
from app.domain.services.verification import VerificationService
from app.domain.services.verification_comparison import (
    VerificationComparisonService,
)
from app.domain.services.verification_snapshot import (
    VerificationSnapshotService,
)
from app.domain.value_objects.financial import (
    ContractField,
    ContractSourceText,
    FinancialConstraint,
)


class DemoFinancialContractCompiler(FinancialContractCompilerPort):
    """Compile the canonical demo rule into a deterministic contract."""

    def __init__(self, seed: DemoSeed) -> None:
        self._seed = seed
        self._base_compiler = DeterministicFinancialContractCompiler()

    def compile(
        self,
        source_text: ContractSourceText,
    ) -> ContractCompilationResult:
        """Compile the demo rule through the production compiler boundary."""
        result = self._base_compiler.compile(source_text)

        if source_text.normalized() != self._seed.business_rule:
            raise ValueError("Unsupported demo business rule.")

        contract = replace(
            result.contract,
            inputs=(
                ContractField(
                    name="refund_amount",
                    data_type="money",
                ),
            ),
            financial_constraints=(
                FinancialConstraint(
                    field="refund_amount",
                    operator=ContractOperator.LESS_THAN_OR_EQUAL,
                    value=self._seed.violation_context[
                        "original_payment_amount"
                    ],
                    currency=self._seed.currency,
                ),
            ),
        )

        return ContractCompilationResult(
            contract=contract,
            source_text=result.source_text,
        )


class DemoPipeline:
    """Execute the deterministic contract and verification stages."""

    def __init__(self, seed: DemoSeed | None = None) -> None:
        self._seed = seed or build_demo_seed()
        self._compiler = FinancialContractCompilerService(
            compiler=DemoFinancialContractCompiler(self._seed),
        )
        self._evaluator = ContractEvaluator()

    @property
    def seed(self) -> DemoSeed:
        """Return the canonical demo seed."""
        return self._seed

    def compile_contract(self) -> FinancialContract:
        """Compile the canonical natural-language demo rule."""
        result = self._compiler.compile(
            ContractSourceText(self._seed.business_rule)
        )

        return replace(
            result.contract,
            id=self._seed.contract_id,
            version=self._seed.contract_version,
            name=self._seed.contract_name,
            required_claim_types=self._seed.required_claim_types,
        )

    def run_baseline(self):
        """Run the canonical baseline payment simulation."""
        return PaymentSimulationRunner.run(
            self._seed.build_simulation()
        )

    def run_attack(self) -> AdversarialExecutionResult:
        """Apply a deterministic duplicate-event attack."""
        from app.domain.models.adversarial_simulation import (
            DuplicateEventAttack,
        )

        simulation = self._seed.build_simulation()

        attack = DuplicateEventAttack(
            simulation_id=simulation.id,
            target_sequence=0,
        )

        scenario = AdversarialScenarioComposer.compose(
            simulation,
            attack,
        )

        return AdversarialScenarioExecutor.execute(
            simulation,
            scenario,
        )

    def evaluate_attack(
        self,
        contract: FinancialContract,
        context: dict[str, Any] | None = None,
    ) -> ContractEvaluationResult:
        """Evaluate the canonical financial violation."""
        return self._evaluator.evaluate(
            contract,
            context if context is not None else self._seed.violation_context,
        )

    def build_verification(
        self,
        contract: FinancialContract,
        context: dict[str, Any] | None = None,
    ) -> tuple[
        VerificationComparison,
        VerificationResult,
        Counterexample,
    ]:
        """Build the production verification result and counterexample."""
        baseline = self.run_baseline()
        attack = self.run_attack()
        evaluation = self.evaluate_attack(contract, context)

        violation_codes = tuple(
            sorted(
                violation.reason_code
                for violation in evaluation.violations
            )
        )

        baseline_snapshot = VerificationSnapshotService.capture_for_contract(
            contract=contract,
            baseline={
                "simulation_id": str(baseline.simulation_id),
                "event_count": len(baseline.trace),
                "passed": True,
            },
            simulation_id=baseline.simulation_id,
            reproducibility_metadata={
                "seed": self._seed.seed,
                "stage": "baseline",
            },
        )

        counterexample_id = uuid5(
            self._seed.simulation_id,
            "counterexample:refund-safety",
        )

        attacked_snapshot = VerificationSnapshotService.capture_for_contract(
            contract=contract,
            baseline={
                "simulation_id": str(attack.simulation_id),
                "event_count": len(attack.adversarial_simulation.events),
                "passed": evaluation.passed,
            },
            violations=violation_codes,
            counterexample_ids=(counterexample_id,),
            simulation_id=attack.simulation_id,
            reproducibility_metadata={
                "seed": self._seed.seed,
                "stage": "attack",
            },
        )

        comparison = VerificationComparisonService.compare(
            baseline_snapshot,
            attacked_snapshot,
        )

        verification = VerificationService.verify(comparison)

        counterexample = Counterexample(
            simulation_id=attack.simulation_id,
            simulation=attack.adversarial_simulation,
            violation_code=(
                violation_codes[0]
                if violation_codes
                else "verification_regression"
            ),
            original_event_count=len(attack.adversarial_simulation.events),
            minimized_event_count=len(attack.adversarial_simulation.events),
        )

        return comparison, verification, counterexample

    @staticmethod
    def _reproduces_simulation_failure(
        simulation: PaymentSimulation,
    ) -> bool:
        """Return whether the payment state machine rejects the simulation."""
        try:
            PaymentSimulationRunner.run(simulation)
        except ValueError:
            return True

        return False

    def calculate_financial_exposure(
        self,
        contract: FinancialContract,
        context: dict[str, Any] | None = None,
    ) -> FinancialBlastRadius:
        """Calculate the demo's financial exposure using the production analyzer."""
        evaluation_context = (
            context if context is not None else self.seed.violation_context
        )
        evaluation = self.evaluate_attack(contract, evaluation_context)

        return FinancialBlastRadiusAnalyzer.analyze(
            contract=contract,
            evaluation=evaluation,
            context=evaluation_context,
        )

    def shrink_counterexample(
        self,
        contract: FinancialContract,
    ) -> Counterexample:
        """Return the minimal deterministic state-machine counterexample."""
        _, verification, counterexample = self.build_verification(contract)

        if verification.passed:
            raise ValueError(
                "Cannot shrink a passing demo verification."
            )

        minimized = CounterexampleShrinker.shrink(
            counterexample.simulation,
            self._reproduces_simulation_failure,
        )

        return Counterexample(
            simulation_id=minimized.id,
            simulation=minimized,
            violation_code=counterexample.violation_code,
            original_event_count=counterexample.original_event_count,
            minimized_event_count=len(minimized.events),
        )

    def investigate(
        self,
        contract: FinancialContract,
    ) -> dict[str, Any]:
        """Investigate the demo failure through bounded production AI tools."""

        investigation_id = uuid5(
            self._seed.simulation_id,
            "investigation:refund-safety",
        )

        registry = build_investigation_tool_registry(
            {
                str(contract.id): contract,
            }
        )

        registry.register(
            InvestigationTool.INSPECT_EXECUTION,
            self._inspect_demo_execution,
        )
        registry.grant(InvestigationTool.INSPECT_EXECUTION)

        engine = AIInvestigationEngine(registry)

        contract_result = engine.investigate(
            InvestigationToolRequest(
                investigation_id=investigation_id,
                tool=InvestigationTool.INSPECT_CONTRACT,
                target_id=contract.id,
            )
        )

        execution_result = engine.investigate(
            InvestigationToolRequest(
                investigation_id=investigation_id,
                tool=InvestigationTool.INSPECT_EXECUTION,
                target_id=self._seed.simulation_id,
            )
        )

        results = (contract_result, execution_result)

        if any(
            result.status is not ToolExecutionStatus.SUCCESS
            for result in results
        ):
            failed = next(
                result for result in results
                if result.status is not ToolExecutionStatus.SUCCESS
            )
            raise RuntimeError(
                "Demo AI investigation failed: "
                f"{failed.explanation or failed.status.value}"
            )

        root_cause = self._derive_root_cause(
            contract_result,
            execution_result,
        )

        return {
            "investigation_id": str(investigation_id),
            "status": ToolExecutionStatus.SUCCESS.value,
            "tools": tuple(result.tool.value for result in results),
            "evidence_ids": tuple(
                str(evidence_id)
                for result in results
                for evidence_id in result.evidence_ids
            ),
            "contract": contract_result.data,
            "execution": execution_result.data,
            "root_cause": root_cause,
        }

    def _inspect_demo_execution(
        self,
        request: InvestigationToolRequest,
    ) -> InvestigationToolResult:
        """Expose only deterministic adversarial execution evidence."""

        execution = self.run_attack().adversarial_simulation

        if request.target_id != self._seed.simulation_id:
            return InvestigationToolResult(
                investigation_id=request.investigation_id,
                tool=InvestigationTool.INSPECT_EXECUTION,
                target_id=request.target_id,
                status=ToolExecutionStatus.NOT_FOUND,
                data={},
                explanation="Payment simulation execution was not found.",
            )

        return InvestigationToolResult(
            investigation_id=request.investigation_id,
            tool=InvestigationTool.INSPECT_EXECUTION,
            target_id=request.target_id,
            status=ToolExecutionStatus.SUCCESS,
            data={
                "id": str(execution.id),
                "seed": execution.seed,
                "events": [
                    {
                        "sequence": event.sequence,
                        "event": event.event.value,
                        "id": str(event.id),
                        "occurred_at": event.occurred_at.isoformat(),
                    }
                    for event in execution.events
                ],
            },
            explanation=(
                "Execution inspection returned deterministic adversarial "
                "demo evidence only."
            ),
        )

    def apply_repair(
        self,
        contract: FinancialContract,
    ) -> dict[str, Any]:
        """Apply the deterministic refund-cap repair at the execution boundary."""
        evaluation = self.evaluate_attack(contract)

        if evaluation.passed:
            return dict(self._seed.violation_context)

        repaired_context = dict(self._seed.violation_context)
        original_amount = repaired_context["original_payment_amount"]

        repaired_context["refund_amount"] = original_amount
        repaired_context["repair"] = "refund_capped_to_original_payment"

        return repaired_context

    def rerun_after_repair(
        self,
        contract: FinancialContract,
        repaired_context: dict[str, Any],
    ) -> tuple[
        VerificationComparison,
        VerificationResult,
        ContractEvaluationResult,
    ]:
        """Re-run production verification against the repaired execution context."""
        comparison, verification, _ = self.build_verification(
            contract,
            repaired_context,
        )
        evaluation = self.evaluate_attack(contract, repaired_context)

        if not evaluation.passed:
            raise RuntimeError(
                "Demo repair did not eliminate the financial violation."
            )

        if not verification.passed:
            raise RuntimeError(
                "Demo repair did not produce a passing verification."
            )

        return comparison, verification, evaluation

    def activate_guardian(self):
        """Activate production Guardian evaluation for the demo refund path."""
        from app.application.financial_guardian.runtime import (
            FinancialGuardianRuntime,
        )
        from app.domain.models.refund_authorization import RefundAuthorization
        from app.domain.models.refund_request import RefundRequest
        from app.domain.services.refund_approval_guard import RefundApprovalGuard
        from app.domain.services.unauthorized_refund_guard import (
            UnauthorizedRefundGuard,
        )

        refund_request = RefundRequest(
            amount_minor=self._seed.amount_minor,
            currency=self._seed.currency,
            approval_granted=False,
        )

        authorization = RefundAuthorization(
            actor_id=self._seed.unauthorized_actor,
            authorized=False,
        )

        evaluations = (
            RefundApprovalGuard(
                approval_threshold_minor=self._seed.amount_minor - 1,
            ).evaluate(refund_request),
            UnauthorizedRefundGuard().evaluate(authorization),
        )

        return FinancialGuardianRuntime().decide(
            evaluations,
            operation="refund",
            actor_id=self._seed.unauthorized_actor,
        )

    def generate_financial_proof(self) -> Any:
        """Generate a production-domain financial proof for the repaired rule."""
        from app.domain.enums.financial import (
            ClaimType,
            VerificationStatus,
        )
        from app.domain.models.financial import (
            FinancialClaim,
            FinancialProof,
        )
        from app.domain.services.proof_evaluator import ProofEvaluator
        from app.domain.value_objects.financial import ConfidenceScore

        proof = FinancialProof(
            subject=self._seed.business_rule,
        )

        claim = FinancialClaim(
            claim_type=ClaimType.TRANSACTION,
            subject=self._seed.business_rule,
            verification_status=VerificationStatus.VERIFIED,
            confidence=ConfidenceScore(Decimal("1.0")),
        )

        evaluation = ProofEvaluator().evaluate([claim])
        proof.claim_ids.append(claim.id)
        proof.apply_evaluation(evaluation)

        return proof

    @staticmethod
    def _derive_root_cause(
        contract_result: InvestigationToolResult,
        execution_result: InvestigationToolResult,
    ) -> str:
        """Derive a bounded root cause only from deterministic evidence."""

        contract_data = contract_result.data
        execution_data = execution_result.data

        contract_name = str(
            contract_data.get("name", "unknown-contract")
        )
        events = execution_data.get("events", [])

        if len(events) >= 2:
            first_event = events[0]
            second_event = events[1]

            if (
                isinstance(first_event, dict)
                and isinstance(second_event, dict)
                and first_event.get("event") == second_event.get("event")
            ):
                return (
                    f"Contract '{contract_name}' was exposed to a duplicate "
                    f"'{first_event.get('event')}' event before the normal "
                    "payment progression completed."
                )

        return (
            f"Contract '{contract_name}' has a deterministic execution "
            "sequence that requires further investigation."
        )


__all__ = [
    "DemoFinancialContractCompiler",
    "DemoPipeline",
]


