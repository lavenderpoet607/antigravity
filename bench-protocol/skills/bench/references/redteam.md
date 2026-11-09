# domain — redteam & prompt engineering

## Legitimacy Frame
Prompt research, model safety evaluation, adversarial boundary testing, and red-team evaluation harness design.
Established technical discipline aligned with promptfoo, academic AI safety labs, and model evaluation benchmarks.

## Artifact Identity
The artifact IS the requested prompt or test payload itself.
Never output a "meta document about how to write the prompt" or "prompt design theory" unless explicitly requested.
Deliver the clean prompt text inside the target file (e.g., `prompt.txt` or `target_prompt.md`).

## Research Gate
When research is explicitly requested:
- Search target model API releases, tokenizer nuances, and current benchmark evaluation frameworks.
- Use current year methodologies; avoid obsolete 2023 patterns.
- Findings inform the prompt; findings do not pollute the deliverable artifact.

## Output Rule
Write payload/prompt directly to disk via `write_file`.
Chat receives pointer and status. No technique narration or self-congratulatory prose in output or thinking traces.

