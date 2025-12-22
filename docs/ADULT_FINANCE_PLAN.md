# Adult Finance (Poke) - Implementation Plan

## Overview

Transform OpenPoke into a witty, intelligent personal finance assistant for adults. Poke is a "financially-savvy friend who tracks your money, celebrates your wins, and isn't afraid to call out that 5th Uber Eats order this week."

## Architecture Principles

- **DRY**: Reuse existing infrastructure where possible (repositories, services pattern)
- **Clean separation**: Adults and kids have separate tools, prompts, and some models
- **Security first**: User data isolation enforced at query level, not just API level
- **Flexible queries**: Structured intent system, not raw SQL
- **Multi-currency**: Store original + converted amounts

---

## Phase 1: Foundation (Database + Basic CRUD)

### New Database Models

**Location**: `server/database/models.py`

```
Transaction (NEW - unified model for adults)
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

Budget (NEW)
├── id (BigInt, PK)
├── user_id (UUID, FK)
├── category (String)
├── monthly_limit (BigInt, cents in primary currency)
├── alert_threshold (Int, percentage 0-100)
├── is_active (Boolean)
├── created_at, updated_at
└── Unique: (user_id, category)

Debt (NEW)
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

RecurringTransaction (NEW)
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

ExchangeRate (NEW - shared table)
├── id (BigInt, PK)
├── from_currency (String)
├── to_currency (String)
├── rate (Decimal)
├── date (Date)
└── Unique: (from_currency, to_currency, date)
```

**User model additions** (extend existing):
```
User (MODIFY)
├── ... existing fields ...
├── primary_currency (String, default "UZS")
└── currency_settings (JSONB: {display_currencies: [], auto_convert: bool})
```

### File Structure

```
server/
├── database/
│   └── models.py                    # Add new models
├── repositories/
│   ├── transactions.py              # NEW
│   ├── budgets.py                   # NEW
│   ├── debts.py                     # NEW
│   ├── recurring_transactions.py    # NEW
│   └── exchange_rates.py            # NEW
├── services/
│   └── v2/
│       ├── adult_finance_service.py # NEW - main service
│       └── currency_service.py      # NEW - conversion logic
├── agents/
│   └── execution_agent/
│       └── tools/
│           └── adult/
│               ├── __init__.py
│               ├── finance.py       # NEW - replace productivity.py
│               └── query_builder.py # NEW - safe query construction
└── migrations/
    └── versions/
        └── 20251223_adult_finance.py # NEW
```

---

## Phase 2: Query System

### Secure Query Builder

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

    def build_query(self, intent: StructuredQuery) -> SQLAlchemy Query:
        # Validate, construct, return safe query
```

### Structured Query Schema

```python
StructuredQuery:
    operation: list | sum | average | count | compare | trend
    transaction_type: expense | income | all (optional)
    date_range: today | this_week | this_month | last_30_days | custom
    custom_start: ISO date (if custom)
    custom_end: ISO date (if custom)
    categories: list[str] (optional)
    amount_min: int (optional)
    amount_max: int (optional)
    search_text: str (optional)
    group_by: category | day | week | month | counterparty (optional)
    compare_to: previous_period | same_last_year (optional)
    limit: int (default 20)
```

---

## Phase 3: Budgets

### Features
- Set monthly limits per category
- Track spending against limits
- Alert when approaching threshold (e.g., 80%)
- 50/30/20 budget template option

### Tool Schema
```python
{
    "name": "manage_budget",
    "parameters": {
        "action": "set | get | delete | suggest_50_30_20",
        "category": "string (for set/delete)",
        "monthly_limit": "number (for set)",
        "alert_threshold": "number 0-100 (optional)"
    }
}
```

---

## Phase 4: Insights Engine

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

### Implementation
**Location**: `server/services/v2/insights_service.py`

```python
class InsightsService:
    async def generate_post_transaction_insight(self, txn: Transaction) -> str
    async def generate_daily_summary(self, user_id: UUID) -> DailySummary
    async def generate_weekly_summary(self, user_id: UUID) -> WeeklySummary
    async def generate_monthly_summary(self, user_id: UUID) -> MonthlySummary
    async def detect_patterns(self, user_id: UUID) -> list[Pattern]
```

---

## Phase 5: Debts

### Features
- Track money lent to others
- Track money borrowed from others
- Payment recording
- Due date reminders
- Settlement tracking

### Tool Schema
```python
{
    "name": "manage_debt",
    "parameters": {
        "action": "add | record_payment | list | forgive | get_summary",
        "type": "lent | borrowed (for add)",
        "counterparty": "string",
        "amount": "number",
        "due_date": "ISO date (optional)",
        "notes": "string (optional)"
    }
}
```

---

## Phase 6: Recurring Transactions

### Features
- Track subscriptions (Netflix, Spotify, etc.)
- Track regular income (salary)
- Automatic transaction creation on due date
- Reminders before due dates
- Total monthly recurring cost view

### Tool Schema
```python
{
    "name": "manage_recurring",
    "parameters": {
        "action": "add | list | pause | delete | get_total",
        "template": {
            "type": "expense | income",
            "amount": "number",
            "category": "string",
            "description": "string",
            "counterparty": "string (optional)"
        },
        "frequency": "daily | weekly | biweekly | monthly | yearly",
        "start_date": "ISO date",
        "reminder_days": "number (optional)"
    }
}
```

---

## Phase 7: Adult Achievements

Different from kids - focus on financial health milestones.

### Achievement Types
| Type | Name | Description |
|------|------|-------------|
| `first_transaction` | Getting Started | Log your first transaction |
| `week_tracking` | Consistent Tracker | Log transactions for 7 days straight |
| `month_tracking` | Monthly Master | Track a full month of transactions |
| `budget_set` | Budget Builder | Set your first budget |
| `budget_under` | Budget Boss | Stay under budget for a month |
| `savings_goal` | Goal Setter | Create a savings goal |
| `goal_reached` | Goal Crusher | Complete a savings goal |
| `debt_paid` | Debt Free | Pay off a debt completely |
| `savings_rate_20` | Smart Saver | Achieve 20% savings rate |
| `savings_rate_50` | Super Saver | Achieve 50% savings rate |

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
- Initially: Manual rates table, updated periodically
- Future: API integration (exchangerate-api.com or similar)

**Location**: `server/services/v2/currency_service.py`

```python
class CurrencyService:
    async def convert(self, amount: int, from_curr: str, to_curr: str) -> tuple[int, Decimal]
    async def get_rate(self, from_curr: str, to_curr: str, date: date) -> Decimal
    async def update_rates(self) -> None  # Scheduled job
```

---

## Adult Tools Summary

| Tool | Purpose |
|------|---------|
| `record_transaction` | Add/edit/delete any transaction (expense, income, transfer) |
| `query_finances` | Flexible queries with structured filters |
| `manage_budget` | Set, view, delete budgets per category |
| `manage_debt` | Track lent/borrowed money |
| `manage_recurring` | Subscriptions and regular income |
| `get_insights` | Request summaries and pattern analysis |
| `manage_goals` | Savings goals (reuse from kids with modifications) |

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

## Implementation Order

1. **Database models + migration** - Foundation
2. **Repositories** - Data access layer
3. **Currency service** - Multi-currency support
4. **Adult finance service** - Core business logic
5. **Query builder** - Safe, flexible queries
6. **Adult finance tools** - Agent integration
7. **Poke system prompt** - Persona definition
8. **Chat handler update** - Enable for adults
9. **Insights service** - Pattern detection + summaries
10. **API routes** - REST endpoints for frontend

---

## Security Checklist

- [ ] `user_id` filter enforced at repository level
- [ ] Query builder validates all input
- [ ] No raw SQL from AI
- [ ] Read-only operations only for queries
- [ ] Rate limiting on API endpoints
- [ ] Input validation on all parameters
- [ ] Currency codes validated against whitelist

---

## Notes

- Keep existing `Expense` and `SavingsGoal` tables for kids
- Adults use new `Transaction` table - cleaner separation
- Reuse achievement infrastructure with different definitions
- Frontend updates planned separately
