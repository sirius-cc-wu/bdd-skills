# Rust BDD Automation Guide

Idiomatic patterns using the **`cucumber`** crate + **`tokio`** for outer acceptance scenarios, paired with standard `cargo test --lib` for inner-loop unit TDD.

---

## 1. Crate Setup (`Cargo.toml`)

Disable Rust's default test harness on the BDD integration test target so `cucumber` drives execution, Gherkin `Rule:` hierarchy, and rich living-documentation output:

```toml
[dev-dependencies]
cucumber = "0.23" # Or latest compatible 0.21+ / 0.23+ release
tokio = { version = "1", features = ["macros", "rt-multi-thread"] }

[[test]]
name = "bdd"
harness = false
```

---

## 2. World, Newtype Parsers & Multi-Seam Driver (`tests/bdd.rs`)

Keep domain types strongly typed via `cucumber::Parameter` / `FromStr`, hold per-scenario state inside `#[derive(Debug, cucumber::World)]`, and delegate step bodies to a clean Driver trait or enum (`InMemoryDriver` vs `HttpDriver`):

```rust
// tests/bdd.rs
use std::str::FromStr;
use cucumber::{given, then, when, Parameter, World};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Parameter)]
#[param(regex = r"\d+", name = "dollars")]
struct Dollars(u64);

impl FromStr for Dollars {
    type Err = std::num::ParseIntError;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Ok(Self(s.parse()?))
    }
}

#[derive(Debug, Default)]
enum AccountDriver {
    #[default]
    InMemory,
    // Add Http(reqwest::Client, String) for @api / walking skeleton seam
}

#[derive(Debug, World)]
#[world(init = Self::new)]
struct BddWorld {
    driver: AccountDriver,
    balance: u64,
    last_error: Option<String>,
}

impl BddWorld {
    fn new() -> Self {
        Self {
            driver: AccountDriver::InMemory,
            balance: 0,
            last_error: None,
        }
    }
}

#[given(expr = "the account balance is ${dollars}")]
async fn set_balance(world: &mut BddWorld, amount: Dollars) {
    world.balance = amount.0;
}

#[when(expr = "the account holder requests ${dollars}")]
async fn request_withdrawal(world: &mut BddWorld, amount: Dollars) {
    if amount.0 > world.balance {
        world.last_error = Some("insufficient funds".into());
    } else {
        world.balance -= amount.0;
    }
}

#[then(expr = "the account balance should be ${dollars}")]
async fn assert_balance(world: &mut BddWorld, expected: Dollars) {
    assert_eq!(world.balance, expected.0);
}

#[tokio::main]
async fn main() {
    BddWorld::run("features").await;
}
```

> **Tip for Modular Suites:** Keep step modules under `tests/steps/*.rs`, expose `BddWorld` in `tests/world.rs`, and call `BddWorld::cucumber().run_and_exit("features").await;` (ensures non-zero exit code in CI on failed or skipped scenarios!). Use `run_and_exit` over plain `run` in CI pipelines.

---

## 3. Data Tables & Docstrings

Access Gherkin tables and docstrings cleanly via `step: &cucumber::gherkin::Step`:

```rust
use cucumber::{given, gherkin::Step};

#[given("the catalog contains:")]
async fn seed_catalog(world: &mut BddWorld, step: &Step) {
    if let Some(table) = step.table() {
        for row in table.rows.iter().skip(1) {
            let (sku, price) = (&row[0], &row[1]);
            world.seed_item(sku, price);
        }
    }
}
```

---

## 4. Verification Commands

```bash
# Inner-loop unit TDD (fast domain/module feedback)
cargo test --lib

# Outer acceptance suite (all features)
cargo test --test bdd

# Filter single scenario by name regex or tag (flags after `--` go to cucumber CLI)
cargo test --test bdd -- -n "Withdrawing cash"
cargo test --test bdd -- -t "@smoke and not @wip"
```
