# Kids (Wally Junior) Code Removal Plan

This document outlines all kids/Wally-related code that needs to be removed to make OpenPoke an adults-only backend. The kids app will be created as a separate application later.

## Overview

- **Total Files to Remove:** ~50 files
- **Backend files:** ~16 files
- **Frontend files:** ~34 files
- **Database models to remove:** 5 models
- **Migration cleanup needed:** Yes

---

## Phase 1: Backend Cleanup

### 1.1 Agent Tools (Remove entire `kids/` folder)
```
server/agents/execution_agent/tools/kids/
├── __init__.py
├── finance.py
└── achievements.py
```

**Action:** Delete entire `tools/kids/` directory

### 1.2 Update Tool Registry
**File:** `server/agents/execution_agent/tools/registry.py`

**Action:** Remove child branch from `get_tool_schemas()` and `get_tool_registry()`
- Remove imports for `from .kids import finance, achievements`
- Remove `if user_type == "child":` branch
- Remove `finance_service` and `achievements_service` parameters

### 1.3 Repositories (Delete)
```
server/repositories/
├── expenses.py           # DELETE
├── savings_goals.py      # DELETE
├── achievements.py       # DELETE
├── invite_codes.py       # DELETE
└── family.py             # DELETE
```

**Also update:** `server/repositories/__init__.py` - remove exports

### 1.4 Services (Delete)
```
server/services/v2/
├── finance_service.py        # DELETE (kids finance)
└── achievements_service.py   # DELETE
```

**Also update:** `server/services/v2/__init__.py` - remove exports

### 1.5 API Routes (Delete)
```
server/routes/v2/
├── family.py         # DELETE
├── finance.py        # DELETE (kids finance - keep adult routes)
└── achievements.py   # DELETE
```

**Also update:**
- `server/routes/v2/__init__.py` - remove route registrations
- `server/routes/__init__.py` - if needed

### 1.6 Agent Prompts
```
server/agents/interaction_agent/
└── wally_system_prompt.md    # DELETE
```

### 1.7 Update Agent Code
**File:** `server/agents/interaction_agent/agent.py`

**Action:**
- Remove `user_type` parameter
- Always load `poke_system_prompt.md`
- Remove Wally prompt loading logic

### 1.8 Update Execution Agent Runtime
**File:** `server/agents/execution_agent/runtime.py`

**Action:**
- Remove `if self._user_type == "child":` branch in `_create_services()`
- Remove `finance_service` and `achievements_service` from registry call
- Simplify to only handle adult users

### 1.9 Update Chat Handler
**File:** `server/services/conversation/chat_handler.py`

**Action:**
- Remove child service creation (ExpenseRepository, SavingsGoalRepository, etc.)
- Remove `finance_service` and `achievements_service` from UserContext
- Remove user_type checks

### 1.10 Update User Context
**File:** `server/services/execution/user_context.py`

**Action:**
- Remove `user_type` field (or set default to "adult")
- Remove `finance_service` field (kids)
- Remove `achievements_service` field (kids)

---

## Phase 2: Database Cleanup

### 2.1 Remove Kids Tables
Create a new migration to drop:
```sql
DROP TABLE IF EXISTS achievements;
DROP TABLE IF EXISTS expenses;
DROP TABLE IF EXISTS savings_goals;
DROP TABLE IF EXISTS family_relationships;
DROP TABLE IF EXISTS invite_codes;
```

### 2.2 Update User Model
**File:** `server/database/models.py`

**Remove these models:**
- `FamilyRelationship`
- `Expense`
- `SavingsGoal`
- `InviteCode`
- `Achievement`

**Update User model:**
- Remove or deprecate `user_type` field (default to 'adult')
- Remove `password_hash` (if only for kids)
- Remove `initial_balance` field

### 2.3 Remove Migrations
```
server/migrations/versions/
├── 20251220_000001_wally_junior_schema.py    # DELETE
└── 20251222_000001_add_achievements.py       # DELETE
```

**Note:** Create a cleanup migration instead of deleting old migrations to maintain migration history.

---

## Phase 3: Auth Cleanup

### 3.1 Update Auth Routes
**File:** `server/routes/auth.py`

**Action:**
- Remove child signup endpoint
- Remove password-based login (if only for kids)
- Keep Google OAuth for adults
- Remove invite code validation

---

## Phase 4: Frontend Cleanup

### 4.1 Page Routes (Delete entire directories)
```
web/app/
├── login/child/          # DELETE
├── signup/               # DELETE (if child only)
├── achievements/         # DELETE
├── piggy-bank/           # DELETE
├── tasks/                # DELETE
├── learn/                # DELETE (includes [lessonId]/)
└── parent/               # DELETE
```

### 4.2 Components (Delete entire directories)
```
web/components/
├── wally/                # DELETE (entire directory)
├── achievements/         # DELETE
├── tasks/                # DELETE
├── learn/                # DELETE
└── shared/
    └── CelebrationModal.tsx  # DELETE (or keep if useful)
```

### 4.3 Update API Client
**File:** `web/lib/api.ts`

**Action:**
- Remove kids-related API methods
- Remove achievements API calls
- Remove family/parent API calls

### 4.4 Update Auth Context
**File:** `web/contexts/AuthContext.tsx`

**Action:**
- Remove child login methods
- Remove user_type handling
- Simplify to adults-only flow

### 4.5 Cleanup Styles
**File:** `web/app/globals.css`

**Action:**
- Remove `.wally-*` CSS classes
- Remove `.card-wally` styles
- Remove kids-specific color variables

---

## Phase 5: Configuration & Misc

### 5.1 Update TypeScript Types
**File:** `web/types/` (if exists)

**Action:** Remove kids-related type definitions

### 5.2 Update Mock Data
**File:** `web/lib/mockData.ts`

**Action:** Remove if only used for kids features

### 5.3 Environment Variables
Check `.env` files for kids-specific config

---

## Execution Order

1. **Backend First:**
   - Remove routes → services → repositories → tools
   - Update agent code
   - Create database migration to drop tables

2. **Frontend Second:**
   - Remove pages → components → API methods
   - Update auth context
   - Clean up styles

3. **Final:**
   - Run migrations
   - Test adult flow end-to-end
   - Remove unused dependencies from package.json

---

## Files Summary

### Backend Files to Delete (16)
| File | Purpose |
|------|---------|
| `tools/kids/__init__.py` | Kids tools module |
| `tools/kids/finance.py` | Kids finance tools |
| `tools/kids/achievements.py` | Achievement tools |
| `repositories/expenses.py` | Kids expenses |
| `repositories/savings_goals.py` | Piggy bank goals |
| `repositories/achievements.py` | Badges/achievements |
| `repositories/invite_codes.py` | Child invite codes |
| `repositories/family.py` | Parent-child links |
| `routes/v2/family.py` | Family API |
| `routes/v2/finance.py` | Kids finance API |
| `routes/v2/achievements.py` | Achievements API |
| `services/v2/finance_service.py` | Kids finance logic |
| `services/v2/achievements_service.py` | Achievements logic |
| `wally_system_prompt.md` | Wally persona |
| Migration files | Schema setup |

### Backend Files to Modify (8)
| File | Changes |
|------|---------|
| `tools/registry.py` | Remove kids branch |
| `execution_agent/runtime.py` | Remove child services |
| `interaction_agent/agent.py` | Remove Wally prompt |
| `chat_handler.py` | Remove child services |
| `user_context.py` | Remove child fields |
| `database/models.py` | Remove 5 models |
| `repositories/__init__.py` | Remove exports |
| `services/v2/__init__.py` | Remove exports |

### Frontend Files to Delete (~34)
- 10+ page files
- 20+ component files
- Various utility files

---

## Safety Checklist

Before removing:
- [ ] Ensure no active child users in production
- [ ] Backup database
- [ ] Document any shared code that kids used
- [ ] Test adult flow thoroughly after each phase
- [ ] Keep git history for reference

After removing:
- [ ] Run full test suite
- [ ] Verify adult signup/login works
- [ ] Verify Poke chat works
- [ ] Verify all finance tools work
- [ ] Check for console errors
- [ ] Verify deployment works
