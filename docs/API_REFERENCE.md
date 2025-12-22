# Wally Junior API Reference

Base URL: `/api/v2`

## Authentication

All endpoints except child auth require JWT Bearer token in Authorization header.

### Child Authentication

#### Verify Invite Code
```
GET /auth/child/verify-code?code=ABCD1234
```

Response:
```json
{
  "valid": true,
  "child_name": "Ali",
  "initial_balance": 10000000
}
```

#### Child Signup
```
POST /auth/child/signup
Content-Type: application/json

{
  "invite_code": "ABCD1234",
  "password": "secret123"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Child Login
```
POST /auth/child/login
Content-Type: application/json

{
  "email": "ali_123@wally.junior",
  "password": "secret123"
}
```

Response: Same as signup

---

## Finance Endpoints

### Get Balance
```
GET /finance/balance
Authorization: Bearer <token>
```

Response:
```json
{
  "current_balance": 5000000,
  "initial_balance": 10000000,
  "total_spent": 3000000,
  "total_saved": 2000000
}
```

### Get Dashboard
```
GET /finance/dashboard
Authorization: Bearer <token>
```

Response:
```json
{
  "balance": 5000000,
  "total_spent_today": 50000,
  "total_spent_week": 500000,
  "total_spent_month": 2000000,
  "active_goals_count": 2,
  "total_saved": 2000000
}
```

### Get Expenses
```
GET /finance/expenses?limit=20
Authorization: Bearer <token>
```

Response:
```json
{
  "expenses": [
    {
      "id": 1,
      "amount": 50000,
      "category": "food",
      "description": "Ice cream",
      "expense_date": "2024-12-20T10:00:00Z",
      "created_at": "2024-12-20T10:00:00Z"
    }
  ],
  "total": 50
}
```

### Log Expense
```
POST /finance/expenses
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 50000,
  "category": "food",
  "description": "Ice cream"
}
```

Response:
```json
{
  "id": 1,
  "message": "Expense logged"
}
```

### Get Spending Summary
```
GET /finance/spending-summary?period=week
Authorization: Bearer <token>
```

Periods: `today`, `week`, `month`

Response:
```json
{
  "period": "week",
  "total": 500000,
  "by_category": {
    "food": 200000,
    "toys": 150000,
    "entertainment": 150000
  }
}
```

### Get Savings Goals
```
GET /finance/goals
Authorization: Bearer <token>
```

Response:
```json
{
  "goals": [
    {
      "id": 1,
      "name": "New Bike",
      "target_amount": 5000000,
      "current_amount": 2000000,
      "status": "active",
      "emoji": "🚲",
      "created_at": "2024-12-01T00:00:00Z",
      "completed_at": null
    }
  ]
}
```

### Create Savings Goal
```
POST /finance/goals
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "New Bike",
  "target_amount": 5000000,
  "emoji": "🚲"
}
```

Response:
```json
{
  "id": 1,
  "message": "Goal created"
}
```

### Add to Savings Goal
```
POST /finance/goals/{goal_id}/add
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 100000
}
```

Response:
```json
{
  "new_amount": 2100000,
  "completed": false,
  "message": "Added to savings"
}
```

### Delete Savings Goal
```
DELETE /finance/goals/{goal_id}
Authorization: Bearer <token>
```

Response:
```json
{
  "message": "Goal deleted"
}
```

---

## Family Endpoints (Parent Only)

### Create Child Account
```
POST /family/create-child
Authorization: Bearer <token>
Content-Type: application/json

{
  "child_name": "Ali",
  "initial_balance": 10000000
}
```

Response:
```json
{
  "invite_code": "ABCD1234",
  "child_name": "Ali",
  "initial_balance": 10000000,
  "expires_at": "2024-12-27T00:00:00Z"
}
```

### Get Children
```
GET /family/children
Authorization: Bearer <token>
```

Response:
```json
{
  "children": [
    {
      "id": "uuid-here",
      "display_name": "Ali",
      "email": "ali_123@wally.junior",
      "initial_balance": 10000000,
      "created_at": "2024-12-15T00:00:00Z"
    }
  ]
}
```

### Get Child Details
```
GET /family/child/{child_id}
Authorization: Bearer <token>
```

Response:
```json
{
  "id": "uuid-here",
  "display_name": "Ali",
  "email": "ali_123@wally.junior",
  "initial_balance": 10000000,
  "created_at": "2024-12-15T00:00:00Z",
  "balance": 5000000,
  "total_spent": 3000000,
  "total_saved": 2000000,
  "recent_expenses": [...],
  "savings_goals": [...]
}
```

### Get Pending Invites
```
GET /family/invites
Authorization: Bearer <token>
```

Response:
```json
{
  "invites": [
    {
      "id": 1,
      "code": "WXYZ5678",
      "child_name": "Sara",
      "initial_balance": 5000000,
      "expires_at": "2024-12-27T00:00:00Z",
      "created_at": "2024-12-20T00:00:00Z"
    }
  ]
}
```

### Cancel Invite
```
DELETE /family/invite/{invite_id}
Authorization: Bearer <token>
```

Response:
```json
{
  "message": "Invite cancelled"
}
```

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message here"
}
```

Common HTTP status codes:
- `400` - Bad request (invalid input)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (not allowed)
- `404` - Not found
- `500` - Server error
