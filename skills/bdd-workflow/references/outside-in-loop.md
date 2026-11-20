# The BDD/TDD Double Loop & Seam Allocation

From *BDD in Action (2nd Ed.)* (Smart & Molak): acceptance tests specify **what** the system does from the outside; unit tests drive **how** components collaborate on the inside.

```text
  [Outer Loop: Acceptance / BDD]
   1. Pick ONE Scenario (Walking Skeleton first)
   2. Wire thin Steps -> Domain Driver / Screenplay Task
   3. Run scenario -> RED (fails on business assertion)
        │
        ▼
      [Inner Loop: Unit TDD]
       4. Write failing unit test for domain/service/adapter
       5. Write minimal code to pass -> GREEN
       6. Refactor design & eliminate duplication
       7. Repeat inner loop until scenario capability exists
        │
        ▼
   8. Re-run outer scenario -> GREEN
   9. Refactor drivers/builders, then pick next Scenario
```

---

## 1. The Walking Skeleton

A **Walking Skeleton** is the thinnest possible end-to-end slice that connects every real architectural layer (UI/Transport → Application Service → Domain → Persistence) with minimal domain logic.

- **Pick first:** The simplest non-trivial happy path (e.g., *withdrawing cash with sufficient funds* or *placing a valid single-item order*).
- **Defer until later scenarios:** Discounts, rate limits, concurrency locks, retries, and edge-case validations.
- **Why:** Exposes wiring, dependency injection, serialization, routing, and runner configuration defects in minutes instead of after days of isolated unit coding.

---

## 2. Discovering Collaborators Outside-In

When the outer step driver calls an entry point that does not exist yet:

1. **Wishful thinking API:** Write the call in the Domain Driver or Screenplay Task as the cleanest domain signature you wish existed (`account.withdraw(Dollars(40))`).
2. **Define ports at boundaries:** When domain logic needs time, IDs, payment gateways, or persistence, define a clean interface/trait/protocol (`Clock`, `PaymentGateway`, `AccountRepository`).
3. **Test-double in inner loop, verify real adapter at integration seam:**
   - Use fast in-memory fakes/stubs in unit TDD and fast domain acceptance runs.
   - Keep at least one real integration / E2E test per external adapter so fakes never drift from reality.

---

## 3. Seam Allocation (The BDD Test Pyramid)

Running 100% of `.feature` files through a real browser creates slow, brittle suites that teams abandon. Allocate scenarios intentionally across seams:

| Seam | Target Share | Best For | Speed |
| :--- | :--- | :--- | :--- |
| **Domain / In-Process Model** | 60–80% | Pricing rules, state machines, eligibility, limits, validation invariants | Milliseconds |
| **Service / In-Process API** | 15–30% | Authz, serialization, transactions, persistence wiring, multi-component workflows | Tens of ms |
| **Browser / Full-Stack E2E** | 5–15% | Walking Skeletons, critical multi-page UX journeys, visual/client-side state glue | Seconds |

### Keeping One Specification Across Seams

Never rewrite Gherkin to expose HTTP or DOM details when moving down a seam. Keep the **same declarative `.feature` wording** and swap the **Driver / Ability** implementation behind the step definitions (e.g., `@ui` tag selects `PlaywrightDriver`; default/fast profile selects `InMemoryDomainDriver` or `HttpApiDriver`).

---

## 4. Brownfield / Legacy Codebases

When introducing BDD to an existing codebase without clean boundaries:

1. **Characterize before changing:** Write 1–3 high-level Gherkin scenarios capturing current observable behavior around the area you are about to modify.
2. **Introduce a Driver seam:** Wrap legacy HTTP endpoints, CLI commands, or controllers behind a Domain Driver so step definitions stay clean while legacy internals are refactored incrementally.
3. **Strangle gradually:** New `Rule:` blocks drive clean domain modules via the Double Loop while legacy paths remain covered by characterization scenarios.
