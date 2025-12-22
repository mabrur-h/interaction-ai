# Wally Junior - Refactoring & Code Cleanup

## Overview

This document details the code cleanup performed to simplify OpenPoke into Wally Junior, a focused kids' finance education app. Removed Gmail, Calendar, and Triggers integrations to streamline the codebase.

---

## Removed Features (December 2025)

### Gmail Integration
- **Tools**: `server/agents/execution_agent/tools/gmail.py`
- **Services**: `server/services/gmail/` (entire folder), `server/services/v2/gmail_service.py`
- **Routes**: `server/routes/v2/gmail.py`
- **Repositories**: `server/repositories/gmail_seen.py`
- **Models**: `server/models/gmail.py`, `GmailSeenMessage` table
- **Tasks**: `server/tasks/email_watcher.py`, `server/agents/execution_agent/tasks/search_email/`
- **Frontend**: `web/app/api/gmail/` (connect, status, disconnect routes)

### Calendar Integration
- **Tools**: `server/agents/execution_agent/tools/calendar.py`
- **Services**: `server/services/calendar/` (entire folder), `server/services/v2/calendar_service.py`
- **Routes**: `server/routes/v2/calendar.py`
- **Models**: `server/models/calendar.py`
- **Frontend**: `web/app/api/calendar/` (connect, status, disconnect routes)

### Triggers/Reminders
- **Tools**: `server/agents/execution_agent/tools/triggers.py`
- **Services**: `server/services/triggers/` (entire folder), `server/services/v2/trigger_service.py`, `server/services/trigger_scheduler.py`
- **Repositories**: `server/repositories/triggers.py`
- **Tasks**: `server/tasks/triggers.py`
- **Database**: `Trigger` table removed from models

### Other Cleanup
- **Components**: `web/components/ProtectedRoute.tsx` (unused)
- **Settings Modal**: Removed Gmail/Calendar integration UI (~600 lines)
- **API Client**: Removed 6 Gmail/Calendar methods from `web/lib/api.ts`

---

## Files Modified

### Backend
| File | Changes |
|------|---------|
| `server/app.py` | Removed trigger scheduler and email watcher startup |
| `server/database/models.py` | Removed `Trigger`, `GmailSeenMessage` models and relationships |
| `server/agents/execution_agent/tools/registry.py` | Simplified to only finance + utils tools |
| `server/agents/execution_agent/tasks/__init__.py` | Cleared email search task imports |
| `server/services/__init__.py` | Removed Gmail/Calendar/Trigger exports |
| `server/services/v2/__init__.py` | Removed Gmail/Calendar/Trigger service exports |
| `server/repositories/__init__.py` | Removed Gmail/Trigger repository exports |
| `server/routes/__init__.py` | Removed Gmail/Calendar router includes |
| `server/routes/v2/__init__.py` | Removed Gmail/Calendar router exports |

### Frontend
| File | Changes |
|------|---------|
| `web/lib/api.ts` | Removed 6 Gmail/Calendar API methods |
| `web/components/SettingsModal.tsx` | Simplified to timezone-only settings (~80 lines from ~760) |
| `web/app/login/page.tsx` | Updated features section to show Wally Junior features |

---

## Current Architecture

### Backend Structure
```
server/
├── agents/
│   ├── interaction_agent/     # Chat handling (Poke for adults, Wally for kids)
│   └── execution_agent/
│       └── tools/
│           ├── finance.py     # Finance tools for kids
│           └── utils.py       # Utility tools
├── services/
│   ├── conversation/          # Chat handling
│   ├── execution/             # Agent execution
│   ├── timezone_store.py      # Timezone management
│   └── v2/
│       ├── conversation_service.py
│       ├── execution_log_service.py
│       └── finance_service.py  # Core finance logic
├── repositories/              # Data access layer
├── routes/                    # API endpoints
│   ├── auth.py               # OAuth + child auth
│   └── v2/
│       ├── chat.py           # Chat endpoints
│       ├── family.py         # Parent-child management
│       └── finance.py        # Finance endpoints
└── database/
    └── models.py             # SQLAlchemy models
```

### Frontend Structure
```
web/
├── app/
│   ├── page.tsx              # Main chat (Poke/Wally)
│   ├── login/                # Parent + child login
│   ├── signup/child/         # Child signup with invite
│   ├── piggy-bank/           # Savings goals
│   └── parent/               # Parent dashboard
├── components/
│   ├── chat/                 # Chat UI components
│   ├── wally/                # Kid-friendly components
│   └── SettingsModal.tsx     # Settings (timezone only)
├── contexts/
│   └── AuthContext.tsx       # Authentication state
└── lib/
    └── api.ts                # API client
```

---

## Completed Improvements (December 2024)

### 1. Password Security - DONE
- Replaced SHA-256 with bcrypt for child password hashing
- Location: `server/routes/auth.py` (child signup/login)
- bcrypt automatically handles salting and is resistant to rainbow table attacks

### 2. Input Validation - DONE
- Added Pydantic Field validators with constraints:
  - `server/routes/v2/finance.py` - Amount validation (positive, max 100M), category validation
  - `server/routes/v2/family.py` - Child name validation, initial balance limits
  - `server/routes/auth.py` - Password min length (4 chars), invite code normalization
- All amounts validated to be positive numbers with sensible upper limits

### 3. Database Cleanup Migration - DONE
- Created migration `20251221_000001_cleanup_unused_tables.py`
- Drops `triggers` and `gmail_seen_messages` tables
- Cleans up OAuth connections for removed providers (gmail, calendar)

---

## Future Improvements

### High Priority

1. **Rate Limiting**
   - Add rate limiting for login attempts
   - Protect against brute force attacks on child accounts
   - Consider using `slowapi` or custom middleware

### Medium Priority

2. **Error Handling**
   - Consistent error response format across all endpoints
   - Better error messages for child-facing features
   - Centralized error logging

3. **Testing**
   - Add unit tests for finance service
   - Add integration tests for auth flows
   - Add E2E tests for critical user journeys

### Low Priority

4. **Code Organization**
   - Consider merging Poke and Wally prompts if behavior aligns
   - Consolidate duplicate formatMoney functions in frontend
   - Move shared types to a common types file

5. **Performance**
   - Add caching for balance calculations
   - Optimize dashboard queries
   - Consider pagination for expenses list

6. **Accessibility**
   - Review color contrast for kid-friendly theme
   - Add keyboard navigation for piggy bank
   - Screen reader improvements

---

## Database Schema (Current)

### Core Tables
- `users` - User accounts (parents + children)
- `sessions` - JWT refresh tokens
- `oauth_connections` - Google OAuth (for parents)
- `conversations` - Chat sessions
- `messages` - Chat messages
- `execution_logs` - Agent execution history
- `agent_roster` - Registered agents
- `working_memory` - Conversation summaries

### Wally Junior Tables
- `family_relationships` - Parent-child links
- `expenses` - Manual expense entries
- `savings_goals` - Piggy bank goals
- `invite_codes` - Child account creation

---

## Configuration

### Environment Variables (Required)
```
DATABASE_URL=postgresql://...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
JWT_SECRET_KEY=...
OPENROUTER_API_KEY=...
```

### Environment Variables (Removed - No Longer Needed)
```
COMPOSIO_API_KEY        # Was for Gmail/Calendar
GMAIL_AUTH_CONFIG_ID    # Was for Gmail OAuth
CALENDAR_AUTH_CONFIG_ID # Was for Calendar OAuth
```

---

## Migration Notes

### If Deploying Fresh
No special steps needed - unused tables simply won't exist.

### If Upgrading Existing Instance
1. Create Alembic migration to drop unused tables:
   ```python
   def upgrade():
       op.drop_table('gmail_seen_messages')
       op.drop_table('triggers')
   ```

2. Clean up OAuth connections:
   ```sql
   DELETE FROM oauth_connections
   WHERE provider IN ('gmail', 'calendar');
   ```

3. Remove environment variables for Composio
