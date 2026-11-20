---
name: bdd-discovery
description: >-
  Use when exploring requirements before coding, conducting Example Mapping,
  clarifying ambiguous user stories, surfacing hidden business rules and edge cases,
  or slicing large features into vertical BDD delivery increments.
---

# BDD Discovery & Example Mapping

Conduct deliberate discovery (*The BDD Books: Discovery*, Nagy & Rose; *BDD in Action, 2nd Ed.*) to turn vague requests into **Rules**, **Concrete Examples**, and **Open Questions** before writing `.feature` files or code.

---

## Step 1: Feature Injection (Anchor Business Value First)

Invert the traditional user story so business outcome drives scope:

```text
In order to <measurable business goal or user value>
As a <specific stakeholder / actor>
I want <capability>
```

Challenge solution-shaped requests (*"Add a Redis cache / modal popup"*) by asking what observable outcome the user or business needs.

---

## Step 2: Build the Example Map

Decompose the story into four explicit card types:

1. **Story / Feature**: One cohesive capability under exploration.
2. **Rules**: Explicit invariants, validations, pricing policies, state transition guards, or authorization constraints.
   - Express each rule as a verifiable business statement (never as an implementation task like *"create DB column"*).
3. **Examples (under each Rule)**: Concrete `Context State → Trigger Action → Observable Outcome` triples using specific, realistic domain values.
   - Provide **at least one positive example** and **at least one counter-example or boundary case** for every non-trivial rule.
4. **Questions**: Ambiguities, conflicting rules, or unspecified error/recovery outcomes.

---

## Step 3: Deliberate Edge-Case Interrogation

Scan every rule systematically across these four dimensions to catch hidden examples:

- **Boundaries & Zeroes**: `0`, exact threshold, `threshold - 1`, `threshold + 1`, empty collections, currency rounding, max lengths.
- **State Preconditions**: Unauthenticated, expired, suspended, already-completed, duplicate submission, insufficient balance/quota.
- **Actor & Permission Splits**: Owner vs admin vs guest; multi-party workflows where Actor A triggers and Actor B observes.
- **Side Effects & Failure Recovery**: Idempotency on retry, notifications, audit entries, partial failures, rollback behavior.

---

## Step 4: Diagnose Map Smells & Slice Vertically

Inspect the completed map before moving to Formulation:

| Smell | Diagnosis | Action |
| :--- | :--- | :--- |
| **Many Questions** | Requirements are under-specified | Stop and ask the user grouped, concise questions with concrete candidate defaults before writing specs or code. |
| **> 5–6 Rules** | Story is too large for one increment | Propose **vertical slices**: Slice 1 = Walking Skeleton happy rule; Slices 2..N = individual exception/policy rules. |
| **Many Examples on 1 Rule** | Either a second hidden rule exists, or it is a calculation table | Extract the hidden rule, or mark the rule as a `Scenario Outline` table candidate during Formulation. |
| **Rule with 0 Examples** | Unverified assumption or empty abstraction | Write a concrete example or convert the gap into an Open Question. |

---

## Step 5: Example Map Output Template

Present the map cleanly for confirmation (or internal planning when requirements are unambiguous) using this layout:

```markdown
### Feature: <Name>
- **Goal**: In order to <value>
- **Actor**: As a <role>
- **Capability**: I want <capability>

#### Rule 1: <Clear business policy>
- **Example**: <State> → <Trigger> → <Outcome>
- **Counter-example / Boundary**: <State> → <Trigger> → <Outcome>

#### Rule 2: <Next business policy>
- **Example**: ...

#### Open Questions
1. <Question>? *(Proposed default: ...)*

#### Proposed Vertical Slices (if > 5 rules)
- **Slice 1 (Walking Skeleton)**: Rule 1 happy path
- **Slice 2**: ...
```

For a complete worked example and slicing patterns, read [example-mapping-patterns.md](./references/example-mapping-patterns.md).
