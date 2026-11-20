---
name: bdd-formulation
description: >-
  Use when writing, reviewing, refactoring, or linting Gherkin .feature files
  (Feature, Rule, Scenario, Scenario Outline, Given-When-Then), translating
  Example Maps into executable specifications, or eliminating brittle UI/API leakage.
---

# BDD Formulation & BRIEF Gherkin Specification

Formulate discovered rules and examples into readable, durable **living documentation** (*The BDD Books: Formulation*, Nagy & Rose; *BDD in Action, 2nd Ed.*).

---

## 1. The BRIEF Principles

Audit every `.feature` file against all five BRIEF criteria:

| Principle | Standard | Avoid |
| :--- | :--- | :--- |
| **B — Business language** | Use ubiquitous domain terms shared with product/business stakeholders. | CSS/XPath selectors (`#btn`), widget verbs (`click`, `hover`, `dropdown`), HTTP paths/codes (`POST /api`, `422`), SQL/class names. |
| **R — Real data** | Use concrete, self-explanatory domain values (`$100`, `alice@example.com`, `2026-03-01`) whose math/logic is obvious at a glance. | Placeholder strings (`"foo"`, `"bar"`, `"test123"`) or vague nouns (`"some valid user"`). |
| **I — Intention-revealing** | Name scenarios after the behavior/rule outcome; phrase steps around actor intent (`When Maya submits her order`). | Implementation descriptions (`Scenario: Test POST /orders endpoint`, `When user clicks submit button`). |
| **E — Essential** | Include *only* state and fields causal to this scenario's outcome. Push required boilerplate defaults into step-layer builders. | Ten `Given` fields irrelevant to the rule being illustrated ("incidental detail"). |
| **F — Focused** | Test **one** rule/behavior per scenario (`Given` state → `When` single trigger → `Then` observable postcondition). | Multi-journey "ping-pong" chains (`When... Then... When... Then...`). |

---

## 2. Gherkin Structural Standards

1. **Feature Header**: State who wants what and why (`In order to... As a... I want...` or concise domain summary).
2. **`Rule:` Grouping (Gherkin 6+)**: Group related scenarios under `Rule: <business rule>` whenever a feature enforces 2+ distinct policies.
   - *Compatibility note:* Cucumber.js, `behave`, `cucumber-rs`, and `pytest-bdd >= 8.0` support `Rule:` natively. Only if constrained to legacy `pytest-bdd < 8.0` should you split by separate `.feature` files or `@rule_*` tags instead.
3. **`Background:` Discipline**:
   - Limit to **1–4** essential `Given` steps shared by *every* scenario in its scope (`Feature` or `Rule`).
   - **Never** put `When` or `Then` inside `Background:`.
4. **`Scenario Outline:` + `Examples:`**:
   - Use only when multiple examples share identical step structure (e.g., fee tiers, boundary thresholds).
   - Give `Examples:` blocks meaningful names (`Examples: Eligible tiers` / `Examples: Rejected amounts`) rather than dumping 20 rows into one table.
5. **Step Tense & Role Clarity**:
   - `Given` — past or current precondition state (*"Maya's account has a balance of $100"*).
   - `When` — single present-tense trigger by a clear actor (*"Maya requests a withdrawal of $40"*).
   - `Then` — observable postcondition (*"$40 should be dispensed"* / *"the remaining balance should be $60"*), never another action.

---

## 3. Mandatory Validation Step

Always run [lint_gherkin.py](./scripts/lint_gherkin.py) after creating or modifying `.feature` files:

```bash
python3 <path-to-skill-dir>/scripts/lint_gherkin.py path/to/features
# Use --strict in CI or review gates to fail on BRIEF heuristic warnings too:
python3 <path-to-skill-dir>/scripts/lint_gherkin.py --strict path/to/features
```

Resolve **all structural errors** (missing `When`/`Then`, `When` inside `Background`, mismatched `Scenario Outline` placeholders, unclosed docstrings, malformed tables) and fix **BRIEF warnings** (`IMPERATIVE_UI`, `TECHNICAL_LEAKAGE`, `MULTIPLE_WHEN_THEN`, `PLACEHOLDER_DATA`, `SCENARIO_TOO_LONG`, `BACKGROUND_TOO_LONG`, `VAGUE_TITLE`).

> **Domain Exception:** If the system under test *explicitly is* an HTTP API gateway, webhook contract, or CLI tool whose domain *is* HTTP headers or shell commands, technical terms in `.feature` files may be intentional—otherwise push protocol details down into the automation driver layer.

For worked refactoring examples, see [brief-anti-patterns.md](./references/brief-anti-patterns.md).
