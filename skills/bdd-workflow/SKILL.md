---
name: bdd-workflow
description: >-
  Use when delivering features end-to-end with Behaviour-Driven Development (BDD),
  Acceptance-Test-Driven Development (ATDD), and Outside-In TDD—from ambiguous user
  requests through Example Mapping, Gherkin .feature specifications, thin step/driver
  automation, and inner-loop unit-tested production code.
---

# Full-Stack BDD Coding Workflow

Drive feature delivery from shared domain understanding to living documentation using the
**Discovery → Formulation → Automation (Double Loop)** workflow synthesized from
*BDD in Action (2nd Ed.)* and *The BDD Books: Discovery & Formulation*.

## Step 0: Entry-Point Triage (Do Not Repeat Settled Phases)

Inspect what already exists in the prompt and workspace before starting:

1. **Ambiguous scope, unexamined business rules, or missing concrete examples** → Start at
   **Phase 1 (Discovery)** using [bdd-discovery](../bdd-discovery/SKILL.md).
2. **Agreed business rules and concrete examples, but no `.feature` specs yet** → Start at
   **Phase 2 (Formulation)** using [bdd-formulation](../bdd-formulation/SKILL.md).
3. **Approved `.feature` scenarios already exist** → Start at
   **Phase 3 (Outside-In Automation & Implementation)** using [bdd-automation](../bdd-automation/SKILL.md).

---

## Phase 1: Deliberate Discovery (Example Mapping)

Follow [bdd-discovery](../bdd-discovery/SKILL.md) to map the feature before writing `.feature` files or production code:

1. Anchor **Business Goal** (*In order to...*), **Actor** (*As a...*), and **Capability** (*I want...*).
2. Enumerate explicit **Rules**, **Concrete Examples** (with boundary & counter-examples), and **Open Questions**.
3. If the story exceeds ~5–6 rules, propose vertical slices and confirm which slice ships first.

> **Gate — No Silent Policy Invention:** Never invent undocumented business rules, error policies, or financial/security thresholds silently. Ask concise, high-impact questions to resolve blocking ambiguities (or record explicit user-approved assumptions) before proceeding.

---

## Phase 2: Formulation (Executable Specifications)

Follow [bdd-formulation](../bdd-formulation/SKILL.md) to translate approved rules and examples into `.feature` files:

1. Write declarative Gherkin obeying **BRIEF** (*Business language, Real data, Intention-revealing, Essential, Focused*).
2. Group multi-rule features under `Rule:` blocks (when supported by the project's runner).
3. Validate every created or edited `.feature` file with [lint_gherkin.py](../bdd-formulation/scripts/lint_gherkin.py):

   ```bash
   python3 <path-to-skill-dir>/../bdd-formulation/scripts/lint_gherkin.py <feature-path>
   ```

> **Gate — Zero Technical Leakage:** Fix all linter errors and address warnings. `.feature` files must contain no CSS/XPath selectors, widget actions (`click`, `dropdown`), HTTP verbs/routes/status codes, or SQL/database details (unless the product itself is an HTTP gateway or CLI).

---

## Phase 3: The Double Loop (Outside-In Implementation)

Follow [bdd-automation](../bdd-automation/SKILL.md) and [outside-in-loop.md](./references/outside-in-loop.md). Work **strictly one scenario at a time**:

1. **Select the Next Scenario**
   - For greenfield features, start with a **Walking Skeleton**: the simplest happy-path scenario that exercises the real architectural seams end-to-end.
   - Follow with edge-case and counter-example scenarios rule by rule.

2. **Outer Loop — Red (Failing Acceptance Scenario)**
   - Implement thin step definitions (1–5 lines of glue) delegating to a **Domain Driver** or **Screenplay Task/Question**.
   - Select the fastest appropriate seam (default: Domain or In-Process Service/API; reserve Browser/E2E `@ui` for Walking Skeletons and critical user journeys).
   - Run the single target scenario and confirm it fails on the **missing business behavior** (not missing step glue or syntax errors).

3. **Inner Loop — Red → Green → Refactor (Unit TDD)**
   - Step inside the architecture boundary discovered by the failing driver/task.
   - Write focused unit tests for domain entities, value objects, policies, services, adapters, and UI components.
   - Cycle **Red → Green → Refactor** cleanly on unit tests, introducing ports/interfaces and in-memory or fake adapters at external I/O boundaries.
   - Re-run the outer scenario whenever inner units support the next slice of behavior.

4. **Outer Loop — Green & Refactor**
   - Verify the target acceptance scenario passes cleanly.
   - Refactor duplication across production modules, test data builders, and step drivers without breaking existing unit or acceptance tests.
   - Repeat from Step 1 for the next scenario.

---

## Phase 4: Living Documentation & Suite Verification

Before declaring a feature done:

1. Run the **full** unit test suite and acceptance test suite (and linter on modified `.feature` files).
2. Confirm zero skipped/pending steps, zero shared mutable state between scenarios, and accurate scenario titles matching implemented rules.
3. Verify seam balance: heavy rule permutations run at fast Domain/Service seams while Walking Skeletons verify full integration.
