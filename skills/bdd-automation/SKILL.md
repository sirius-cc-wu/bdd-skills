---
name: bdd-automation
description: >-
  Use when automating Gherkin scenarios, writing step definitions, designing BDD
  test architecture (Screenplay Pattern or Domain Drivers), choosing between UI,
  API, and domain test seams, or implementing BDD in TypeScript, Python, or Rust.
---

# BDD Automation & Test Architecture

Implement executable specifications cleanly (*BDD in Action, 2nd Ed.*, Smart & Molak) so acceptance suites stay fast, deterministic, and decoupled from UI/transport churn.

---

## 1. The Cardinal Rule: Strict 3-Layer Separation

Keep every automated scenario separated into three distinct layers:

1. **Layer 1 — Business Specification (`.feature`)**: Declarative domain behavior; zero implementation leakage.
2. **Layer 2 — Step Definitions & Business Tasks (Pure Glue)**:
   - Step functions must be **1–5 lines**: parse parameters, look up the **Actor / World / Driver**, execute a business **Task** or **Driver method**, or assert an observable **Question / Outcome**.
   - **Never** put CSS selectors, Playwright calls, HTTP client code, SQL queries, loops, or complex conditionals inside step definitions.
3. **Layer 3 — Technical Drivers / Screenplay Abilities & Interactions**:
   - Encapsulate DOM locators, HTTP requests, CLI calls, or direct domain calls inside dedicated **Domain Drivers** or **Screenplay Abilities/Actions/Questions**.
   - Read [screenplay-and-drivers.md](./references/screenplay-and-drivers.md) when choosing between Domain Drivers and the full Screenplay Pattern.

---

## 2. Seam Selection Heuristic (Fast by Default)

Execute scenarios at the lowest architectural seam that truthfully validates the rule:

- **Default to Fast Seams (Domain or In-Process Service/API):** Run business rules, calculations, state transitions, validations, and permission checks in milliseconds without launching browsers or real sockets.
- **Reserve Browser / Full E2E (`@ui` / `@e2e`) for Walking Skeletons & Critical Journeys:** Keep 5–15% of scenarios at the browser/full-stack seam to verify client-side state, rendering, and real integration wiring.
- **Swap Drivers, Not Gherkin:** Keep the same declarative `.feature` wording and bind different Driver/Ability implementations by tag or test profile (`@ui` vs `@domain`).

---

## 3. Scenario Isolation, Builders & Determinism

1. **Zero Shared Mutable State:** Construct a fresh `World` / DI container / test fixture per scenario; never rely on execution order.
2. **Test Data Builders:** Supply sensible domain defaults (`AccountBuilder().with_balance(100)`), setting only the attributes mentioned in the scenario's `Given` steps.
3. **Fast Precondition Seeding:** Even in `@ui` browser tests, seed `Given` state via domain/API helpers rather than clicking through UI setup screens (unless registration/creation *is* the scenario under test).
4. **Control Nondeterminism at Port Boundaries:** Inject deterministic `Clock`, `IdGenerator`, and external gateway fakes at application boundaries—never mock internal domain objects inside acceptance tests.

---

## 4. Outside-In Execution Loop

For each scenario:
1. Run the single target scenario first (**Outer Red** — fails on missing domain outcome, not missing step definitions).
2. Drop into **Inner Unit TDD** (`vitest` / `pytest` / `cargo test --lib`) to build domain entities, policies, and adapters test-first.
3. Return to the outer scenario until **Outer Green**, refactor duplication in both production code and drivers, then move to the next scenario.

---

## 5. Stack-Specific Implementation Guides

Load only the reference guide matching the target codebase:

- **TypeScript / JavaScript** (`playwright-bdd`, `@cucumber/cucumber`, Vitest): [typescript.md](./references/typescript.md)
- **Python** (`pytest-bdd >= 8.0`, `behave`, `pytest-playwright`): [python.md](./references/python.md)
- **Rust** (`cucumber` crate, `tokio`, `cargo test`): [rust.md](./references/rust.md)
