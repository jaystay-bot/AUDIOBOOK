# BOOK BIBLE — internal brief for writers (not narrated)

**Working title:** *OPERATOR — How to Command AI in 2026 (and Not Get Out-Computed)*
**Listener:** Jay (jaystay). Solo builder / operator. Smart, impatient, no CS PhD, ships
things. Pays for frontier models, does NOT use free tiers. Has Midjourney + a stack of
tools. Wants to understand how to *instruct* AI so it does deep, autonomous work for him —
and how to stay economically relevant as AI eats startups and jobs.

**Why it exists:** This is the audiobook Jay would *want* played to him — the one that
teaches the person giving the instructions how to give the *right* instructions. No fluff,
no "AI is amazing" cheerleading, no doom. Operator-grade. Dense. Honest about tradeoffs.

## Hard rules for every chapter

1. **Spoken style.** Write a SCRIPT to be read aloud by a TTS voice. Short-to-medium
   sentences. Natural spoken cadence. No markdown headers, no bullet lists, no code blocks,
   no URLs read aloud, no "Chapter 3, section 2." Spell out small numbers. Say "for example"
   not "e.g." Say "percent" not "%". Avoid tongue-twisters and long parentheticals.
2. **Length:** ~2,100–2,400 words (~15 minutes at narration pace). The intro can be ~1,700.
3. **No invented version numbers.** Refer to model *families* — Claude (Opus / Sonnet /
   Haiku), GPT-5 family, Gemini, Grok, plus open-weight DeepSeek, Qwen, Llama, Mistral, GLM.
   You may say "as of mid-2026" and describe capability *tiers* and *trends*, but never bet
   the content on a specific point-release that will be stale in a month. Teach durable
   judgment, not a leaderboard snapshot.
4. **Real, concrete, actionable.** Every chapter must give the listener something they can
   DO. Prefer specific moves, mental models, and named techniques over vibes.
5. **Honest.** Name the tradeoffs and failure modes. Where something is hype, say so.
6. **Voice:** Direct, warm, a little blunt. Second person ("you"). Like a sharp friend who
   has shipped a lot and respects your time. Occasional dry humor. Never condescending.
7. **Continuity:** You may reference earlier ideas by name (the Instruction Stack, the
   Jaystay Loop, guardrails, the human moat) but don't depend on the listener remembering
   exact wording.
8. **Output:** Write ONLY the narrated text (plain prose paragraphs) to the target file.
   Start with a single spoken title line, then the body. No meta commentary.

## The seven tracks

- 00 Cold Open — why this exists, the real stakes, how to listen.
- 01 The Map — the 2026 model landscape and how to choose without a benchmark obsession.
- 02 The Instruction Stack — how to make an LLM actually perform (context engineering, specs, evals).
- 03 The Jaystay System Loop — a repeatable operating loop for getting deep work out of agents.
- 04 Autonomy Inside Guardrails — deep autonomous work without constant key/auth babysitting, safely.
- 05 Build With What's Free — GitHub repos, public endpoints, MCP → a shipped product.
- 06 Don't Get Out-Computed — the human moat: leverage, taste, distribution, ownership.

## Recurring concepts (use consistently)

- **The Instruction Stack:** role/spec → context → constraints → output contract → eval loop.
- **The Jaystay Loop:** Frame → Brief → Constrain → Unleash → Inspect → Bank. (deep work cycle)
- **Guardrails, not handcuffs:** scope autonomy with budgets, allowlists, dry-runs, checkpoints.
- **The human moat:** taste, judgment, distribution, relationships, ownership of the problem.
- **Out-computed vs out-thought:** the machine wins on compute; you win on what to point it at.
