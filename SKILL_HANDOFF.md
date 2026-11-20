# BDD Skill Handoff Architecture

This document defines how the four modular skills in `/home/ccwu/Projects/bdd` route work, exchange artifacts, enforce quality gates, and escalate backwards when downstream steps uncover upstream gaps.

---

## 1. Handoff & Feedback Flowchart

`bdd-workflow` acts as the entry-point router and lifecycle coordinator. Individual skills can also be invoked standalone when a team enters mid-stream (for example, formulating directly from an existing Example Map or automating pre-approved `.feature` files).

```mermaid
flowchart TD
    Req["User Prompt or Feature Request"] --> Triage{"bdd-workflow Step 0: Entry-Point Triage"}

    Triage -->|"Ambiguous scope, missing rules or examples"| Disc["Phase 1: bdd-discovery (Example Mapping)"]
    Triage -->|"Rules & examples agreed, no .feature yet"| Form["Phase 2: bdd-formulation (BRIEF Gherkin)"]
    Triage -->|"Approved .feature scenarios already exist"| Auto["Phase 3: bdd-automation (Double Loop)"]

    Disc --> G1{"Gate 1: Open Questions resolved & slice <= 5-6 rules?"}
    G1 -->|"Blocking questions or oversized story"| UserQ["Ask User / Propose Vertical Slices"]
    UserQ --> Disc
    G1 -->|"Approved Example Map (Goal, Rules, Examples)"| Form

    Form --> Lint["Run lint_gherkin.py on .feature files"]
    Lint --> G2{"Gate 2: 0 syntax errors & BRIEF clean?"}
    G2 -->|"Errors or UI/HTTP/DB leakage warnings"| Form
    G2 -->|"Contradictory or missing business rule discovered"| Disc
    G2 -->|"Validated .feature specs"| Auto

    subgraph DoubleLoop["Single-Scenario Double Loop (Walking Skeleton first, then rule by rule)"]
        Auto --> OuterRed["Outer Red: Thin steps (1-5 lines) + Driver/Screenplay Task"]
        OuterRed --> InnerTDD["Inner Unit TDD: Red -> Green -> Refactor"]
        InnerTDD --> OuterGreen["Outer Green: Target scenario passes; refactor drivers & code"]
    end

    OuterRed -->|"Imperative or leaky Gherkin step phrasing"| Form
    InnerTDD -->|"Undecided domain policy or edge case"| Disc
    OuterGreen -->|"More scenarios remain in slice"| Auto
    OuterGreen -->|"All slice scenarios green"| Phase4["Phase 4: bdd-workflow Living Documentation Check"]

    Phase4 --> Verify["Run full unit + acceptance + linter checks; audit seam balance"]
    Verify --> Done["Verified Feature & Living Documentation"]
```

---

## 2. End-to-End Handoff Sequence

```mermaid
sequenceDiagram
    actor User
    participant W as bdd-workflow
    participant D as bdd-discovery
    participant F as bdd-formulation
    participant L as lint_gherkin.py
    participant A as bdd-automation

    User->>W: Submit feature request or task
    W->>W: Triage workspace & prompt state

    alt Rules or examples are unclear
        W->>D: Hand off raw request for discovery
        D->>D: Run Feature Injection & Example Mapping
        opt Blocking Open Questions or > 5-6 rules
            D-->>User: Present Example Map, Questions & vertical slices
            User-->>D: Confirm rules, defaults & slice scope
        end
        D->>F: Hand off approved Example Map (Goal, Rules, Examples)
    else Rules agreed, no .feature files
        W->>F: Route directly to formulation
    else Approved .feature files exist
        W->>A: Route directly to outside-in automation
    end

    F->>F: Author declarative BRIEF .feature files (with Rule: blocks)
    F->>L: Validate syntax & BRIEF heuristics
    L-->>F: Pass (0 errors, warnings resolved)

    opt Formulation spots missing or conflicting rule
        F-->>D: Escalate ambiguity to Example Mapping
    end

    F->>A: Hand off validated .feature specifications

    loop One scenario at a time (Walking Skeleton first)
        A->>A: Outer Red — wire thin steps + Domain Driver / Screenplay Task
        A->>A: Inner TDD — Red -> Green -> Refactor unit tests & domain code
        A->>A: Outer Green — pass target scenario & refactor
        opt Step writing exposes leaky Gherkin or missing policy
            A-->>F: Refactor Gherkin phrasing to declarative intent
            A-->>D: Escalate undecided business rule to User
        end
    end

    A->>W: Return automated steps, drivers, unit tests & passing suite
    W->>W: Phase 4 — verify full unit/BDD suites, linter & fast seam balance
    W-->>User: Deliver passing implementation & living documentation
```

---

## 3. Handoff Contracts & Direct Entry Points

### Forward & Feedback Transitions

| Transition | Trigger Condition | Artifact Handed Off | Gate / Acceptance Condition |
| :--- | :--- | :--- | :--- |
| [`bdd-workflow`](./skills/bdd-workflow/SKILL.md) → [`bdd-discovery`](./skills/bdd-discovery/SKILL.md) | Scope is ambiguous, rules are unexamined, or concrete examples/boundaries are missing | Feature goal prompt and codebase context | Entry triage confirms requirements are not yet settled |
| [`bdd-discovery`](./skills/bdd-discovery/SKILL.md) → [`bdd-formulation`](./skills/bdd-formulation/SKILL.md) | Example Map completed for the current vertical slice | Structured Example Map (Goal/Actor/Capability, Rules, Examples + counter-examples) | **Gate 1:** Blocking Open Questions resolved with user (no silent policy invention); slice holds `<= 5–6` rules |
| [`bdd-formulation`](./skills/bdd-formulation/SKILL.md) → [`bdd-automation`](./skills/bdd-automation/SKILL.md) | Gherkin `.feature` files authored and reviewed | Declarative `.feature` specs (`Feature`, `Rule`, `Background`, `Scenario`, `Scenario Outline`) | **Gate 2:** [`lint_gherkin.py`](./skills/bdd-formulation/scripts/lint_gherkin.py) passes with 0 structural errors and BRIEF compliance (zero UI/HTTP/DB leakage) |
| [`bdd-automation`](./skills/bdd-automation/SKILL.md) → [`bdd-workflow`](./skills/bdd-workflow/SKILL.md) | All scenarios in the slice pass outer acceptance and inner unit tests | Thin step glue, Drivers/Screenplay Tasks, test data builders, unit-tested production code | Zero skipped/pending steps; fresh per-scenario state; fast domain/service seam balance verified in [outside-in-loop.md](./skills/bdd-workflow/references/outside-in-loop.md) |
| **Backward:** `bdd-formulation` → `bdd-discovery` | Writing concrete `Given–When–Then` uncovers contradictory or undefined rules | Conflicting rule or uncovered boundary | Resolved via Example Map update and user confirmation |
| **Backward:** `bdd-automation` → `bdd-formulation` | Wiring steps reveals UI selectors, HTTP details, or multi-journey chains in Gherkin | Imperative or bloated scenario | Refactored using [brief-anti-patterns.md](./skills/bdd-formulation/references/brief-anti-patterns.md) and re-linted |
| **Backward:** `bdd-automation` → `bdd-discovery` | Inner TDD exposes an unspecified error path, rounding rule, or concurrency policy | Concrete edge-case question | Clarified with user before inventing domain policy |

### Standalone Direct Invocations

- **Invoke [`bdd-discovery`](./skills/bdd-discovery/SKILL.md) alone** (with [example-mapping-patterns.md](./skills/bdd-discovery/references/example-mapping-patterns.md)) when running requirements discovery or slicing a backlog item before any implementation starts.
- **Invoke [`bdd-formulation`](./skills/bdd-formulation/SKILL.md) alone** (with [`lint_gherkin.py`](./skills/bdd-formulation/scripts/lint_gherkin.py)) when converting an existing Example Map or refactoring brittle legacy `.feature` files.
- **Invoke [`bdd-automation`](./skills/bdd-automation/SKILL.md) alone** (with [screenplay-and-drivers.md](./skills/bdd-automation/references/screenplay-and-drivers.md) and [typescript.md](./skills/bdd-automation/references/typescript.md), [python.md](./skills/bdd-automation/references/python.md), or [rust.md](./skills/bdd-automation/references/rust.md)) when `.feature` specs are already approved and only step wiring, driver architecture, or outside-in TDD implementation is needed.
