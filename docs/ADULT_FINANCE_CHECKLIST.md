# Adult Finance Implementation Checklist

## Phase 1: Foundation

### Database
- [ ] Add to `models.py`: Transaction, Budget, Debt, RecurringTransaction, ExchangeRate
- [ ] Extend User model: primary_currency, currency_settings
- [ ] Create migration: `20251223_adult_finance.py`
- [ ] Run migration

### Repositories
- [ ] `server/repositories/transactions.py`
- [ ] `server/repositories/budgets.py`
- [ ] `server/repositories/debts.py`
- [ ] `server/repositories/recurring_transactions.py`
- [ ] `server/repositories/exchange_rates.py`
- [ ] Update `server/repositories/__init__.py`

### Services
- [ ] `server/services/v2/currency_service.py`
- [ ] `server/services/v2/adult_finance_service.py`
- [ ] Update `server/services/v2/__init__.py`

---

## Phase 2: Agent Tools

### Query Builder
- [ ] `server/agents/execution_agent/tools/adult/query_builder.py`

### Adult Finance Tools
- [ ] `server/agents/execution_agent/tools/adult/finance.py`
  - [ ] `record_transaction` tool
  - [ ] `query_finances` tool
  - [ ] `manage_budget` tool
  - [ ] `manage_debt` tool
  - [ ] `manage_recurring` tool
  - [ ] `get_insights` tool
- [ ] Update `server/agents/execution_agent/tools/adult/__init__.py`
- [ ] Update `server/agents/execution_agent/tools/registry.py`

### Persona
- [ ] `server/agents/interaction_agent/poke_system_prompt.md`
- [ ] Update agent.py to load correct prompt by user_type

---

## Phase 3: Integration

### Chat Handler
- [ ] Update `chat_handler.py` to create adult finance services
- [ ] Update `UserContext` with adult services

### API Routes (optional - if needed for frontend)
- [ ] `server/routes/v2/adult_finance.py`
- [ ] Update `server/routes/v2/__init__.py`
- [ ] Update `server/routes/__init__.py`

---

## Phase 4: Insights

- [ ] `server/services/v2/insights_service.py`
  - [ ] Post-transaction insights
  - [ ] Daily summary
  - [ ] Weekly summary
  - [ ] Monthly summary
  - [ ] Pattern detection

---

## Phase 5: Cleanup

- [ ] Remove `server/agents/execution_agent/tools/adult/productivity.py`
- [ ] Remove OAuth sync for adults (no longer needed)
- [ ] Test adult flow end-to-end
- [ ] Test kid flow still works

---

## File Structure After Implementation

```
server/
├── database/
│   └── models.py                         # +5 new models
├── repositories/
│   ├── __init__.py                       # Updated exports
│   ├── transactions.py                   # NEW
│   ├── budgets.py                        # NEW
│   ├── debts.py                          # NEW
│   ├── recurring_transactions.py         # NEW
│   └── exchange_rates.py                 # NEW
├── services/v2/
│   ├── __init__.py                       # Updated exports
│   ├── adult_finance_service.py          # NEW
│   ├── currency_service.py               # NEW
│   └── insights_service.py               # NEW
├── agents/
│   ├── interaction_agent/
│   │   ├── poke_system_prompt.md         # NEW
│   │   └── agent.py                      # Updated
│   └── execution_agent/tools/
│       ├── registry.py                   # Updated
│       └── adult/
│           ├── __init__.py               # Updated
│           ├── finance.py                # NEW (replaces productivity.py)
│           └── query_builder.py          # NEW
└── migrations/versions/
    └── 20251223_adult_finance.py         # NEW
```
