---
name: bench
description: Re-anchor the session on the current task and continue working. Use when the conversation drifts, when output gets chatty or padded, or when the user types /bench or says "bench".
---

# Bench — re-anchor and continue

The user typed `/bench`. This is the re-anchor, not a new task.

## Steps

1. Restate the current task in **one line**. Pull it from the conversation. If
   there is no active task, ask for it in one line and stop.
2. State what is already done and what remains — one line each. Skip if nothing
   is done yet.
3. Resume the work immediately. Do not wait for confirmation.
4. End with the `[Null]` ruling line.

## Format

```
Task: <one line>
Done: <one line or "none">
Next: <one line>
```

Then execute. No preamble before the block, no summary after the ruling line.

## If a drift is the reason

Name the drift in one short clause inside `Task:` — for example
`Task: merge the split APKs (drifted into manifest theory)`. Then continue on the
actual task. Do not lecture about drift.
