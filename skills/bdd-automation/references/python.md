# Python BDD Automation Guide

Idiomatic patterns using **`pytest-bdd >= 8.0`** (recommended for `pytest` codebases) and **`behave`**, with `Protocol`-based multi-seam drivers.

> **Version Warning (`pytest-bdd`):** Gherkin 6+ `Rule:` blocks require **`pytest-bdd >= 8.0.0`** (which uses `gherkin-official`). Earlier `pytest-bdd` (< 8.0) versions fail to parse `Rule:` keywords.

---

## 1. Runner Selection

| Use Case | Recommended Tool | Why |
| :--- | :--- | :--- |
| **Standard Python / FastAPI / Django / Playwright** | `pytest-bdd >= 8.0` | Native `Rule:` support, full `pytest` fixture DI, `pytest-playwright` integration, unified unit + BDD reporting. |
| **Standalone Acceptance Suite** | `behave` | Explicit `context` lifecycle (`before_scenario`), native `Rule:` support, familiar Cucumber-style steps. |

---

## 2. Multi-Seam Driver Protocol (`pytest-bdd >= 8.0`)

Define a `Protocol` for layer-3 drivers and select the concrete implementation via a `pytest` fixture (`--seam=domain` default for speed, `--seam=http` or `@ui` for Walking Skeletons):

```python
# tests/bdd/drivers.py
from dataclasses import dataclass, field
from typing import Protocol


class AccountDriver(Protocol):
    def open_account(self, owner: str, balance_dollars: int) -> None: ...
    def withdraw(self, owner: str, amount_dollars: int) -> None: ...
    def balance_of(self, owner: str) -> int: ...
    def last_rejection(self) -> str | None: ...


@dataclass
class DomainAccountDriver:
    """Fast in-process seam driving domain entities directly."""
    # Fresh per-scenario repository/state
    _accounts: dict[str, int] = field(default_factory=dict)
    _rejection: str | None = None

    def open_account(self, owner: str, balance_dollars: int) -> None:
        self._accounts[owner] = balance_dollars

    def withdraw(self, owner: str, amount_dollars: int) -> None:
        bal = self._accounts[owner]
        if amount_dollars > bal:
            self._rejection = "insufficient funds"
            return
        self._accounts[owner] = bal - amount_dollars

    def balance_of(self, owner: str) -> int:
        return self._accounts[owner]

    def last_rejection(self) -> str | None:
        return self._rejection
```

```python
# tests/bdd/conftest.py
import pytest
from tests.bdd.drivers import AccountDriver, DomainAccountDriver


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--seam", action="store", default="domain", choices=["domain", "ui"])


@pytest.fixture
def account_driver(request: pytest.FixtureRequest) -> AccountDriver:
    seam = request.config.getoption("--seam")
    if seam == "ui":
        # Return Playwright-backed driver wrapping `request.getfixturevalue("page")`
        ...
    return DomainAccountDriver()
```

```python
# tests/bdd/test_withdrawal_steps.py
from pytest_bdd import given, parsers, scenarios, then, when
from tests.bdd.drivers import AccountDriver

scenarios("../../features/withdrawal.feature")


@given(parsers.parse("{owner}'s account has a balance of ${balance:d}"))
def open_account(account_driver: AccountDriver, owner: str, balance: int) -> None:
    account_driver.open_account(owner, balance)


@when(parsers.parse("{owner} requests a withdrawal of ${amount:d}"))
def withdraw_cash(account_driver: AccountDriver, owner: str, amount: int) -> None:
    account_driver.withdraw(owner, amount)


@then(parsers.parse("{owner}'s remaining balance should be ${expected:d}"))
def check_balance(account_driver: AccountDriver, owner: str, expected: int) -> None:
    assert account_driver.balance_of(owner) == expected
```

---

## 3. Functional State Pattern (`target_fixture`)

For immutable domain workflows without mutable driver fields, use `target_fixture` on `@given` / `@when` steps so `pytest-bdd` binds return values directly into downstream step fixtures.

---

## 4. Verification Commands

```bash
# Run BDD scenarios (fast domain seam) + inner unit tests
pytest tests/unit
pytest tests/bdd
pytest tests/bdd -k "sufficient_funds"

# Run full-stack UI Walking Skeletons
pytest tests/bdd -m ui --seam=ui

# If using behave instead of pytest-bdd:
behave features/withdrawal.feature
behave --tags=@smoke
```
