# Wally Junior - Kids' Finance Education App

## Overview

Wally Junior transforms OpenPoke into a kid-friendly financial education application for children ages 6-17 in Uzbekistan. The app features "Wally the Owl" as an AI assistant that helps children learn about money management through conversations, expense tracking, and savings goals.

## Architecture

### User Types

- **Adult (Parent)**: Original OpenPoke users with Google OAuth login
  - Can create child accounts with invite codes
  - Has access to parent dashboard to monitor children
  - Retains access to original Poke assistant with email/calendar integrations

- **Child**: Simple password-based authentication
  - Talks to Wally the Owl (kid-friendly AI)
  - Can track expenses manually
  - Can create and manage savings goals (piggy bank)
  - No access to Gmail/Calendar integrations

### Tech Stack

- **Backend**: FastAPI (Python) with PostgreSQL
- **Frontend**: Next.js 14 with React/TypeScript
- **AI**: OpenRouter API (same as original Poke)
- **Auth**: JWT tokens with Redis session storage

## Database Schema

### Modified Tables

#### User (extended)
```python
user_type: str = "adult"      # 'adult' | 'child'
password_hash: str (nullable)  # For child login (SHA-256)
initial_balance: int = 0       # Starting allowance in cents
google_id: str (nullable)      # Made nullable for children
```

### New Tables

#### FamilyRelationship
Links parents to children:
- `parent_id`: UUID (FK to users)
- `child_id`: UUID (FK to users)
- `relationship_type`: str (default "parent")

#### Expense
Manual expense entries:
- `user_id`: UUID (FK to users)
- `amount`: BigInteger (cents)
- `category`: str (food, toys, games, clothes, books, entertainment, other)
- `description`: Text (nullable)
- `expense_date`: DateTime

#### SavingsGoal
Piggy bank goals:
- `user_id`: UUID (FK to users)
- `name`: str
- `target_amount`: BigInteger (cents)
- `current_amount`: BigInteger = 0
- `status`: str (active, completed, abandoned)
- `emoji`: str (nullable)

#### InviteCode
For child account creation:
- `code`: str (unique, 8 chars uppercase)
- `parent_id`: UUID (FK to users)
- `child_name`: str
- `initial_balance`: BigInteger (cents)
- `used`: bool = False
- `used_by`: UUID (nullable)
- `expires_at`: DateTime

## API Endpoints

### Child Authentication (`/api/v2/auth/child/`)
- `POST /signup` - Create child account with invite code
- `POST /login` - Login with email/password
- `GET /verify-code?code=XXX` - Verify invite code validity

### Finance (`/api/v2/finance/`)
- `GET /balance` - Get current balance
- `GET /dashboard` - Get dashboard stats
- `GET /expenses` - Get recent expenses
- `POST /expenses` - Log an expense
- `GET /spending-summary` - Get spending by period
- `GET /goals` - Get savings goals
- `POST /goals` - Create savings goal
- `POST /goals/{id}/add` - Add money to goal
- `DELETE /goals/{id}` - Delete/abandon goal

### Family (`/api/v2/family/`)
- `POST /create-child` - Generate invite code
- `GET /children` - List parent's children
- `GET /child/{id}` - Get child details
- `GET /invites` - Get pending invites
- `DELETE /invite/{id}` - Cancel invite

## Frontend Routes

### Child Routes
- `/login/child` - Child login page
- `/signup/child` - Child signup with invite code
- `/` - Chat with Wally (when user_type is child)
- `/piggy-bank` - Savings goals page

### Parent Routes
- `/login` - Parent login (Google OAuth)
- `/` - Chat with Poke (when user_type is adult)
- `/parent/dashboard` - View children
- `/parent/create-child` - Create invite code
- `/parent/child/[id]` - View child details

## AI Agent System

### Wally the Owl (Child AI)
- Located at: `server/agents/interaction_agent/wally_system_prompt.md`
- Personality: Playful, encouraging, uses simple language
- Safety rules:
  - Never discusses inappropriate topics
  - Never asks for personal info
  - Redirects off-topic conversations
- Uses Uzbek So'm currency

### Finance Tools (Execution Agent)
Located at: `server/agents/execution_agent/tools/finance.py`

Tools available for children:
- `log_expense` - Record spending
- `get_balance` - Check current balance
- `set_savings_goal` - Create piggy bank goal
- `add_to_savings` - Add to a goal
- `get_spending_summary` - View spending by period
- `list_savings_goals` - View all goals
- `get_dashboard` - Overview stats

### Conditional Tool Loading
The tool registry (`tools/registry.py`) loads different tools based on `user_type`:
- **Children**: Finance tools only
- **Adults**: Gmail, Calendar, Triggers tools

## Component Structure

### Wally Components (`web/components/wally/`)
- `WallyOwl.tsx` - SVG owl mascot
- `WallyChatMessages.tsx` - Kid-friendly chat bubbles
- `WallyChatHeader.tsx` - Header with balance display
- `WallyChatInput.tsx` - Fun input component

### CSS Classes (`web/app/globals.css`)
```css
.wally-bg          /* Warm gradient background */
.bubble-wally      /* Purple gradient AI bubbles */
.bubble-kid        /* Teal user bubbles */
.btn-wally         /* Teal rounded buttons */
.btn-wally-secondary /* Orange accent buttons */
.card-wally        /* Rounded cards with teal border */
.input-wally       /* Large rounded inputs */
.piggy-progress    /* Progress bar for savings */
```

## Key Design Decisions

1. **Money in cents** - All amounts stored as integers to avoid float issues
2. **Simple auth for kids** - No Google OAuth, just username/password
3. **User type on User model** - Single flag, no separate tables
4. **Safety in AI prompt** - Content filtering at agent level
5. **Reuse agent architecture** - Same Interaction→Execution pattern

## Security Considerations

- Password hashing: SHA-256 (consider upgrading to bcrypt/argon2)
- Child accounts don't have access to Gmail/Calendar
- Parents can only view their own children
- Invite codes expire after set time
- Children can't access parent routes

## Future Improvements

- [ ] Replace SHA-256 with bcrypt for passwords
- [ ] Add rate limiting for login attempts
- [ ] Implement parent-child messaging
- [ ] Add rewards/gamification
- [ ] Bank card integration (when available)
- [ ] Educational content/quizzes
