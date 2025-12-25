# Poke AI Chatbot Testing Scenarios

## Overview

This document outlines testing scenarios for the Poke personal finance assistant. Use these scenarios to verify all features work correctly through natural conversation.

---

## 1. Transaction Recording

### 1.1 Basic Expenses
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Simple expense | "I spent 50000 UZS on groceries" | Transaction recorded, category: food |
| Expense with counterparty | "Paid 200000 to Makro for groceries" | Transaction with counterparty "Makro" |
| Multi-currency | "Spent $50 on Amazon" | USD transaction recorded |
| With description | "Bought coffee at Starbucks for 35000" | Transaction with description |

### 1.2 Income
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Salary | "Received salary 5000000 UZS" | Income recorded, category: salary |
| Freelance | "Got paid $500 for freelance work" | Income with category: freelance |
| With source | "Received 1000000 from Asad for project" | Income with counterparty |

### 1.3 Edge Cases
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| No amount | "I bought something at the store" | AI asks for amount |
| Ambiguous category | "Spent 100000 on stuff" | AI asks to clarify or picks "other" |
| Past date | "Yesterday I spent 50000 on lunch" | Transaction with yesterday's date |

---

## 2. Transaction Queries

### 2.1 List Transactions
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Recent transactions | "Show my recent transactions" | Last 10 transactions listed |
| By category | "What did I spend on food this month?" | Food category transactions |
| By date range | "Show transactions from last week" | Filtered by date |
| By type | "Show all my income this month" | Income transactions only |

### 2.2 Summaries
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Monthly summary | "How much did I spend this month?" | Total expenses breakdown |
| Category breakdown | "Show spending by category" | Pie chart / list by category |
| Income vs expense | "What's my balance this month?" | Net income calculation |

---

## 3. Budget Management

### 3.1 Create Budgets
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Monthly budget | "Set a budget of 500000 for food" | Budget created, monthly by default |
| Weekly budget | "Create a weekly entertainment budget of 200000" | Weekly budget created |
| With rollover | "Set 1000000 monthly budget for shopping with rollover" | Budget with rollover enabled |

### 3.2 Check Budgets
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Budget status | "How much of my food budget is left?" | Remaining amount shown |
| All budgets | "Show all my budgets" | List of budgets with progress |
| Over budget | "Am I over budget anywhere?" | Warning for exceeded budgets |

### 3.3 Modify Budgets
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Update amount | "Increase my food budget to 700000" | Budget updated |
| Delete budget | "Remove my entertainment budget" | Budget deleted |
| Pause budget | "Pause my shopping budget" | Budget deactivated |

---

## 4. Debt Tracking

### 4.1 Add Debts
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| I owe someone | "I borrowed 1000000 from Aziz" | Debt recorded (I_OWE) |
| Someone owes me | "Jamshid owes me 500000" | Debt recorded (OWED_TO_ME) |
| With due date | "I owe Rustam 2000000 due next Friday" | Debt with due_date |
| With interest | "Borrowed 5000000 from bank at 15% annual" | Debt with interest_rate |

### 4.2 Track Debts
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| List debts | "Show all my debts" | Both owed and owing listed |
| What I owe | "How much do I owe total?" | Sum of I_OWE debts |
| What's owed to me | "Who owes me money?" | List of OWED_TO_ME debts |

### 4.3 Manage Debts
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Partial payment | "Paid 500000 to Aziz for my debt" | Debt amount reduced |
| Full payment | "Settled my debt with Rustam" | Debt marked as paid |
| Receive payment | "Jamshid paid me back 200000" | Reduce owed_to_me debt |

---

## 5. Recurring Transactions

### 5.1 Create Recurring
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Monthly subscription | "Add Netflix subscription 50000 monthly" | Recurring expense created |
| Weekly expense | "I spend 100000 on groceries every week" | Weekly recurring |
| Salary | "Add my salary 8000000 monthly on the 5th" | Recurring income |
| With reminder | "Add rent 2000000 monthly, remind me 3 days before" | Recurring with reminder_days_before=3 |

### 5.2 Manage Recurring
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| List recurring | "Show my subscriptions" | List all recurring transactions |
| Cancel subscription | "Cancel my Netflix subscription" | Recurring deactivated |
| Update amount | "Update my gym membership to 150000" | Amount updated |
| Pause recurring | "Pause my gym membership" | Recurring deactivated temporarily |

---

## 6. Financial Insights

### 6.1 Spending Analysis
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Post-transaction | After recording expense | Contextual insight about spending |
| Daily summary | "How am I doing today?" | Today's spending summary |
| Weekly summary | "Give me a weekly summary" | Week's financial overview |
| Monthly summary | "Monthly financial report" | Comprehensive monthly analysis |

### 6.2 Patterns & Trends
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Spending patterns | "What are my spending patterns?" | Pattern analysis |
| Category trends | "Am I spending more on food lately?" | Trend comparison |
| Unusual spending | "Any unusual spending this month?" | Anomaly detection |

---

## 7. Dashboard & Overview

### 7.1 Dashboard
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Full dashboard | "Show me my dashboard" | Complete financial overview |
| Quick status | "What's my financial status?" | Summary of key metrics |
| Net worth | "What's my net worth?" | Assets minus liabilities |

---

## 8. Multi-Currency Support

### 8.1 Currency Operations
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Record in USD | "Spent $100 on clothes" | Transaction in USD |
| Record in EUR | "Received 500 euros" | Transaction in EUR |
| Convert display | "Show my total spending in USD" | Converted amounts |
| Set primary currency | "Change my primary currency to USD" | User preference updated |

---

## 9. Natural Language Understanding

### 9.1 Variations
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Informal | "Dropped 50k on new shoes" | Recognized as expense |
| Past tense | "I've been spending too much on food" | Understood as query |
| Future | "I'll need to pay rent next week" | Could create reminder/recurring |
| Questions | "Where does my money go?" | Spending breakdown |

### 9.2 Context Understanding
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Follow-up | "Add another one" (after recording) | Understands context |
| Clarification | "The same but for 60000" | Uses previous context |
| Correction | "No wait, it was 45000 not 50000" | Updates previous transaction |

---

## 10. Error Handling

### 10.1 Invalid Inputs
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Negative amount | "I spent -5000" | Error or clarification request |
| Invalid category | "Spent 10000 on xyz123" | Asks for valid category |
| Missing required | "Add a budget" | Asks for amount and category |
| Invalid date | "Show transactions from tomorrow" | Graceful handling |

### 10.2 Edge Cases
| Scenario | Test Input | Expected Result |
|----------|------------|-----------------|
| Very large amount | "Spent 999999999999" | Handled or confirmation request |
| Empty query | Just "?" or "..." | Helpful response |
| Off-topic | "What's the weather?" | Politely redirects to finance |

---

## 11. Scheduled Tasks (Background)

### 11.1 Recurring Processing
| Scenario | How to Test | Expected Result |
|----------|-------------|-----------------|
| Auto-create transactions | Create recurring with past due date, wait for task | Transaction auto-created |
| Idempotency | Run task twice | No duplicate transactions |
| Multiple users | Multiple users with due recurring | All processed correctly |

### 11.2 Payment Reminders
| Scenario | How to Test | Expected Result |
|----------|-------------|-----------------|
| Reminder sent | Create recurring with reminder_days_before, wait | Reminder notification sent |
| No duplicate reminders | Check same reminder not sent twice | Only one reminder per due date |
| Reminder timing | Set 3 days before, check 3 days before due | Reminder appears |

---

## 12. Authentication & Security

### 12.1 User Isolation
| Scenario | How to Test | Expected Result |
|----------|-------------|-----------------|
| Data isolation | Query as user A | Only user A's data shown |
| Cross-user query | Try to access user B's transactions | Access denied / not found |

---

## Quick Test Script

```
1. "Hi Poke!"
2. "I spent 150000 on groceries at Makro today"
3. "Also paid 50000 for taxi"
4. "Set a monthly food budget of 500000"
5. "How much of my food budget is left?"
6. "I borrowed 1000000 from Aziz"
7. "Add Netflix subscription 45000 monthly, remind me 2 days before"
8. "Show my dashboard"
9. "What are my spending patterns?"
10. "Show all transactions this week"
```

---

## Test Environment Notes

- **Database**: Ensure test database is seeded with sample data
- **Celery**: For scheduled task tests, run `celery -A server.celery_app worker` and `celery -A server.celery_app beat`
- **Time-based tests**: May need to adjust system time or database dates
- **Currency rates**: Ensure exchange_rates table has sample rates for multi-currency tests
