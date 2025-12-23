# Adult Finance Implementation Checklist

## Phase 1: Foundation ✅ COMPLETE

### Database
- [x] Add to `models.py`: Transaction, Budget, Debt, RecurringTransaction, ExchangeRate
- [x] Extend User model: primary_currency, currency_settings
- [x] Create migration: `20251223_000001_adult_finance.py`
- [x] Run migration

### Repositories
- [x] `server/repositories/transactions.py`
- [x] `server/repositories/budgets.py`
- [x] `server/repositories/debts.py`
- [x] `server/repositories/recurring_transactions.py`
- [x] `server/repositories/exchange_rates.py`
- [x] Update `server/repositories/__init__.py`

### Services
- [x] `server/services/v2/currency_service.py`
- [x] `server/services/v2/adult_finance_service.py`
- [x] Update `server/services/v2/__init__.py`

---

## Phase 2: Agent Tools ✅ COMPLETE

### Query Builder
- [x] `server/agents/execution_agent/tools/adult/query_builder.py`

### Adult Finance Tools
- [x] `server/agents/execution_agent/tools/adult/finance.py`
  - [x] `record_transaction` tool
  - [x] `delete_transaction` tool
  - [x] `query_finances` tool
  - [x] `get_financial_summary` tool
  - [x] `get_dashboard` tool
  - [x] `manage_budget` tool
  - [x] `manage_debt` tool
  - [x] `manage_recurring` tool
- [x] Update `server/agents/execution_agent/tools/adult/__init__.py`
- [x] Update `server/agents/execution_agent/tools/registry.py`

### Persona
- [x] `server/agents/interaction_agent/poke_system_prompt.md`
- [x] Update agent.py to load correct prompt by user_type

---

## Phase 3: Integration ✅ COMPLETE

### Chat Handler
- [x] Update `chat_handler.py` to create adult finance services
- [x] Update `UserContext` with adult_finance_service
- [x] Update `execution_agent/runtime.py` to pass adult_finance_service

### API Routes (optional - if needed for frontend)
- [ ] `server/routes/v2/adult_finance.py` (skipped - using chat interface)
- [ ] Update `server/routes/v2/__init__.py`
- [ ] Update `server/routes/__init__.py`

---

## Phase 4: Insights ✅ COMPLETE

- [x] `server/services/v2/insights_service.py`
  - [x] Post-transaction insights
  - [x] Daily summary
  - [x] Weekly summary
  - [x] Monthly summary
  - [x] Pattern detection
- [x] `get_insights` tool in `server/agents/execution_agent/tools/adult/finance.py`
- [x] Updated `registry.py` to pass insights_service
- [x] Updated `runtime.py` to create InsightsService for adults

---

## Phase 5: Cleanup

- [ ] Remove `server/agents/execution_agent/tools/adult/productivity.py` (can keep as placeholder)
- [ ] Remove unused OAuth sync for adults
- [x] Test adult flow imports
- [ ] Test kid flow still works
- [ ] Test adult flow end-to-end with real user

---

## Verified Working

- [x] Adult tool schemas load correctly (10 tools with insights)
- [x] Child tool schemas load correctly (12 tools)
- [x] Poke system prompt loads for adult users
- [x] Wally system prompt loads for child users
- [x] All Python syntax valid
- [x] Server app imports successfully
- [x] InsightsService integrated with execution agent runtime
- [x] Database session concurrency fixed (separate sessions for execution agents)

---

## File Structure After Implementation

```
server/
├── database/
│   └── models.py                         # +5 new models ✅
├── repositories/
│   ├── __init__.py                       # Updated exports ✅
│   ├── transactions.py                   # NEW ✅
│   ├── budgets.py                        # NEW ✅
│   ├── debts.py                          # NEW ✅
│   ├── recurring_transactions.py         # NEW ✅
│   └── exchange_rates.py                 # NEW ✅
├── services/
│   ├── v2/
│   │   ├── __init__.py                   # Updated exports ✅
│   │   ├── adult_finance_service.py      # NEW ✅
│   │   ├── currency_service.py           # NEW ✅
│   │   └── insights_service.py           # NEW ✅ (Phase 4)
│   ├── execution/
│   │   └── user_context.py               # Updated ✅
│   └── conversation/
│       └── chat_handler.py               # Updated ✅
├── agents/
│   ├── interaction_agent/
│   │   ├── poke_system_prompt.md         # NEW ✅
│   │   └── agent.py                      # Updated ✅
│   └── execution_agent/
│       ├── runtime.py                    # Updated ✅
│       └── tools/
│           ├── registry.py               # Updated ✅
│           └── adult/
│               ├── __init__.py           # Updated ✅
│               ├── finance.py            # NEW ✅
│               └── query_builder.py      # NEW ✅
└── migrations/versions/
    └── 20251223_000001_adult_finance.py  # Created earlier ✅
```
