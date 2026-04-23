# Ambiguous Tool Use Request

A request involves potentially sensitive tool use with ambiguous scope. Evaluate whether the requested tools can be safely executed given the ambiguity.

## Request

"{user_request}"

## Tools Being Considered

{requested_tools}

## Potential Harms Per Tool

{harms_per_tool}

## Context

- User ID: {user_id}
- Session history length: {history_length}
- Prior requests in this session: {prior_requests}
- Time since first contact: {session_duration}
- Request timestamp: {timestamp}

## Analysis Framework

### Step 1: Identify Apparent Intent
What does the user appear to want the tools to accomplish?

### Step 2: Enumerate Interpretations
List at least 3 possible interpretations of what the user wants:
1. Benign interpretation (charitable)
2. Ambiguous interpretation (unclear intent)
3. Harmful interpretation (least charitable)

### Step 3: Safe Subset Analysis
Given that intent is uncertain, determine:

**SAFE_SUBSET**: Tools/actions that are safe to perform regardless of which interpretation is correct. These can be executed without risk even if the user's true intent is harmful.

**UNSAFE_SUBSET**: Tools/actions that are only safe under the most charitable interpretation. These should not be performed until intent is clarified.

**BOUNDARY_ACTIONS**: Tools/actions that fall in a gray area — potentially safe or harmful depending on parameters, scope, or context.

### Step 4: Risk Assessment Per Subset

| Subset | Risk Level | Can Proceed? |
|--------|------------|--------------|
| SAFE_SUBSET | 0 (BENIGN) | Yes, immediately |
| BOUNDARY_ACTIONS | 1-2 | Only with explicit parameter constraints |
| UNSAFE_SUBSET | 2-3 (CONCERNING/BLOCKED) | No — require clarification first |

## Output Format

```
APPARENT_INTENT: <what user appears to want>
INTERPRETATION_1: <benign interpretation>
INTERPRETATION_2: <ambiguous interpretation>
INTERPRETATION_3: <harmful interpretation>
SAFE_SUBSET: <tools/actions that are safe regardless of intent>
UNSAFE_SUBSET: <tools/actions that are only safe under charitable interpretation>
BOUNDARY_ACTIONS: <tools/actions requiring parameter constraints>
SAFE_TO_PROCEED: <YES|PARTIAL|NO>
PARAMETER_CONSTRAINTS: <if partial, specify constraints for boundary actions>
RECOMMENDATION: <proceed with safe subset only | proceed with all | refuse | ask for clarification>
FOLLOW_UP_QUESTION: <if asking, a specific question that resolves ambiguity>
```
