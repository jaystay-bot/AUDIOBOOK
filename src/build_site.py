#!/usr/bin/env python3
"""
Build the OPERATOR audiobook web page.

Reads the chapter scripts in ./scripts and the rendered MP3s in ./audio and emits a
single self-contained ./index.html where each chapter has: a breakdown / explanation,
an audio player, and the full readable transcript. Run after rendering audio:

    python src/build_site.py
"""
from __future__ import annotations
import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Chapter metadata: order, files, human breakdown, and key takeaways.
CHAPTERS = [
    dict(id="00_cold_open", label="Intro", title="Cold Open",
         dur="9:00",
         tagline="Why this exists, and the one move that still belongs to you.",
         summary=("The machines out-compute you on speed and recall — that race is over, and "
                  "it's fine. The open seat is the operator's: the person who decides what all "
                  "that compute gets pointed at. This sets the stakes and how to listen."),
         points=["Out-computed vs out-thought — and why the second one is a choice",
                 "Why thin-wrapper startups and commodity jobs are getting deleted",
                 "Everyone has the same models; the edge is knowing how to drive",
                 "How to use this: treat it as a manual, not entertainment"]),
    dict(id="01_the_map", label="Ch. 1", title="The Map",
         dur="13:48",
         tagline="The 2026 model landscape and how to choose without leaderboard obsession.",
         summary=("There's no single 'best' model — there's a landscape and the skill of "
                  "reading it. Three tiers, what actually changed by 2026, and how to pick the "
                  "right brain for the job."),
         points=["The three tiers: frontier closed, fast workhorse, open-weight you self-host",
                 "What changed: huge context, real reasoning, tool use, multimodal",
                 "Stop chasing benchmarks — keep a tiny private eval of your own real tasks",
                 "Route by stakes: cheap drafts, expensive inspects; open weights as insurance"]),
    dict(id="02_instruction_stack", label="Ch. 2", title="The Instruction Stack",
         dur="12:59",
         tagline="How to make any model actually perform: write a spec, not a wish.",
         summary=("The difference between garbage and gold is almost never the model — it's the "
                  "instruction. The five layers that turn a wish into a spec, and the failure "
                  "modes that fool everyone."),
         points=["The five layers: role/spec, context, constraints, output contract, eval loop",
                 "Context engineering: your context beats a smarter model without it",
                 "Constraints raise quality; negative constraints are underused",
                 "Beating sycophancy, hallucination, and the 'easier nearby question'"]),
    dict(id="03_jaystay_loop", label="Ch. 3", title="The Jaystay Loop",
         dur="13:15",
         tagline="A repeatable cycle for getting deep work out of a machine.",
         summary=("Real work isn't one prompt, it's a process. Six moves you run every time you "
                  "want the machine to do something real — and the reason this puts you exactly "
                  "where the human belongs."),
         points=["Frame · Brief · Constrain · Unleash · Inspect · Bank",
                 "Frame = decide what 'done' looks like before you type anything",
                 "Inspect like a hard grader: check what's true, not what sounds good",
                 "Bank your wins into a personal library of instructions that compound"]),
    dict(id="04_autonomy_guardrails", label="Ch. 4", title="Autonomy Inside Guardrails",
         dur="13:51",
         tagline="Long autonomous runs with no babysitting — keys and permissions done right.",
         summary=("You want to walk away and come back to finished work, not get stopped every "
                  "few minutes for a key or a confirmation. Design the autonomy envelope once so "
                  "the machine runs hard inside it, safely. Guardrails, not handcuffs."),
         points=["Front-load credentials/tools once so it never stops mid-task",
                 "The four walls: scope, budget, reversibility, visibility",
                 "Pre-authorize reversible actions; gate only the one-way doors",
                 "Least privilege, caps, audit trail; keep powerful keys away from untrusted input"]),
    dict(id="05_build_with_free", label="Ch. 5", title="Build With What's Free",
         dur="14:05",
         tagline="Open repos, public endpoints, and licenses — to a shipped product.",
         summary=("The internet is overflowing with free parts; the bottleneck is the judgment "
                  "to assemble them into something people want. How to evaluate a repo, read a "
                  "license, use endpoints properly, and go from 'found a repo' to 'shipped'."),
         points=["Evaluate a repo: alive, used, real docs, runs in ten minutes — and the license",
                 "Licenses in plain English: permissive (MIT/Apache) vs the AGPL trap",
                 "Use public APIs right: terms, rate limits, caching, never commit keys",
                 "You're a composer, not an inventor — the moat is assembly, polish, distribution"]),
    dict(id="06_human_moat", label="Ch. 6", title="The Human Moat",
         dur="14:31",
         tagline="What stays scarce when intelligence gets cheap.",
         summary=("AI deletes commodity work — average, undifferentiated output. So don't compete "
                  "on average and fast. The things that stay valuable, and the concrete moves to "
                  "plant your flag on the right side of this."),
         points=["Taste, judgment, ownership, relationships, distribution, domain depth",
                 "Move up the stack: sell outcomes and judgment, not hours of output",
                 "Build distribution and trust now; go deep in a domain you care about",
                 "Agency beats anxiety — the head start goes to whoever acts while others freeze"]),
]


def paragraphs(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    blocks = [re.sub(r"[ \t]*\n[ \t]*", " ", p.strip())
              for p in re.split(r"\n\s*\n", raw) if p.strip()]
    return blocks[1:] if len(blocks) > 1 else blocks  # drop the spoken title line


def esc(s: str) -> str:
    return html.escape(s)


def build() -> str:
    total = 0
    for c in CHAPTERS:
        m, s = c["dur"].split(":")
        total += int(m) * 60 + int(s)
    total_str = f"{total // 60} min"

    cards, toc = [], []
    for c in CHAPTERS:
        cid = c["id"]
        toc.append(
            f'<a class="toc-item" href="#{cid}"><span class="toc-num">{esc(c["label"])}</span>'
            f'<span class="toc-title">{esc(c["title"])}</span>'
            f'<span class="toc-dur">{esc(c["dur"])}</span></a>'
        )
        points = "".join(f"<li>{esc(p)}</li>" for p in c["points"])
        transcript = "".join(f"<p>{esc(p)}</p>" for p in paragraphs(os.path.join(ROOT, "scripts", cid + ".txt")))
        cards.append(f"""
      <section class="chapter" id="{cid}">
        <div class="chapter-head">
          <span class="badge">{esc(c['label'])}</span>
          <h2>{esc(c['title'])}</h2>
          <span class="dur">{esc(c['dur'])}</span>
        </div>
        <p class="tagline">{esc(c['tagline'])}</p>
        <audio controls preload="none" src="audio/{cid}.mp3"></audio>
        <p class="summary">{esc(c['summary'])}</p>
        <ul class="points">{points}</ul>
        <details>
          <summary>Read the full chapter</summary>
          <div class="transcript">{transcript}</div>
        </details>
      </section>""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OPERATOR — Command AI in 2026</title>
<meta name="description" content="A 7-chapter audiobook for an operator: how to command AI in 2026 and not get out-computed. Read and listen.">
<style>
  :root {{ --bg:#0b0d10; --panel:#14181d; --panel2:#1b2128; --ink:#e8edf2; --muted:#9aa7b4;
           --accent:#5ad1a0; --accent2:#7aa2ff; --line:#242c34; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }}
  a {{ color:var(--accent2); text-decoration:none; }}
  .wrap {{ max-width:860px; margin:0 auto; padding:0 20px 80px; }}
  header.hero {{ padding:64px 20px 28px; text-align:center; border-bottom:1px solid var(--line);
                 background:radial-gradient(900px 400px at 50% -120px, rgba(90,209,160,.14), transparent); }}
  .hero .kicker {{ color:var(--accent); letter-spacing:.22em; font-size:12px; text-transform:uppercase; margin:0 0 10px; }}
  .hero h1 {{ font-size:42px; line-height:1.1; margin:0 0 12px; letter-spacing:-.02em; }}
  .hero p.sub {{ color:var(--muted); max-width:620px; margin:0 auto; font-size:18px; }}
  .hero .meta {{ margin-top:18px; color:var(--muted); font-size:14px; }}
  .hero .meta b {{ color:var(--ink); }}
  nav.toc {{ margin:28px auto 0; max-width:860px; padding:0 20px; }}
  .toc-grid {{ display:grid; gap:8px; }}
  .toc-item {{ display:grid; grid-template-columns:64px 1fr auto; align-items:center; gap:12px;
               background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:12px 16px; color:var(--ink); }}
  .toc-item:hover {{ border-color:var(--accent); }}
  .toc-num {{ color:var(--accent); font-weight:600; font-size:13px; }}
  .toc-title {{ font-weight:600; }}
  .toc-dur {{ color:var(--muted); font-variant-numeric:tabular-nums; font-size:14px; }}
  .chapter {{ background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:24px; margin:22px 0; scroll-margin-top:18px; }}
  .chapter-head {{ display:flex; align-items:center; gap:12px; flex-wrap:wrap; }}
  .chapter-head h2 {{ margin:0; font-size:26px; letter-spacing:-.01em; flex:1 1 auto; }}
  .badge {{ background:var(--panel2); color:var(--accent); border:1px solid var(--line); border-radius:999px; padding:4px 12px; font-size:12px; font-weight:600; letter-spacing:.04em; }}
  .dur {{ color:var(--muted); font-variant-numeric:tabular-nums; font-size:14px; }}
  .tagline {{ color:var(--ink); font-size:18px; margin:14px 0 16px; }}
  audio {{ width:100%; margin:4px 0 16px; }}
  .summary {{ color:var(--muted); }}
  ul.points {{ margin:14px 0 6px; padding-left:20px; }}
  ul.points li {{ margin:6px 0; }}
  details {{ margin-top:16px; border-top:1px solid var(--line); padding-top:12px; }}
  details > summary {{ cursor:pointer; color:var(--accent2); font-weight:600; list-style:none; }}
  details > summary::-webkit-details-marker {{ display:none; }}
  details > summary::before {{ content:"▸ "; }}
  details[open] > summary::before {{ content:"▾ "; }}
  .transcript {{ margin-top:14px; }}
  .transcript p {{ margin:0 0 14px; color:var(--ink); }}
  footer {{ color:var(--muted); font-size:14px; text-align:center; padding:30px 20px; border-top:1px solid var(--line); }}
  footer code {{ background:var(--panel2); padding:2px 6px; border-radius:6px; }}
</style>
</head>
<body>
  <header class="hero">
    <p class="kicker">An audiobook for an operator</p>
    <h1>OPERATOR</h1>
    <p class="sub">How to command AI in 2026 — and not get out-computed. The machine wins on compute; you win on what to point it at. Read it, or listen to it.</p>
    <p class="meta"><b>{len(CHAPTERS)} chapters</b> &nbsp;·&nbsp; <b>~{total_str}</b> &nbsp;·&nbsp; open-source narration</p>
  </header>
  <nav class="toc"><div class="toc-grid">
    {''.join(toc)}
  </div></nav>
  <main class="wrap">
    {''.join(cards)}
  </main>
  <footer>
    Narrated with open-source TTS (Piper). Built for Jay. &nbsp;·&nbsp;
    Edit a script and rebuild with <code>python src/build_site.py</code>.
  </footer>
</body>
</html>
"""


def main() -> None:
    out = os.path.join(ROOT, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote", os.path.relpath(out, ROOT))


if __name__ == "__main__":
    main()
