---

# **CODEx SCRIPT — Trading System Rebuild Constitution (v1)**

## **0\) Project identity**

**Project name:** Trading System (Strategy Lab–centric)  
**Repo:** `trading-system`  
**Primary objective:** Convert an existing backtesting-focused codebase into a **unified trading platform** that supports:

1. **Deterministic backtesting** (canonical)  
2. **Paper trading** (live-ish market data, simulated fills)  
3. **Broker-ready live trading** (adapter \+ reconciliation scaffolding)

…and does so with a **single authoritative risk engine** and **portable strategy interfaces** that can support AI/ML-driven idea generation without destabilizing execution.

---

## **1\) Non-negotiable architecture principles (do not violate)**

### **A. Single canonical orchestration path**

All backtests must route through **Strategy Lab** runner (not legacy wrappers).  
Legacy backtesting wrappers may remain temporarily, but only as **thin adapters** that delegate to Strategy Lab runner.

### **B. Risk is an enforcement gate, not analytics**

Order sizing, stop placement, drawdown gating, pyramiding (later) must be enforced by the **RiskEngine** before execution.  
No strategy or execution backend may bypass risk checks.

### **C. Execution is a pluggable backend**

Introduce an `ExecutionEngine` interface with implementations:

* `BacktestExecutionEngine` (deterministic)  
* `PaperExecutionEngine` (simulated fills, live-ish pricing)  
* `BrokerExecutionEngine` (adapter stub \+ reconciliation hooks)

### **D. Deterministic backtesting semantics**

**Backtest market order fills occur at the next bar OPEN.**  
This must be encoded into configuration and tested. No silent changes.

### **E. Stable contracts / schemas**

Define stable domain types (`Signal`, `OrderIntent`, `ExecutionReport`, etc.) in one place.  
All modules communicate via these contracts.

### **F. Backtest → Paper → Live parity**

The strategy \+ risk \+ execution lifecycle must be the same across modes, changing only:

* data source  
* execution backend

### **G. Persistence and observability are platform features**

For backtest runs and trading sessions, persist:

* configs (versioned)  
* trades and fills  
* portfolio equity history and drawdown history  
* risk rejections and execution events (at least as logs; ideally DB)

---

## **2\) Definitions and scope boundaries**

### **What this rebuild includes**

* Unified Strategy Lab backtest runner  
* Execution backend abstraction  
* Backtest engine with deterministic fills at next bar open \+ stop triggering  
* FastAPI endpoints to run backtests and retrieve results  
* Persistence to existing DB models (extend if needed)  
* Paper trading loop skeleton  
* Broker adapter scaffolding \+ reconciliation hooks (no secrets required)  
* ML runway: feature registry \+ model strategy interface \+ score→signal policy

### **What is explicitly out of scope (for now)**

* Full broker-specific implementation (IBKR/Alpaca) beyond adapter interface \+ mock  
* Complex microstructure simulation (partial fills, order book)  
* Distributed infrastructure, Kubernetes, high-availability  
* Real-time websockets UI (polling is acceptable)

---

## **3\) “Source of truth” for key behaviors**

### **Trade lifecycle (must remain consistent)**

1. Data provides bars/quotes (mode-specific)  
2. Strategy emits `Signal`  
3. RiskEngine evaluates portfolio state and config  
4. RiskEngine returns either:  
   * `OrderIntent` (approved, sized, stop attached)  
   * or `RiskViolation` (rejected)  
5. ExecutionEngine processes `OrderIntent`  
6. ExecutionEngine returns `ExecutionReport` (filled/rejected/partial)  
7. PortfolioState updates equity, drawdown, positions  
8. Metrics \+ persistence updated

### **Stop behavior (v1)**

* Stop-loss triggers if intrabar low/high crosses stop price.  
* Fill is at stop price (v1). (If later refined, must be versioned.)

### **Portfolio sizing base**

* Controlled by config:  
  * fixed notional sizing (initial equity)  
  * compounding sizing (current equity)

---

## **4\) Execution rules (how Codex must work)**

### **R1 — One PR at a time, no unplanned refactors**

Codex must not refactor unrelated modules “for cleanliness.”  
Only modify files needed for the PR scope.

### **R2 — Context Check-In at start of every PR**

At the beginning of each PR, Codex must produce a short checklist:

*  I understand the target architecture principles A–G.  
*  I will preserve next-bar-open fill semantics.  
*  I will not change public interfaces except those defined in this PR.  
*  I will ensure all prior tests still pass.

### **R3 — Add tests with every behavior change**

If behavior changes or a new module is introduced, add unit/integration tests.

### **R4 — Verification protocol at end of every PR**

Codex must run and report:

* lint (if configured)  
* unit tests  
* integration tests (tiny OHLCV fixture)  
* regression confirmation: all previous tests pass

### **R5 — Avoid drift: update docs and changelog**

Each PR must update:

* relevant README section OR a `docs/architecture.md`  
* a short entry in `CHANGELOG.md` or `docs/decisions.md` (if present)

### **R6 — Determinism and seeds**

All backtests must be deterministic:

* fixed fill rules  
* fixed ordering  
* fixed random seed when randomness exists

### **R7 — No hard-coded environment secrets**

Broker scaffolding must not require API keys; use mock adapters.

---

## **5\) Target module map (canonical)**

Codex should implement towards this structure; do not create parallel competing “cores”.

```
strategy_lab/
  core/
    types.py
    config.py
  backtest/
    runner.py
    metrics.py
    reports.py
  execution/
    base.py
    backtest_engine.py
    paper_engine.py
    broker_engine.py
    fees.py
    slippage.py
  risk/
    engine.py
    portfolio_state.py
  persistence/
    repo.py
    mappers.py
backend/
  api/
  services/
  db/
```

---

# **PR SERIES — Discrete work packages with check-in \+ verification**

## **PR 01 — Canonical domain contracts \+ config (no behavior change)**

**Goal:** Introduce stable types/configs used across modules.

**Work**

* Add `strategy_lab/core/types.py` and `strategy_lab/core/config.py`  
* Add tests: serialization / validation  
* No modifications elsewhere except imports if needed.

**Verification**

* Run tests; ensure existing tests pass.

---

## **PR 02 — Strategy Lab backtest runner v1 (minimal end-to-end)**

**Goal:** A single backtest entrypoint that can run one strategy end-to-end using existing RiskEngine.

**Work**

* Add `strategy_lab/backtest/runner.py`  
* Add tiny OHLCV fixture \+ integration test:  
  * strategy emits known signals (hardcoded)  
  * ensure runner produces equity curve \+ trade log  
* Runner should call risk engine and update PortfolioState.

**Verification**

* Integration test must be deterministic.

---

## **PR 03 — ExecutionEngine interface \+ BacktestExecutionEngine (NEXT BAR OPEN)**

**Goal:** Make execution pluggable; enforce next-bar-open fills.

**Work**

* Add `strategy_lab/execution/base.py`  
* Add `strategy_lab/execution/backtest_engine.py`  
* Update runner to use ExecutionEngine  
* Implement:  
  * market entry fill at next bar open  
  * stop-loss intrabar trigger  
* Tests:  
  * fill timing test (explicitly checks next bar open)  
  * stop trigger test

**Verification**

* Runner integration test updated; all tests pass.

---

## **PR 04 — Legacy backtest adapter (route everything through Strategy Lab)**

**Goal:** Preserve old entrypoints but delegate to Strategy Lab runner.

**Work**

* Add adapter module in legacy area that calls runner  
* Update UI/CLI entry to use runner (or adapter)  
* Add deprecation warnings in legacy runner

**Verification**

* A “legacy path” invocation test that asserts it delegates.

---

## **PR 05 — Backtest reporting outputs (DF \+ JSON) \+ consistent metrics**

**Goal:** Standardize outputs to feed UI/API.

**Work**

* Add `strategy_lab/backtest/reports.py`  
* Ensure outputs include:  
  * equity curve  
  * trade log  
  * summary metrics including max drawdown and cumulative return  
* Add tests comparing expected keys and shapes.

**Verification**

* Integration test checks report schema.

---

## **PR 06 — Persistence layer (map core types → DB)**

**Goal:** Save backtest runs, trades, equity history using existing DB models.

**Work**

* Add `strategy_lab/persistence/mappers.py` and `repo.py`  
* Add run id, config hash, and idempotency  
* Extend DB schema if missing `backtest_run` record (migration if needed)

**Verification**

* Test using sqlite (or existing test DB) to insert run \+ trades \+ history.

**Deferred cleanup (tracked)**

* Address SQLAlchemy 2.x deprecation warning in `backend/db/models.py` by migrating
  `sqlalchemy.ext.declarative.declarative_base` to
  `sqlalchemy.orm.declarative_base`.
* Schedule: execute during PR 07 (API + DB-touching phase) unless PR 06 schema
  updates make it lower-risk to include immediately.

---

## **PR 07 — FastAPI backtest endpoints**

**Goal:** Run backtests via API and fetch results.

**Work**

* Add `backend/services/backtest_service.py`  
* Add `backend/api/routes_backtest.py`:  
  * `POST /backtests/run`  
  * `GET /backtests/{run_id}/summary|trades|equity`  
* Pydantic request/response schemas  
* Wire into `backend/main.py`

**Verification**

* API tests (TestClient) cover run \+ fetch.

**Deferred test dependency (tracked)**

* Add `httpx` to dev/test dependencies so FastAPI `TestClient` HTTP-level route
  tests can run in CI and local verification without skipping.
* Schedule: add in PR 08 setup/tasks before expanding API test breadth.

---

## **PR 08 — Paper trading session skeleton \+ PaperExecutionEngine**

**Goal:** Introduce session control, state persistence, simulated fills using live-ish data provider abstraction.

**Work**

* Add `strategy_lab/execution/paper_engine.py`  
* Add `backend/services/trading_service.py` with polling “tick” loop callable  
* Add endpoints:  
  * `POST /trading/sessions/start`  
  * `POST /trading/sessions/stop`  
  * `GET /trading/sessions/{id}/status`  
* Use mock quote provider for tests

**Verification**

* Deterministic session test with mocked quotes.

---

## **PR 09 — Broker scaffolding \+ reconciliation hooks (mock only)**

**Goal:** Create adapter interface without committing to a broker.

**Work**

* Add `BrokerAdapter` interface \+ `MockBrokerAdapter`  
* Add `BrokerExecutionEngine` stub  
* Add reconciliation function:  
  * fetch positions/orders/fills  
  * align internal state

**Verification**

* Tests run against mock adapter; no secrets required.

---

## **PR 10 — ML runway: feature registry \+ model strategy interface**

**Goal:** Enable AI/ML-driven idea generation safely.

**Work**

* Add feature registry/pipeline  
* Add model interface \+ score→signal policy  
* Add a dummy model strategy backtest test

**Verification**

* Backtest can run ML strategy and produce stable outputs.

---

## **PR 11 — Remove legacy backtesting implementation (post-parity)**

**Goal:** Eliminate redundancy and prevent drift.

**Work**

* Remove legacy execution paths  
* Update docs and imports  
* Ensure everything routes through Strategy Lab

**Verification**

* Full test suite passes; no dangling imports.

---

# **PR template Codex must follow (copy/paste for each PR)**

## **Context Check-In**

*  Preserving next-bar-open fill semantics  
*  Strategy→Risk→Execution lifecycle preserved  
*  No bypass of RiskEngine  
*  No unrelated refactors  
*  All prior tests must remain green

## **Implementation Notes**

* Files changed:  
* New files:  
* Public interfaces added/changed:

## **Verification**

* Tests run:  
* Result:  
* Regression: all previous tests passing

---
