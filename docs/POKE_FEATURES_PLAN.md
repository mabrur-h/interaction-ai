# Poke Finance App - Feature Roadmap

## Overview

This document outlines the planned features for Poke, the adult personal finance chatbot. Features are prioritized by user value and implementation complexity.

---

## Priority 1: Currency Management

### Goal
Allow users to manage their primary currency, view/set exchange rates, and control display preferences.

### Current State
| Component | Status |
|-----------|--------|
| `User.primary_currency` | ✅ Exists (default: UZS) |
| `User.currency_settings` | ✅ Exists (JSONB) |
| `ExchangeRate` model | ✅ Exists |
| `CurrencyService` | ✅ Exists (convert, format, get_rate) |
| `manage_currency` tool | ❌ Missing |

### Supported Currencies
- UZS (Uzbek so'm) - default
- USD (US Dollar)
- EUR (Euro)
- RUB (Russian Ruble)
- GBP (British Pound)

### Tool Design: `manage_currency`

```json
{
  "name": "manage_currency",
  "description": "Manage currency settings - change primary currency, view/set exchange rates, see available currencies.",
  "parameters": {
    "action": {
      "enum": ["get_settings", "set_primary", "get_rates", "set_rate", "list_currencies"],
      "description": "What to do"
    },
    "currency": {
      "type": "string",
      "enum": ["UZS", "USD", "EUR", "RUB", "GBP"],
      "description": "Currency code for set_primary or set_rate"
    },
    "rate": {
      "type": "number",
      "description": "Exchange rate value (for set_rate: how much 1 unit of this currency = in UZS)"
    },
    "auto_convert": {
      "type": "boolean",
      "description": "Auto-convert foreign transactions to primary currency"
    }
  }
}
```

### Actions

| Action | Description | Example |
|--------|-------------|---------|
| `get_settings` | View current currency settings | "What's my currency?" |
| `set_primary` | Change primary currency | "Change my currency to USD" |
| `get_rates` | View all exchange rates | "Show me exchange rates" |
| `set_rate` | Set/update an exchange rate | "Set dollar rate to 12,800" |
| `list_currencies` | List supported currencies | "What currencies do you support?" |

### Implementation Steps

1. **Add tool schema** to `finance.py`
2. **Create `_manage_currency` function**:
   - `get_settings`: Return user's primary_currency and currency_settings
   - `set_primary`: Update User.primary_currency, handle existing transaction display
   - `get_rates`: Query ExchangeRate table for all rates to/from primary currency
   - `set_rate`: Upsert exchange rate (bidirectional)
   - `list_currencies`: Return SUPPORTED_CURRENCIES with symbols
3. **Add to registry**
4. **Update Poke system prompt** with currency tool

### User Experience Examples

```
User: "change my currency to dollars"
Poke: "Switched to USD. Your transactions will now show in dollars. Previous UZS amounts converted at 1 USD = 12,600 so'm."

User: "what's the dollar rate?"
Poke: "1 USD = 12,600 UZS. Last updated yesterday."

User: "set euro to 13500"
Poke: "Updated. 1 EUR = 13,500 UZS now."
```

### Files to Modify
| File | Changes |
|------|---------|
| `server/agents/execution_agent/tools/adult/finance.py` | Add manage_currency schema + function |
| `server/services/v2/adult_finance_service.py` | Add currency management methods |
| `server/agents/interaction_agent/poke_system_prompt.md` | Add currency tool docs |

---

## Priority 2: Savings Goals

### Goal
Let users set savings targets (e.g., "Save $1000 for vacation by June") and track progress.

### Database Schema

```sql
CREATE TABLE savings_goals (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,           -- "Vacation fund", "Emergency fund"
    target_amount BIGINT NOT NULL,         -- Target in cents
    current_amount BIGINT DEFAULT 0,       -- Saved so far
    currency VARCHAR(3) NOT NULL,
    target_date DATE,                       -- Optional deadline
    priority INTEGER DEFAULT 1,             -- For multiple goals
    status VARCHAR(20) DEFAULT 'active',    -- active, completed, paused, cancelled
    auto_allocate_percent INTEGER,          -- Auto-save % of income
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    UNIQUE(user_id, name)
);

CREATE TABLE savings_contributions (
    id BIGSERIAL PRIMARY KEY,
    goal_id BIGINT REFERENCES savings_goals(id) ON DELETE CASCADE,
    amount BIGINT NOT NULL,
    source VARCHAR(50),                     -- 'manual', 'auto_income', 'transfer'
    transaction_id BIGINT REFERENCES transactions(id),
    contributed_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT
);
```

### Tool Design: `manage_savings_goal`

```json
{
  "name": "manage_savings_goal",
  "description": "Create and track savings goals. Set targets, add money, check progress.",
  "parameters": {
    "action": {
      "enum": ["create", "add_money", "withdraw", "list", "get_progress", "update", "complete", "delete"],
      "description": "What to do"
    },
    "name": {
      "type": "string",
      "description": "Goal name (e.g., 'vacation', 'emergency fund', 'new phone')"
    },
    "amount": {
      "type": "integer",
      "description": "Amount in cents"
    },
    "target_amount": {
      "type": "integer",
      "description": "Target amount for create/update"
    },
    "target_date": {
      "type": "string",
      "description": "ISO date for deadline"
    },
    "auto_allocate_percent": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "description": "Auto-allocate this % of each income to this goal"
    }
  }
}
```

### Features

1. **Create goals** with optional deadlines
2. **Add/withdraw money** from goals
3. **Auto-allocate** from income (e.g., "Save 10% of every paycheck")
4. **Progress tracking** with projections
5. **Multiple goals** with priorities
6. **Celebration** when goals are reached

### User Experience Examples

```
User: "I want to save 5 million for a vacation"
Poke: "Vacation goal created: 0 / 5,000,000 so'm. When's the trip?"

User: "put 200k towards vacation"
Poke: "Added 200k. Vacation fund: 200,000 / 5,000,000 so'm (4%). 4.8M to go."

User: "auto save 10% of my salary"
Poke: "Done. 10% of every income goes to vacation. At current rate, you'll hit the goal in ~8 months."

User: "how are my savings going?"
Poke: "Vacation: 1.2M / 5M (24%) - on track for June
       Emergency: 800k / 3M (27%) - ahead of schedule"
```

### Implementation Steps

1. Create database migration
2. Create `SavingsGoalRepository`
3. Add methods to `AdultFinanceService`
4. Create tool schema and handler
5. Hook into `record_transaction` for auto-allocation on income
6. Update system prompt

---

## Priority 3: Loan/Credit Tracking

### Goal
Track loans with interest calculations - both money borrowed AND money lent with interest.

### Difference from Current Debts
Current `manage_debt` tracks simple IOUs. This adds:
- Interest rates (APR)
- Payment schedules
- Amortization
- Interest accrued tracking
- Payoff projections

### Database Schema

```sql
CREATE TABLE loans (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,            -- "Car loan", "Bank credit"
    loan_type VARCHAR(20) NOT NULL,        -- 'borrowed', 'lent'
    principal_amount BIGINT NOT NULL,       -- Original amount
    current_balance BIGINT NOT NULL,        -- Remaining balance
    interest_rate NUMERIC(5,2),             -- Annual rate (e.g., 24.00 for 24%)
    interest_type VARCHAR(20) DEFAULT 'simple',  -- 'simple', 'compound'
    currency VARCHAR(3) NOT NULL,
    counterparty VARCHAR(100),              -- Bank name, person, etc.
    start_date DATE NOT NULL,
    end_date DATE,                          -- Expected payoff date
    payment_frequency VARCHAR(20),          -- 'monthly', 'weekly', 'custom'
    minimum_payment BIGINT,                 -- Required monthly payment
    total_interest_paid BIGINT DEFAULT 0,
    total_interest_earned BIGINT DEFAULT 0, -- For lent money
    status VARCHAR(20) DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE loan_payments (
    id BIGSERIAL PRIMARY KEY,
    loan_id BIGINT REFERENCES loans(id) ON DELETE CASCADE,
    amount BIGINT NOT NULL,
    principal_portion BIGINT,               -- How much went to principal
    interest_portion BIGINT,                -- How much went to interest
    payment_date DATE NOT NULL,
    transaction_id BIGINT REFERENCES transactions(id),
    notes TEXT
);
```

### Tool Design: `manage_loan`

```json
{
  "name": "manage_loan",
  "description": "Track loans with interest - both borrowed and lent money. Calculate payoffs, track payments.",
  "parameters": {
    "action": {
      "enum": ["add", "make_payment", "receive_payment", "list", "get_details", "calculate_payoff", "update", "close"],
      "description": "What to do"
    },
    "loan_type": {
      "enum": ["borrowed", "lent"],
      "description": "Did you borrow or lend this money?"
    },
    "name": {
      "type": "string",
      "description": "Loan name (e.g., 'Car loan', 'Bank credit', 'Loan to Akmal')"
    },
    "amount": {
      "type": "integer",
      "description": "Principal amount or payment amount"
    },
    "interest_rate": {
      "type": "number",
      "description": "Annual interest rate as percentage (e.g., 24 for 24%)"
    },
    "counterparty": {
      "type": "string",
      "description": "Who you borrowed from or lent to"
    },
    "end_date": {
      "type": "string",
      "description": "Expected payoff date (ISO format)"
    },
    "loan_id": {
      "type": "integer",
      "description": "Loan ID for payments/updates"
    }
  }
}
```

### Features

1. **Track borrowed money** with interest accrual
2. **Track lent money** with interest earnings
3. **Payment breakdown** (principal vs interest)
4. **Payoff calculator** ("What if I pay extra?")
5. **Amortization schedule**
6. **Payment reminders** (integrates with recurring)
7. **Interest accrual alerts**

### User Experience Examples

```
User: "I took a 10 million loan from the bank at 24% annual"
Poke: "Ouch, 24%. Added bank loan: 10M so'm. Monthly interest: ~200k. Want me to set up payment reminders?"

User: "paid 500k on the bank loan"
Poke: "Payment recorded. 200k went to interest, 300k to principal. Balance: 9.7M. At this rate, 28 months to payoff."

User: "how much interest have I paid total?"
Poke: "You've paid 1.2M in interest so far on your bank loan. The original debt was 10M - you've given them 12% extra already."

User: "I lent Jamshid 2 million at 5% monthly"
Poke: "Logged. Jamshid owes you 2M + 100k/month interest. He's costing himself 60% annually. Good friend."
```

---

## Priority 4: Spending Streaks & Challenges

### Goal
Gamify financial habits with streaks, challenges, and achievements to drive engagement.

### Features

#### 4.1 Spending Streaks
Track consecutive days/weeks of good behavior:
- **No-spend streak**: Days without discretionary spending
- **Under-budget streak**: Weeks staying under budget
- **Savings streak**: Consecutive deposits to savings goals
- **Logging streak**: Days you logged at least one transaction

#### 4.2 Challenges
Time-boxed goals with rewards:
- **No eating out for a week**
- **Spend under X this month**
- **Save X amount in 30 days**
- **Track every expense for 7 days**

#### 4.3 Achievements/Badges
Milestone celebrations:
- First transaction logged
- First budget set
- 7-day logging streak
- Paid off a debt
- Reached a savings goal
- 30 days under budget

### Database Schema

```sql
CREATE TABLE user_streaks (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    streak_type VARCHAR(50) NOT NULL,       -- 'logging', 'no_spend', 'under_budget', 'savings'
    current_count INTEGER DEFAULT 0,
    best_count INTEGER DEFAULT 0,
    last_activity_date DATE,
    started_at DATE,
    broken_at DATE,
    UNIQUE(user_id, streak_type)
);

CREATE TABLE challenges (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    challenge_type VARCHAR(50) NOT NULL,    -- 'no_spend_category', 'budget_limit', 'save_amount', 'log_daily'
    target_value BIGINT,                    -- Amount or count
    target_category VARCHAR(100),           -- For category-specific challenges
    current_progress BIGINT DEFAULT 0,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',    -- active, completed, failed, abandoned
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE achievements (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    achievement_type VARCHAR(100) NOT NULL,
    earned_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,                         -- Extra data about how it was earned
    UNIQUE(user_id, achievement_type)
);
```

### Tool Design: `manage_challenges`

```json
{
  "name": "manage_challenges",
  "description": "Create challenges, check streaks, view achievements. Gamify your finances!",
  "parameters": {
    "action": {
      "enum": ["start_challenge", "check_progress", "list_active", "view_streaks", "view_achievements", "abandon_challenge"],
      "description": "What to do"
    },
    "challenge_type": {
      "enum": ["no_spend", "budget_limit", "save_amount", "log_daily", "category_limit"],
      "description": "Type of challenge"
    },
    "target_value": {
      "type": "integer",
      "description": "Target amount or count"
    },
    "category": {
      "type": "string",
      "description": "Category for category-specific challenges"
    },
    "duration_days": {
      "type": "integer",
      "minimum": 1,
      "maximum": 90,
      "description": "Challenge duration in days"
    }
  }
}
```

### User Experience Examples

```
User: "I want to stop eating out"
Poke: "Challenge accepted. No restaurant spending for 7 days. Current streak: 0 days. I'll be watching."

User: [3 days later] "lunch 25k restaurant"
Poke: "25k logged. RIP your no-restaurant challenge. 3 days was a good run though. Try again?"

User: "how's my streak?"
Poke: "Logging streak: 12 days (personal best!)
       Under-budget: 3 weeks straight
       No-spend: 0 (you bought coffee 2 hours ago)"

User: "what badges do I have?"
Poke: "You've earned:
       🎯 First Transaction
       📊 Budget Boss (set 3+ budgets)
       🔥 Week Warrior (7-day logging streak)
       💰 Debt Destroyer (paid off 1 debt)"
```

---

## Priority 5: Engagement & Retention Features

### 5.1 Daily/Weekly Digest
Automated summaries at user-preferred times:
- Morning: "Today's budget remaining: X. Upcoming bills: Y."
- Evening: "You spent X today. Big one was Z."
- Weekly: "This week: spent X, earned Y, saved Z. Category breakdown..."

### 5.2 Smart Observations
Proactive insights pushed to users:
- "You've spent 50% more on food this week vs last"
- "3 subscriptions renewing next week. Total: X"
- "You're 80% through your shopping budget with 10 days left"
- "Coffee spending: 15 this month. That's 450k. Just saying."

### 5.3 Milestones & Celebrations
Acknowledge positive moments:
- "First month tracking! You logged 47 transactions."
- "Net worth increased by 500k this month!"
- "Biggest savings month ever: 2M saved!"
- "Paid off your loan to Bekzod. Freedom feels good."

### 5.4 Personality Evolution
Poke's tone adapts to user behavior:
- **New users**: More helpful, less roasty
- **Regular loggers**: More conversational
- **Struggling users**: Supportive, constructive
- **Winning users**: Celebratory but pushing for more

### 5.5 Social Features (Future)
- Share achievements (opt-in)
- Anonymous spending comparisons ("You spend 20% less on food than average")
- Challenge friends
- Leaderboards

---

## Implementation Order

### Phase 1: Currency Management (This Week)
1. Add `manage_currency` tool
2. Implement all actions
3. Update system prompt
4. Test currency switching

### Phase 2: Savings Goals (Week 2)
1. Database migration
2. Repository + Service
3. Tool implementation
4. Auto-allocation hook
5. Progress tracking

### Phase 3: Loan Tracking (Week 3)
1. Database migration
2. Interest calculation logic
3. Tool implementation
4. Payment tracking
5. Payoff projections

### Phase 4: Gamification (Week 4)
1. Streaks infrastructure
2. Challenge system
3. Achievements
4. Hook into transactions

### Phase 5: Engagement (Week 5+)
1. Digest system
2. Smart observations
3. Milestone tracking
4. Notification preferences

---

## Success Metrics

| Feature | Key Metric | Target |
|---------|------------|--------|
| Currency | Users changing currency | 20%+ |
| Savings | Goals created | 1+ per active user |
| Loans | Loans tracked | 30%+ of users |
| Streaks | 7+ day logging streaks | 50%+ retention |
| Challenges | Challenges completed | 60%+ completion |
| Engagement | Daily active users | 40%+ of registered |

---

## Technical Notes

### Consistency
- All amounts stored in cents (BIGINT)
- All currencies use ISO 4217 codes
- All dates in UTC, convert for display
- User's timezone respected for streaks/daily resets

### Performance
- Index on user_id for all user-scoped tables
- Cache exchange rates (15 min TTL)
- Batch streak updates (not on every transaction)

### Error Handling
- Graceful degradation if external APIs fail
- Default rates for currency conversion
- Don't break transactions if gamification fails
