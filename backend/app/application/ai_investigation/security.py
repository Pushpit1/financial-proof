"""Security policy for AI investigation tool execution."""

from collections.abc import Mapping, Sequence
from typing import Any

from app.application.ai_investigation.contracts import InvestigationTool


class InvestigationToolSecurityError(ValueError):
    """Raised when an AI investigation request violates security policy."""


class InvestigationToolSecurityPolicy:
    """Fail-closed security boundary for investigation tool arguments."""

    MAX_ARGUMENTS = 16
    MAX_KEY_LENGTH = 64
    MAX_STRING_LENGTH = 512
    MAX_COLLECTION_ITEMS = 32
    MAX_DEPTH = 3

    _ALLOWED_ARGUMENTS: dict[InvestigationTool, frozenset[str]] = {
        InvestigationTool.INSPECT_CONTRACT: frozenset(
            {"include_constraints"},
        ),
        InvestigationTool.INSPECT_EXECUTION: frozenset(),
        InvestigationTool.INSPECT_STATE: frozenset(),
        InvestigationTool.INSPECT_VIOLATION: frozenset(),
        InvestigationTool.INSPECT_FINANCIAL_IMPACT: frozenset(),
        InvestigationTool.REPLAY_SCENARIO: frozenset(),
        InvestigationTool.COMPARE_EXPECTED_ACTUAL: frozenset(),
    }

    def validate(
        self,
        tool: InvestigationTool,
        arguments: Mapping[str, Any],
    ) -> None:
        """Validate tool arguments before any handler is executed."""

        allowed = self._ALLOWED_ARGUMENTS.get(tool)

        if allowed is None:
            raise InvestigationToolSecurityError(
                f"Tool '{tool.value}' is not authorized by the security policy."
            )

        if len(arguments) > self.MAX_ARGUMENTS:
            raise InvestigationToolSecurityError(
                "Investigation tool argument count exceeds the security limit."
            )

        for key, value in arguments.items():
            if not isinstance(key, str):
                raise InvestigationToolSecurityError(
                    "Investigation tool argument names must be strings."
                )

            if not key or len(key) > self.MAX_KEY_LENGTH:
                raise InvestigationToolSecurityError(
                    "Investigation tool argument name is invalid."
                )

            if key not in allowed:
                raise InvestigationToolSecurityError(
                    f"Argument '{key}' is not allowed for tool '{tool.value}'."
                )

            self._validate_value(value, depth=0)

    def _validate_value(self, value: Any, *, depth: int) -> None:
        if depth > self.MAX_DEPTH:
            raise InvestigationToolSecurityError(
                "Investigation tool argument nesting exceeds the security limit."
            )

        if isinstance(value, str):
            if len(value) > self.MAX_STRING_LENGTH:
                raise InvestigationToolSecurityError(
                    "Investigation tool argument string exceeds the security limit."
                )
            return

        if value is None or isinstance(value, (bool, int, float)):
            return

        if isinstance(value, Mapping):
            if len(value) > self.MAX_COLLECTION_ITEMS:
                raise InvestigationToolSecurityError(
                    "Investigation tool argument mapping exceeds the security limit."
                )

            for key, item in value.items():
                if not isinstance(key, str):
                    raise InvestigationToolSecurityError(
                        "Nested investigation argument keys must be strings."
                    )
                if not key or len(key) > self.MAX_KEY_LENGTH:
                    raise InvestigationToolSecurityError(
                        "Nested investigation argument key is invalid."
                    )
                self._validate_value(item, depth=depth + 1)
            return

        if isinstance(value, Sequence) and not isinstance(
            value,
            (bytes, bytearray),
        ):
            if len(value) > self.MAX_COLLECTION_ITEMS:
                raise InvestigationToolSecurityError(
                    "Investigation tool argument collection exceeds the security limit."
                )

            for item in value:
                self._validate_value(item, depth=depth + 1)
            return

        raise InvestigationToolSecurityError(
            "Investigation tool argument contains an unsupported value type."
        )
