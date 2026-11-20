# BRIEF Gherkin Anti-Patterns & Refactorings

Concrete Before → After refactorings based on *The BDD Books: Formulation* (Nagy & Rose) and *BDD in Action, 2nd Ed.*.

---

## 1. Imperative UI Scripting → Declarative Capability (**B, I**)

**Before (Brittle, coupled to DOM layout):**
```gherkin
Scenario: Test login
  Given I navigate to "https://app.example.com/login"
  When I type "maya@example.com" into the "#email-input" field
  And I type "CorrectHorse99!" into the "#password-input" field
  And I click the "Sign In" button
  Then the ".welcome-banner" element should contain "Welcome, Maya"
```

**After (Business language, seam-independent):**
```gherkin
Scenario: Registered member signs in with valid credentials
  Given Maya has an active account with password "CorrectHorse99!"
  When Maya signs in with her email and password "CorrectHorse99!"
  Then Maya should be greeted as an authenticated member
```

---

## 2. Transport / Database Leakage → Domain Behavior (**B**)

**Before (Exposes HTTP verbs, status codes, and SQL):**
```gherkin
Scenario: Reject duplicate email
  Given a row exists in the "users" table with email "foo@bar.com"
  When I send a POST request to "/api/v1/users" with JSON payload '{"email": "foo@bar.com"}'
  Then the response status code should be 409
```

**After (Pure domain intent; works across domain, API, or UI drivers):**
```gherkin
Rule: Each member account must use a unique email address

  Scenario: Rejecting registration with an already registered email
    Given a member is already registered with email "maya@example.com"
    When an applicant tries to register using email "maya@example.com"
    Then the registration should be rejected because the email is already in use
```

---

## 3. Incidental Detail Overload → Essential Defaults (**E, R**)

**Before (Noisy irrelevant attributes obscure why the rule triggers):**
```gherkin
Scenario: Free shipping
  Given a customer named "John Doe" with phone "555-0100" and billing address "12 Main St, Austin, TX"
  And a product SKU "ABC-999" in category "Books" weighing 1.2 kg priced at $60.00
  When the customer checks out using Visa ending in 4242
  Then shipping should be $0.00
```

**After (Only causal facts appear; builders supply defaults):**
```gherkin
Rule: Standard domestic orders of $50 or more qualify for free shipping

  Scenario: Qualifying for free shipping at the exact threshold
    Given Maya's cart contains items totaling $50.00
    When she checks out with standard domestic shipping
    Then the shipping fee should be $0.00
```

---

## 4. Ping-Pong Multi-Journey Scenarios → Focused Scenarios (**F**)

**Before (Chained `When → Then → When → Then` tests 3 features at once):**
```gherkin
Scenario: Order lifecycle
  Given an empty cart
  When Maya adds a $30 book to her cart
  Then the cart subtotal should be $30
  When Maya submits her order
  Then the order status should be "Pending"
  When Maya cancels the order
  Then the order status should be "Cancelled"
```

**After (Each scenario specifies one rule independently):**
```gherkin
Scenario: Adding an item updates the cart subtotal
  Given Maya has an empty cart
  When she adds a $30 book to the cart
  Then the cart subtotal should be $30

Scenario: Cancelling a pending order marks it cancelled
  Given Maya has a pending order
  When she cancels the order
  Then the order status should be "Cancelled"
```

---

## 5. Overloaded Background → Scoped Context (**E, F**)

**Before:** Feature-level `Background:` seeds 6 preconditions (promo code, loyalty tier, gift card, shipping address) even though half the scenarios only test cart item removal.

**After:** Keep feature-level `Background:` to 1–2 universally shared steps, move rule-specific setup into `Rule:`-scoped `Background:` blocks, and keep one-off preconditions inside individual `Scenario:` blocks.

---

## 6. Undifferentiated Mega-Outline → Grouped Rules & Named Examples (**I, F**)

**Before:** One 25-row `Scenario Outline` mixing domestic free shipping, international flat fees, VIP overrides, and invalid negative weights with cryptic flag columns (`is_vip | is_intl | expected_err | fee`).

**After:** Separate into distinct `Rule:` blocks (one per policy) and use compact, named `Examples:` tables only for numeric tier/boundary variations sharing the exact same sentence structure.

---

## 7. Passive / Actorless Steps → Explicit Actor Attribution (**I**)

**Before:** `When the order is approved` / `Then the notification is sent` (unclear *who* approved it—customer, warehouse staff, or billing webhook?).

**After:** `When warehouse manager Sam approves the order` / `Then buyer Maya should receive an approval confirmation`.
