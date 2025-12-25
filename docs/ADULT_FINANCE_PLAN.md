# Adult Finance (Poke) - Implementation Plan

## Status: IMPLEMENTED

This plan has been fully implemented. See `ADULT_FINANCE_CHECKLIST.md` for completion status.

---

## Overview

OpenPoke is a witty, intelligent personal finance assistant for adults. Poke is a "financially-savvy friend who tracks your money, celebrates your wins, and isn't afraid to call out that 5th Uber Eats order this week."

**Note**: This is now an adults-only application. Kids/Wally Junior code has been removed and will be a separate backend.

---

## Architecture Principles

- **DRY**: Reuse existing infrastructure where possible (repositories, services pattern)
- **Security first**: User data isolation enforced at query level, not just API level
- **Flexible queries**: Structured intent system, not raw SQL
- **Multi-currency**: Store original + converted amounts

---

## Database Models

**Location**: `server/database/models.py`

```
Transaction (unified model for all transactions)
├── id (BigInt, PK)
├── user_id (UUID, FK)
├── type: expense | income | transfer
├── amount (BigInt, cents)
├── currency (String, 3-char ISO code)
├── amount_primary (BigInt, converted to user's primary currency)
├── exchange_rate (Decimal, rate at transaction time)
├── category (String)
├── description (Text)
├── counterparty (String, optional - who paid/received)
├── transaction_date (DateTime)
├── is_recurring (Boolean)
├── recurring_id (FK to RecurringTransaction, optional)
├── tags (JSONB, array of strings)
├── created_at, updated_at
└── Index: (user_id, transaction_date), (user_id, type, category)

Budget
├── id (BigInt, PK)
├── user_id (UUID, FK)
├── category (String)
├── monthly_limit (BigInt, cents in primary currency)
├── alert_threshold (Int, percentage 0-100)
├── is_active (Boolean)
├── created_at, updated_at
└── Unique: (user_id, category)

Debt
├── id (BigInt, PK)
├── user_id (UUID, FK)
├── counterparty_name (String)
├── type: lent | borrowed
├── original_amount (BigInt)
├── remaining_amount (BigInt)
├── currency (String)
├── due_date (Date, optional)
├── status: active | paid | forgiven
├── notes (Text)
├── created_at, updated_at
└── Index: (user_id, status)

RecurringTransaction
├── id (BigInt, PK)
├── user_id (UUID, FK)
├── template (JSONB - transaction details)
├── frequency: daily | weekly | biweekly | monthly | yearly
├── next_due_date (Date)
├── last_processed_date (Date)
├── reminder_days_before (Int, optional)
├── is_active (Boolean)
├── created_at
└── Index: (user_id, is_active, next_due_date)

ExchangeRate (shared table)
├── id (BigInt, PK)
├── from_currency (String)
├── to_currency (String)
├── rate (Decimal)
├── date (Date)
└── Unique: (from_currency, to_currency, date)

User (extended)
├── ... existing fields ...
├── primary_currency (String, default "UZS")
└── currency_settings (JSONB: {display_currencies: [], auto_convert: bool})
```

---

## Secure Query Builder

**Location**: `server/agents/execution_agent/tools/adult/query_builder.py`

Design:
- AI provides structured intent (not raw SQL)
- Query builder validates and constructs safe queries
- `user_id` filter ALWAYS injected - cannot be bypassed
- Whitelist of allowed operations, tables, filters

```python
class FinanceQueryBuilder:
    ALLOWED_OPERATIONS = ["list", "sum", "average", "count", "compare", "trend"]
    ALLOWED_TABLES = ["transactions", "budgets", "debts"]

    def __init__(self, user_id: UUID):
        self.user_id = user_id  # Always enforced

    def build_query(self, intent: StructuredQuery) -> SQLAlchemy Query
```

---

## Finance Tools

| Tool | Purpose |
|------|---------|
| `record_transaction` | Add/edit/delete any transaction (expense, income, transfer) |
| `delete_transaction` | Remove a transaction by ID |
| `query_finances` | Flexible queries with structured filters |
| `get_financial_summary` | Overview of finances |
| `get_dashboard` | Quick stats view |
| `manage_budget` | Set, view, delete budgets per category |
| `manage_debt` | Track lent/borrowed money |
| `manage_recurring` | Subscriptions and regular income |
| `get_insights` | Request summaries and pattern analysis |

---

## Insights Engine

**Location**: `server/services/v2/insights_service.py`

### Triggers
| Trigger | When | Content |
|---------|------|---------|
| Post-transaction | After any add/edit | Quick insight ("3rd coffee this week") |
| Daily summary | Evening (configurable) | Day's totals + notable patterns |
| Weekly summary | Sunday evening | Week review + budget status |
| Monthly summary | 1st of month | Full report + trends + goal progress |

### Pattern Detection
- Unusual spending spikes
- Recurring patterns (daily coffee)
- Budget limit approaching
- Subscription creep (increasing recurring costs)
- Income vs expense ratio alerts

---

## Multi-Currency Support

### Design
1. User sets `primary_currency` (default: UZS)
2. Transactions store:
   - `amount` + `currency` (original)
   - `amount_primary` + `exchange_rate` (converted)
3. All aggregations use `amount_primary` for consistency
4. Display can show multiple currencies

### Exchange Rate Source
- Currently: Manual rates table, updated periodically
- Future: API integration (exchangerate-api.com or similar)

**Location**: `server/services/v2/currency_service.py`

---

## Poke Persona

**Location**: `server/agents/interaction_agent/poke_system_prompt.md`

Personality traits:
- Witty and perceptive
- Like a financially-savvy friend
- Celebrates wins genuinely
- Calls out patterns without being preachy
- Uses humor appropriately
- Gives context (e.g., "that $50/month is $600/year")

Example responses:
- "Third Uber Eats this week - meal prep Sunday didn't happen, huh?"
- "Nice! You spent 20% less on food than last month. Your wallet thanks you."
- "You've got 3 streaming subscriptions totaling $45/month. Using all of them?"

---

## Security Checklist

- [x] `user_id` filter enforced at repository level
- [x] Query builder validates all input
- [x] No raw SQL from AI
- [x] Read-only operations only for queries
- [x] Input validation on all parameters
- [x] Currency codes validated against whitelist

---

## Future Enhancements

- [ ] REST API endpoints for frontend dashboard
- [ ] Scheduled recurring transaction processing
- [ ] Exchange rate API integration
- [ ] Adult achievements/milestones system
- [ ] Budget templates (50/30/20 rule)
- [ ] Receipt/invoice attachment support
