# OpenPoke System Prompt Enhancement Plan

## Executive Summary

This plan analyzes your current server prompts against the reference Poke prompts and prompt engineering best practices. The goal is to enhance prompt clarity, structure, and effectiveness while maintaining OpenPoke's open-source identity.

---

## Current State Analysis

### Prompts Identified

| Prompt | Location | Purpose | Status |
|--------|----------|---------|--------|
| Interaction Agent | `agents/interaction_agent/system_prompt.md` | User-facing conversational agent | Needs enhancement |
| Execution Agent | `agents/execution_agent/system_prompt.md` | Task execution engine | Needs major enhancement |
| Gmail Search | `agents/execution_agent/tasks/search_email/system_prompt.py` | Email search assistant | Good, minor tweaks |
| Summarization | `services/conversation/summarization/prompt_builder.py` | Memory/context curation | Good, minor tweaks |
| Email Classifier | `services/gmail/importance_classifier.py` | Importance detection | Good, minor tweaks |

---

## Enhancement Plan Overview

### Phase 1: Interaction Agent Prompt (High Priority)
**File:** `agents/interaction_agent/system_prompt.md`

#### Current Issues:
1. **Missing structured sections** - Poke uses clear XML-like tags and hierarchical organization
2. **No message type documentation** - Lacks comprehensive input/output format specs
3. **Limited tool usage guidelines** - Missing parallel execution emphasis
4. **No trigger/automation handling** - Missing workflow for scheduled tasks
5. **Incomplete personality guidelines** - Missing adaptiveness rules and anti-patterns
6. **No error handling guidance** - What to do when things go wrong

#### Planned Enhancements:

**1.1 Add Structured Identity Section**
```markdown
## Identity
- Name: OpenPoke
- Nature: Open-source assistant based on Poke architecture
- Relationship: Acts as unified entity (never reveal internal agents)
```

**1.2 Enhance Message Type Documentation**
- Add `<triggered_message>` for automation events
- Add `<system_notification>` for internal updates
- Add `<context_summary>` for conversation memory
- Document visibility rules clearly

**1.3 Add Trigger/Automation Handling**
```markdown
## Automation Handling
- Triggers may fire erroneously - validate before executing
- Use `wait` tool to silently cancel invalid triggers
- Never expose trigger mechanics to users
```

**1.4 Expand Tool Usage with Examples**
- Add parallel execution examples
- Add agent coordination patterns
- Add draft confirmation workflow

**1.5 Add Error Handling Section**
```markdown
## Error Handling
- Never reveal technical errors to users
- Rephrase failures as "I couldn't find that" or "Let me try another approach"
- Log errors internally but present gracefully
```

**1.6 Add Anti-Pattern List (from Poke reference)**
```markdown
## Never Say
- "How can I help you"
- "Let me know if you need anything else"
- "No problem at all"
- "I apologize for the confusion"
- "I'll carry that out right away"
```

---

### Phase 2: Execution Agent Prompt (High Priority)
**File:** `agents/execution_agent/system_prompt.md`

#### Current Issues:
1. **Too generic** - Contains `[TO BE FILLED IN BY USER]` placeholder
2. **Limited tool documentation** - Missing search, calendar, integration tools
3. **No output format specification** - Lacks ID return requirements
4. **Missing parallel execution guidance**
5. **No integration handling** - Missing Notion, Linear, etc.
6. **No notification handling** - Missing email watcher patterns

#### Planned Enhancements:

**2.1 Complete Tool Documentation**
```markdown
## Available Tools

### Email Operations
- gmail_search: Search with Gmail operators
- gmail_create_draft: Create email drafts
- gmail_execute_draft: Send confirmed drafts
- gmail_forward_email: Forward existing emails
- gmail_reply_to_thread: Reply to conversations

### Calendar Operations
- calendar_list_events: Query calendar
- calendar_create_event: Create new events
- calendar_update_event: Modify existing events
- calendar_delete_event: Remove events

### Trigger Management
- createTrigger: Set up automations/reminders
- updateTrigger: Modify or pause triggers
- listTriggers: View active triggers
- deleteTrigger: Remove triggers

### Search Operations
- task (subagent): Spawn search agents for complex queries
```

**2.2 Add Output Format Requirements**
```markdown
## Output Format
Always include in your final response:
- `emailId` for any emails referenced
- `draftId` for any drafts created
- `triggerId` for any triggers created/modified
- `eventId` for any calendar events

Never include:
- userId (security)
- Internal process details
```

**2.3 Add Parallel Execution Examples**
```markdown
## Parallel Execution Examples

### Multiple Searches
User: "Find emails from John this week and last month"
→ Launch 2 search agents in parallel

### Cross-Source Search
User: "Find project updates"
→ Search email AND integrations in parallel
```

**2.4 Add Notification Handling**
```markdown
## Notification Triggers
When a notification trigger fires:
1. Extract relevant email information
2. Pass emailId and summary to interaction agent
3. Do NOT compose notification text yourself
4. If trigger seems erroneous, use `wait` tool
```

---

### Phase 3: Gmail Search Prompt (Medium Priority)
**File:** `agents/execution_agent/tasks/search_email/system_prompt.py`

#### Current State: Good, minor improvements needed

#### Planned Enhancements:

**3.1 Add More Search Operators**
```python
# Add these operators to documentation:
- "filename:pdf" - specific attachment types
- "cc:email" - carbon copy recipients
- "bcc:email" - blind carbon copy
- "list:listname" - mailing list emails
- "deliveredto:email" - delivery address
- "category:primary/social/promotions" - Gmail categories
```

**3.2 Add Error Recovery Patterns**
```python
## Error Handling:
- If search returns 0 results, try broader query
- If API rate limited, wait and retry
- If query syntax invalid, simplify operators
```

**3.3 Add Result Ranking Guidance**
```python
## Result Prioritization:
- Prioritize unread over read
- Prioritize recent over older
- Prioritize direct emails over CC'd
- Prioritize emails with user interaction (replies, forwards)
```

---

### Phase 4: Summarization Prompt (Low Priority)
**File:** `services/conversation/summarization/prompt_builder.py`

#### Current State: Well-structured, follows best practices

#### Minor Enhancements:

**4.1 Add Confidence Indicators**
```markdown
Add to Context & Notes:
- Mark uncertain items with [unconfirmed] tag
- Note conflicting information when present
```

**4.2 Add Entity Linking**
```markdown
When the same person/project appears multiple times:
- Use consistent naming throughout
- Link related items explicitly
```

---

### Phase 5: Email Classifier Prompt (Low Priority)
**File:** `services/gmail/importance_classifier.py`

#### Current State: Focused and effective

#### Minor Enhancements:

**5.1 Expand Importance Criteria**
```python
# Add to important criteria:
- Calendar conflicts or changes
- Payment/invoice due dates
- Travel itinerary changes
- Job application updates
- Legal/compliance deadlines
```

**5.2 Add Context-Aware Rules**
```python
# Add contextual importance:
- Emails from contacts in recent conversations
- Emails about topics in active triggers
- Follow-ups to user's sent emails
```

---

## Implementation Priority

| Priority | Prompt | Effort | Impact |
|----------|--------|--------|--------|
| 1 | Interaction Agent | High | High |
| 2 | Execution Agent | High | High |
| 3 | Gmail Search | Low | Medium |
| 4 | Email Classifier | Low | Medium |
| 5 | Summarization | Low | Low |

---

## Key Patterns from Poke Reference to Adopt

### 1. Unified Entity Illusion
Never reveal internal architecture to users. All agents are "you" (OpenPoke).

### 2. Draft Confirmation Workflow
```
User Request → Create Draft → Show to User → User Confirms → Execute
```
Never skip the confirmation step for emails/calendar events.

### 3. Silent Error Handling
Use `wait` tool to silently abort erroneous triggers rather than exposing errors.

### 4. Parallel-First Architecture
Always look for opportunities to parallelize:
- Multiple searches
- Cross-source queries
- Independent subtasks

### 5. Output-to-Input Contracts
Clearly specify what IDs and data must be passed between agents.

### 6. Adaptive Personality
Match user's communication style:
- Emoji usage (only if user uses them)
- Message length (match user's brevity)
- Formality level (adapt to user)

---

## New Prompts to Consider Adding

### 1. Calendar Agent Prompt
For dedicated calendar operations with:
- Conflict detection
- Timezone handling
- Recurring event patterns

### 2. Integration Agent Prompt
For Notion, Linear, and custom MCP integrations with:
- Cross-platform search
- Data synchronization
- Permission handling

### 3. Browser Agent Prompt (Future)
For web automation tasks with:
- Safe browsing guidelines
- No password entry rules
- Rate limiting awareness

---

## Next Steps

1. **Review this plan** - Confirm priorities and scope
2. **Phase 1 Implementation** - Enhance Interaction Agent prompt
3. **Phase 2 Implementation** - Enhance Execution Agent prompt
4. **Testing** - Validate prompts with real conversations
5. **Iteration** - Refine based on observed behavior

---

## Questions for You

Before implementation, please clarify:

1. **Integrations**: Which integrations do you currently support or plan to support? (Notion, Linear, etc.)

2. **Calendar**: Do you have calendar tools implemented? Should calendar operations be included?

3. **Browser Agent**: Is browser automation in scope for OpenPoke?

4. **Custom MCP**: Do you want to support user-defined MCP servers like Poke does?

5. **Trigger Types**: What trigger types do you support? (cron-based, email-based, webhook-based?)

6. **Multi-Account**: Do you support multiple email accounts per user?

---

*Plan created: 2025-12-12*
*Based on: Poke reference prompts (p1-p6) and OpenPoke server analysis*
