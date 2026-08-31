from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class DeterministicClock:
    """Clock whose output is completely controlled by the simulation."""

    current: datetime
    step: timedelta = timedelta(seconds=1)

    def now(self) -> datetime:
        """Return the current deterministic timestamp."""
        return self.current

    def advance(self, steps: int = 1) -> datetime:
        """Advance the clock by a deterministic number of steps."""
        if steps < 0:
            raise ValueError("Clock steps cannot be negative.")

        self.current = self.current + self.step * steps
        return self.current
