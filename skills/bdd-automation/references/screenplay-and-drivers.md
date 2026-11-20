# BDD Automation Architecture: Domain Drivers vs. Screenplay Pattern

Reference blueprint from *BDD in Action (2nd Ed.)* for keeping step definitions thin and reusable across seams.

---

## Choosing Your Layer-2/3 Pattern

| Criterion | Domain / Protocol Driver | Screenplay Pattern |
| :--- | :--- | :--- |
| **Best suited for** | Single-actor services, CLIs, domain libraries, small web apps | Multi-actor workflows (buyer + admin), rich browser + API flows, large suites |
| **Core abstraction** | One cohesive `Driver` interface per capability (`OrderDriver`) | **Actors** with **Abilities** performing **Tasks**/**Actions** and asking **Questions** |
| **Overhead** | Very low (1 interface + 1–2 concrete drivers) | Moderate initially; pays off rapidly once > ~20 scenarios share actions |
| **Multi-seam support** | Swap driver implementation (`InMemoryOrderDriver` vs `PlaywrightOrderDriver`) | Swap Actor's `Ability` or Task implementation per seam |

---

## The 5 Screenplay Building Blocks

```text
  Actor (e.g., Maya)
    ├── has Abilities ──────► BrowseTheWeb(page), CallApi(client), UseDomain(app)
    ├── attempts Tasks ─────► PlaceOrder(items) ──composes──► Actions (SelectItem, SubmitCheckout)
    └── asks Questions ─────► OrderStatus(), AccountBalance() ──used in──► Then assertions
```

1. **Actor (`Maya`, `WarehouseAdmin`)**: Represents the persona executing steps. Holds scoped state and granted **Abilities**.
2. **Ability (`BrowseTheWeb`, `CallRestApi`, `OperateInMemory`)**: Thin capability wrapper around a concrete tool (Playwright `Page`, HTTP client, or domain service).
3. **Task (`ApplyPromoCode.called("SPRING20")`, `WithdrawCash.amount(40)`)**: Domain-named composition of lower-level Actions or sub-Tasks. Step definitions call Tasks—never raw clicks.
4. **Action / Interaction (`ClickElement`, `PostJson`, `ExecuteCommand`)**: Single technical interaction using one of the Actor's Abilities.
5. **Question (`DisplayedDiscount()`, `CurrentBalance()`)**: Read-only query returning a domain value or state for `Then` assertions.

---

## Multi-Seam Polymorphism Blueprint

Keep step definitions completely unaware of whether a scenario runs against in-memory domain objects, an HTTP API, or a browser:

```text
  Feature Step: "When Maya requests a withdrawal of $40"
         │
         ▼
  Step Glue: actor.attemptsTo(WithdrawCash.amount(40))   [or driver.withdraw("Maya", 40)]
         │
         ├──► [@domain profile] ──► InMemoryAtmDriver / DomainAbility (0.5 ms)
         ├──► [@api profile]    ──► HttpAtmDriver / CallRestApi       (15 ms)
         └──► [@ui profile]     ──► PlaywrightAtmDriver / BrowseTheWeb (800 ms)
```

### Design Rules
- **Single source of truth for locators:** In UI drivers/actions, keep selectors (`getByRole`, `getByLabel`, `data-testid`) strictly inside Page/Target objects or Interaction classes—never in step definitions.
- **No assertions inside `When` Tasks:** Tasks perform actions; `Then` steps assert against **Questions** or driver query methods so failure diagnostics remain crystal clear.
- **Role-named constructors:** Prefer expressive factories (`WithdrawCash.amount(40)`) over raw primitives so step code reads like English.
