"""Tests for the financial contract compiler service."""

import pytest

from app.application.ports.financial_contract_compiler import (
    ContractCompilationResult,
)
from app.application.services.financial_contract_compiler import (
    FinancialContractCompilerService,
)
from app.domain.models.financial import ContractField, FinancialContract
from app.domain.value_objects.financial import ContractSourceText


class FakeCompiler:
    """Deterministic compiler used for application-service tests."""

    def __init__(self) -> None:
        self.received_source: ContractSourceText | None = None
        self.result: ContractCompilationResult | None = None

    def compile(
        self,
        source_text: ContractSourceText,
    ) -> ContractCompilationResult:
        self.received_source = source_text

        if self.result is None:
            self.result = ContractCompilationResult(
                contract=FinancialContract(
                    name="Compiled Contract",
                ),
                source_text=source_text,
            )

        return self.result


def test_service_delegates_compilation_to_port() -> None:
    compiler = FakeCompiler()
    source = ContractSourceText(
        "Customer may request a refund within 30 days."
    )

    service = FinancialContractCompilerService(
        compiler=compiler,  # type: ignore[arg-type]
    )

    result = service.compile(source)

    assert compiler.received_source == source
    assert result.source_text == source
    assert result.contract.name == "Compiled Contract"


def test_service_returns_validated_compiler_result() -> None:
    compiler = FakeCompiler()
    source = ContractSourceText("A valid contract.")

    expected = ContractCompilationResult(
        contract=FinancialContract(
            name="Expected Contract",
        ),
        source_text=source,
    )
    compiler.result = expected

    service = FinancialContractCompilerService(
        compiler=compiler,  # type: ignore[arg-type]
    )

    result = service.compile(source)

    assert result is expected


def test_service_rejects_invalid_compiler_result_type() -> None:
    class InvalidCompiler:
        def compile(
            self,
            source_text: ContractSourceText,
        ) -> str:
            return "invalid"

    service = FinancialContractCompilerService(
        compiler=InvalidCompiler(),  # type: ignore[arg-type]
    )

    source = ContractSourceText("A valid contract.")

    with pytest.raises(
        TypeError,
        match="Compiler must return ContractCompilationResult",
    ):
        service.compile(source)


def test_service_rejects_contract_failing_validation() -> None:
    class RejectingValidator:
        def validate(self, contract):
            class Result:
                valid = False
                errors = (
                    "Simulated compiler validation failure.",
                )

            return Result()

    compiler = FakeCompiler()

    service = FinancialContractCompilerService(
        compiler=compiler,  # type: ignore[arg-type]
        validator=RejectingValidator(),  # type: ignore[arg-type]
    )

    with pytest.raises(
        ValueError,
        match="Simulated compiler validation failure",
    ):
        service.compile(
            ContractSourceText("Invalid contract.")
        )

def test_compiler_pipeline_produces_valid_domain_contract() -> None:
    from app.application.services.deterministic_contract_compiler import (
        DeterministicFinancialContractCompiler,
    )
    from app.domain.services.contract_validator import ContractValidator

    compiler = DeterministicFinancialContractCompiler()
    service = FinancialContractCompilerService(
        compiler=compiler,
        validator=ContractValidator(),
    )

    source = ContractSourceText(
        "Refund Policy"
    )

    result = service.compile(source)

    validation = ContractValidator().validate(
        result.contract
    )

    assert validation.valid is True
    assert validation.errors == ()
    assert result.contract.name == "Refund Policy"
    assert result.source_text == source

def test_service_compile_and_persist_requires_unit_of_work() -> None:
    compiler = FakeCompiler()

    service = FinancialContractCompilerService(
        compiler=compiler,  # type: ignore[arg-type]
    )

    with pytest.raises(
        ValueError,
        match="Compiler unit of work is required",
    ):
        service.compile_and_persist(
            ContractSourceText("Persisted Contract")
        )


def test_service_compile_and_persist_uses_contract_repository() -> None:
    compiler = FakeCompiler()

    class ContractRepository:
        def __init__(self) -> None:
            self.items = []

        def add(self, contract):
            self.items.append(contract)
            return contract

    class UnitOfWork:
        def __init__(self) -> None:
            self.contracts = ContractRepository()
            self.entered = False
            self.committed = False
            self.rolled_back = False

        def __enter__(self):
            self.entered = True
            return self

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            if exc_type is None:
                self.committed = True
            else:
                self.rolled_back = True

    unit_of_work = UnitOfWork()

    service = FinancialContractCompilerService(
        compiler=compiler,  # type: ignore[arg-type]
        unit_of_work=unit_of_work,  # type: ignore[arg-type]
    )

    source = ContractSourceText("Persisted Contract")

    result = service.compile_and_persist(source)

    assert result.contract.name == "Compiled Contract"
    assert result.source_text == source
    assert len(unit_of_work.contracts.items) == 1
    assert unit_of_work.contracts.items[0] == result.contract
    assert unit_of_work.entered is True
    assert unit_of_work.committed is True
    assert unit_of_work.rolled_back is False


def test_service_compile_and_persist_rolls_back_on_repository_failure() -> None:
    compiler = FakeCompiler()

    class FailingRepository:
        def add(self, contract):
            raise RuntimeError("Simulated contract persistence failure.")

    class UnitOfWork:
        def __init__(self) -> None:
            self.contracts = FailingRepository()
            self.committed = False
            self.rolled_back = False

        def __enter__(self):
            return self

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            if exc_type is None:
                self.committed = True
            else:
                self.rolled_back = True

    unit_of_work = UnitOfWork()

    service = FinancialContractCompilerService(
        compiler=compiler,  # type: ignore[arg-type]
        unit_of_work=unit_of_work,  # type: ignore[arg-type]
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated contract persistence failure",
    ):
        service.compile_and_persist(
            ContractSourceText("Failing Contract")
        )

    assert unit_of_work.committed is False
    assert unit_of_work.rolled_back is True
def test_service_compile_and_persist_writes_contract_to_database() -> None:
    from app.application.services.deterministic_contract_compiler import (
        DeterministicFinancialContractCompiler,
    )
    from app.db.models.financial import FinancialContractModel
    from app.db.unit_of_work import FinancialUnitOfWork
    from tests.conftest import create_session

    session = create_session()

    service = FinancialContractCompilerService(
        compiler=DeterministicFinancialContractCompiler(),
        unit_of_work=FinancialUnitOfWork(session),
    )

    source = ContractSourceText(
        "Refund Policy"
    )

    result = service.compile_and_persist(source)

    stored = session.get(
        FinancialContractModel,
        result.contract.id,
    )

    assert stored is not None
    assert stored.id == result.contract.id
    assert stored.name == "Refund Policy"
    assert stored.version == result.contract.version
def test_compile_and_persist_rolls_back_when_repository_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.application.services.deterministic_contract_compiler import (
        DeterministicFinancialContractCompiler,
    )
    from app.db.models.financial import FinancialContractModel
    from app.db.unit_of_work import FinancialUnitOfWork
    from tests.conftest import create_session

    session = create_session()
    unit_of_work = FinancialUnitOfWork(session)

    service = FinancialContractCompilerService(
        compiler=DeterministicFinancialContractCompiler(),
        unit_of_work=unit_of_work,
    )

    original_add = unit_of_work.contracts.add

    def failing_add(contract):
        original_add(contract)
        raise RuntimeError(
            "Simulated contract persistence failure."
        )

    monkeypatch.setattr(
        unit_of_work.contracts,
        "add",
        failing_add,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated contract persistence failure",
    ):
        service.compile_and_persist(
            ContractSourceText("Rollback Contract")
        )

    session.expire_all()

    stored_contracts = session.query(
        FinancialContractModel
    ).all()

    assert stored_contracts == []

def test_service_rejects_compiler_returning_wrong_result_type() -> None:
    class InvalidCompiler:
        def compile(self, source_text):
            return object()

    service = FinancialContractCompilerService(
        compiler=InvalidCompiler(),  # type: ignore[arg-type]
    )

    with pytest.raises(
        TypeError,
        match="Compiler must return ContractCompilationResult",
    ):
        service.compile(
            ContractSourceText("Invalid compiler output.")
        )


def test_service_rejects_validator_errors() -> None:
    compiler = FakeCompiler()

    class RejectingValidator:
        def validate(self, contract):
            class Result:
                valid = False
                errors = (
                    "Contract contains an invalid rule.",
                    "Contract contains an invalid authorization.",
                )

            return Result()

    service = FinancialContractCompilerService(
        compiler=compiler,  # type: ignore[arg-type]
        validator=RejectingValidator(),  # type: ignore[arg-type]
    )

    with pytest.raises(
        ValueError,
        match="Contract contains an invalid rule",
    ):
        service.compile(
            ContractSourceText("Invalid contract.")
        )


def test_service_does_not_persist_when_validation_fails() -> None:
    compiler = FakeCompiler()

    class RejectingValidator:
        def validate(self, contract):
            class Result:
                valid = False
                errors = ("Validation failed.",)

            return Result()

    class Repository:
        def add(self, contract):
            raise AssertionError(
                "Repository must not be called for invalid contracts."
            )

    class UnitOfWork:
        def __init__(self):
            self.contracts = Repository()

        def __enter__(self):
            raise AssertionError(
                "Unit of work must not be entered for invalid contracts."
            )

        def __exit__(self, exc_type, exc_value, traceback):
            pass

    service = FinancialContractCompilerService(
        compiler=compiler,  # type: ignore[arg-type]
        validator=RejectingValidator(),  # type: ignore[arg-type]
        unit_of_work=UnitOfWork(),  # type: ignore[arg-type]
    )

    with pytest.raises(
        ValueError,
        match="Validation failed",
    ):
        service.compile_and_persist(
            ContractSourceText("Rejected contract.")
        )

def test_service_rejects_invalid_compiled_contract_with_real_validator() -> None:
    class InvalidCompiler:
        def compile(
            self,
            source_text: ContractSourceText,
        ) -> ContractCompilationResult:
            contract = FinancialContract(
                name="Invalid Contract",
                inputs=(
                    ContractField(
                        name="customer_id",
                        data_type="string",
                    ),
                ),
                outputs=(
                    ContractField(
                        name="customer_id",
                        data_type="string",
                    ),
                ),
            )

            return ContractCompilationResult(
                contract=contract,
                source_text=source_text,
            )

    service = FinancialContractCompilerService(
        compiler=InvalidCompiler(),  # type: ignore[arg-type]
    )

    with pytest.raises(
        ValueError,
        match="both input and output",
    ):
        service.compile(
            ContractSourceText("Invalid contract.")
        )



    
def test_compile_and_persist_real_uow_rolls_back_on_repository_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.application.services.deterministic_contract_compiler import (
        DeterministicFinancialContractCompiler,
    )
    from app.db.models.financial import FinancialContractModel
    from app.db.unit_of_work import FinancialUnitOfWork
    from tests.conftest import create_session

    session = create_session()
    unit_of_work = FinancialUnitOfWork(session)

    service = FinancialContractCompilerService(
        compiler=DeterministicFinancialContractCompiler(),
        unit_of_work=unit_of_work,
    )

    original_add = unit_of_work.contracts.add

    def failing_add(contract):
        original_add(contract)
        raise RuntimeError(
            "Simulated contract persistence failure."
        )

    monkeypatch.setattr(
        unit_of_work.contracts,
        "add",
        failing_add,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated contract persistence failure",
    ):
        service.compile_and_persist(
            ContractSourceText("Rollback Contract")
        )

    session.expire_all()

    assert (
        session.query(FinancialContractModel).count()
        == 0
    )
    
def test_persisted_compiled_contract_can_be_retrieved_as_domain_contract() -> None:
    from app.application.services.deterministic_contract_compiler import (
        DeterministicFinancialContractCompiler,
    )
    from app.application.services.financial_contract import (
        FinancialContractApplicationService,
    )
    from app.db.unit_of_work import FinancialUnitOfWork
    from tests.conftest import create_session

    session = create_session()

    compiler_service = FinancialContractCompilerService(
        compiler=DeterministicFinancialContractCompiler(),
        unit_of_work=FinancialUnitOfWork(session),
    )

    result = compiler_service.compile_and_persist(
        ContractSourceText("Retrievable Contract")
    )

    contract_service = FinancialContractApplicationService(
        FinancialUnitOfWork(session),
    )

    restored = contract_service.get_contract(
        result.contract.id
    )

    assert restored is not None
    assert restored.id == result.contract.id
    assert restored.name == result.contract.name
    assert restored.version == result.contract.version
    
def test_compiler_end_to_end_preserves_contract_identity_and_rules() -> None:
    from app.application.services.deterministic_contract_compiler import (
        DeterministicFinancialContractCompiler,
    )
    from app.application.services.financial_contract import (
        FinancialContractApplicationService,
    )
    from app.db.unit_of_work import FinancialUnitOfWork
    from tests.conftest import create_session

    session = create_session()

    compiler_service = FinancialContractCompilerService(
        compiler=DeterministicFinancialContractCompiler(),
        unit_of_work=FinancialUnitOfWork(session),
    )

    source = ContractSourceText(
        "End To End Financial Contract"
    )

    compiled = compiler_service.compile_and_persist(source)

    contract_service = FinancialContractApplicationService(
        FinancialUnitOfWork(session),
    )

    restored = contract_service.require_contract_version(
        compiled.contract.name,
        compiled.contract.version,
    )

    assert restored.id == compiled.contract.id
    assert restored.name == compiled.contract.name
    assert restored.version == compiled.contract.version
    assert (
        restored.minimum_confidence
        == compiled.contract.minimum_confidence
    )
    assert (
        restored.minimum_supported_claim_ratio
        == compiled.contract.minimum_supported_claim_ratio
    )
    assert (
        restored.required_claim_types
        == compiled.contract.required_claim_types
    )

