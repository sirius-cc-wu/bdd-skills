# Example Mapping Worked Patterns & Story Slicing

Reference guide for turning vague feature prompts into concrete, vertically sliced Example Maps.

---

## Worked Example: "Add promo codes to checkout"

### Initial Prompt (Too Vague to Code)
> *"Users should be able to enter a promo code at checkout to get a discount."*

### Step 1: Feature Injection
- **In order to** run seasonal acquisition campaigns without changing catalog prices,
- **As a** registered shopper,
- **I want** to apply a valid promo code to my checkout order.

### Step 2: Example Map

#### Rule 1: Percentage promo codes reduce the merchandise subtotal
- **Example**: Cart subtotal `$100.00`, active code `SPRING20` (`20%` off) → shopper applies `SPRING20` → discount is `$20.00`, order subtotal becomes `$80.00`.
- **Boundary (Rounding)**: Cart subtotal `$10.01`, code `TEN` (`10%` off) → discount rounds half-even/half-up? *(Moved to Open Questions!)*.

#### Rule 2: Expired or unknown promo codes are rejected without changing the cart
- **Counter-example (Expired)**: Code `WINTER10` expired on `2026-03-01`; today is `2026-03-02` → applying `WINTER10` fails with "promo code expired"; cart remains `$100.00`.
- **Counter-example (Unknown)**: Code `NOPE99` does not exist → applying `NOPE99` fails with "invalid promo code".

#### Rule 3: Promo codes requiring a minimum spend only apply when threshold is met
- **Boundary (Exact match)**: Code `SAVE15` requires `$50.00` minimum; cart is `$50.00` → `SAVE15` applies.
- **Counter-example (`threshold - $0.01`)**: Cart is `$49.99` → `SAVE15` rejected with minimum spend reason.

#### Rule 4: Single-use per customer cannot be redeemed twice
- **Counter-example**: Shopper Maya already completed an order using `WELCOME10` → applying `WELCOME10` on a second order is rejected.

#### Open Questions (Resolve Before Coding)
1. **Shipping vs. Subtotal**: Does a percentage discount apply before or after shipping and tax? *(Proposed default: merchandise subtotal before tax and shipping.)*
2. **Stacking**: Can a shopper apply multiple promo codes simultaneously, or does entering a new code replace the previous one? *(Proposed default: at most one promo code per order; entering a new code replaces the active one.)*
3. **Rounding mode**: Should fractional cents round half-up or half-even? *(Proposed default: round half-up to nearest cent.)*

---

## Vertical Slicing Strategies

When a map grows beyond **5–6 Rules**, slice **vertically through every architectural layer** rather than horizontally ("build DB schema → build API → build UI"):

1. **Slice by Walking Skeleton First**: Deliver Rule 1 (single active percentage code, basic validation) end-to-end across UI/API/Domain/Persistence.
2. **Slice by Policy Rule**: Add Rule 3 (minimum spend) and Rule 2 (expiry) as independent increments.
3. **Slice by Exception / Edge Case**: Add Rule 4 (per-customer redemption tracking) once core redemption works.
4. **Slice by Actor / Channel**: Support guest vs. registered shoppers or admin code creation in follow-up slices.

---

## Spotting Fake Rules (Implementation Disguised as Policy)

| Implementation Task (Wrong Level) | Reframed Observable Business Rule |
| :--- | :--- |
| *"Store promo codes in a `promo_codes` PostgreSQL table"* | *"Promo code usage counts persist across user sessions and concurrent checkouts."* |
| *"Return HTTP 422 JSON with field `error_code`"* | *"Rejected promo codes leave the cart unchanged and tell the shopper why the code was declined."* |
| *"Use a dropdown and toast alert on the checkout page"* | *(Omit widget mechanics from Discovery/Gherkin; keep UI choices out of business rules.)* |
