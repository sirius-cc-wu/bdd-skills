# TypeScript / JavaScript BDD Automation Guide

Idiomatic patterns using **`playwright-bdd`** (Browser / Full-Stack E2E), **`@cucumber/cucumber`** (Domain / API / Multi-seam), and **Vitest** (Inner-loop Unit TDD).

---

## 1. Runner Selection

| Use Case | Recommended Stack | Why |
| :--- | :--- | :--- |
| **Full-Stack / Browser E2E (`@ui`)** | `playwright-bdd` + `@playwright/test` | Compiles `.feature` into native Playwright tests (`bddgen`) with parallel workers, traces, fixtures, and web-first auto-waiting assertions. |
| **Domain / Service / Multi-Seam** | `@cucumber/cucumber` + `tsx` + `vitest` | Lightweight fast execution directly against TypeScript domain modules or HTTP handlers with custom `World` DI. |

---

## 2. Browser / E2E Pattern with `playwright-bdd`

Keep Playwright's `page` wrapped inside a fixture-injected **Actor / Screenplay** or **AppDriver** so steps stay free of selectors.

```typescript
// tests/bdd/fixtures.ts
import { test as base } from 'playwright-bdd';
import { expect, type Page } from '@playwright/test';

export class CheckoutDriver {
  constructor(private readonly page: Page) {}

  async seedCartWithSubtotal(dollars: number): Promise<void> {
    // Seed preconditions quickly via API or test fixture endpoint, not UI clicks
    await this.page.request.post('/test-support/cart', { data: { subtotalDollars: dollars } });
    await this.page.goto('/checkout');
  }

  async applyPromoCode(code: string): Promise<void> {
    await this.page.getByLabel('Promo code').fill(code);
    await this.page.getByRole('button', { name: 'Apply' }).click();
  }

  async expectDiscount(dollars: number): Promise<void> {
    await expect(this.page.getByTestId('discount-amount')).toHaveText(`$${dollars.toFixed(2)}`);
  }
}

export const test = base.extend<{ checkout: CheckoutDriver }>({
  checkout: async ({ page }, use) => {
    await use(new CheckoutDriver(page));
  },
});
```

```typescript
// tests/bdd/steps/checkout.steps.ts
import { createBdd } from 'playwright-bdd';
import { test } from '../fixtures';

const { Given, When, Then } = createBdd(test);

Given("Maya's cart contains items totaling ${int}", async ({ checkout }, subtotal: number) => {
  await checkout.seedCartWithSubtotal(subtotal);
});

When('she applies promo code {string}', async ({ checkout }, code: string) => {
  await checkout.applyPromoCode(code);
});

Then('the discount should be ${int}', async ({ checkout }, expected: number) => {
  await checkout.expectDiscount(expected);
});
```

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';
import { defineBddConfig } from 'playwright-bdd';

const testDir = defineBddConfig({
  features: 'features/**/*.feature',
  steps: 'tests/bdd/**/*.ts',
});

export default defineConfig({ testDir });
```

---

## 3. Fast Domain / Multi-Seam Pattern with `@cucumber/cucumber`

Use a `World` class holding a **Driver interface** selected at startup (`BDD_SEAM=domain` vs `http`), plus custom parameter types (`defineParameterType`) for domain value objects.

```typescript
// tests/bdd/support/world.ts
import { setWorldConstructor, World, Before } from '@cucumber/cucumber';
import { InMemoryAccountDriver, type AccountDriver } from './drivers/accountDriver';

export class BddWorld extends World {
  driver!: AccountDriver;
}

Before(function (this: BddWorld) {
  // Fresh driver per scenario: zero cross-scenario shared state
  this.driver = new InMemoryAccountDriver();
});

setWorldConstructor(BddWorld);
```

---

## 4. Verification Commands

```bash
# Playwright-BDD: generate & run all or filtered scenario
npx bddgen && npx playwright test
npx bddgen && npx playwright test -g "Qualifying for free shipping"

# Cucumber.js: run all or single line / tag
npx cucumber-js
npx cucumber-js features/promo_codes.feature:14
npx cucumber-js --tags "@smoke and not @wip"

# Inner-loop Unit TDD (Vitest)
npx vitest run
```
