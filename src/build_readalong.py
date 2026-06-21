#!/usr/bin/env python3
"""
Build a self-contained read-along player.

Re-renders each chapter sentence-by-sentence with Piper so we know the exact start
time of every sentence, interpolates word timing within each sentence, and emits a
single offline HTML file (readalong.html) that:
  - plays each chapter's audio,
  - highlights the current sentence and word as it plays (karaoke style),
  - auto-scrolls and lets you click any word to jump there,
  - shows each chapter's key points as a visual "artifact" card.

Audio (audio/<id>.mp3) is regenerated here so timings line up exactly. Run:
    python src/build_readalong.py
"""
from __future__ import annotations
import html
import json
import os
import re
import subprocess
import tempfile
import wave

from build_site import CHAPTERS  # reuse chapter metadata (title/label/summary/points)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICE = os.path.join(ROOT, "voices", "en-us-ryan-high.onnx")
AUDIO_DIR = os.path.join(ROOT, "audio")
LENGTH_SCALE = 1.45
SENT_GAP = 0.18      # seconds of silence between sentences
PARA_GAP = 0.5       # seconds of silence between paragraphs


def ffmpeg_exe() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def clean(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = text.replace("%", " percent")
    return text.replace("\r", " ")


def paragraphs(raw: str) -> list[str]:
    blocks = [re.sub(r"[ \t]*\n[ \t]*", " ", p.strip())
              for p in re.split(r"\n\s*\n", raw) if p.strip()]
    return blocks[1:] if len(blocks) > 1 else blocks  # drop spoken title line


def split_sentences(para: str) -> list[str]:
    t = re.sub(r"\s+", " ", para).strip()
    # protect common abbreviations and decimals so we don't split on them
    t = re.sub(r"\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|e\.g|i\.e|a\.m|p\.m|U\.S|U\.K)\.",
               lambda m: m.group(0).replace(".", "⊙"), t, flags=re.I)
    t = re.sub(r"(\d)\.(\d)", r"\1⊙\2", t)
    parts = re.findall(r"[^.!?]+[.!?]+(?=\s+[A-Z\"'(]|\s*$)|[^.!?]+$", t)
    out = [p.replace("⊙", ".").strip() for p in parts]
    return [s for s in out if s]


def piper_pcm(voice, text: str) -> tuple[bytes, int]:
    from piper.config import SynthesisConfig
    cfg = SynthesisConfig(length_scale=LENGTH_SCALE)
    pcm = bytearray()
    rate = 22050
    for ch in voice.synthesize(text, syn_config=cfg):
        pcm += ch.audio_int16_bytes
        rate = ch.sample_rate
    return bytes(pcm), rate


def word_times(sentence: str, t0: float, dur: float) -> list[dict]:
    words = sentence.split()
    if not words:
        return []
    weights = [len(w) + 1 for w in words]
    total = sum(weights)
    span = dur * 0.97  # leave a hair at the end
    times, acc = [], 0.0
    for w, wt in zip(words, weights):
        start = t0 + span * (acc / total)
        acc += wt
        end = t0 + span * (acc / total)
        times.append({"w": w, "t": round(start, 3), "d": round(end - start, 3)})
    return times


def render_chapter(voice, chap: dict) -> dict:
    path = os.path.join(ROOT, "scripts", chap["id"] + ".txt")
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    pcm = bytearray()
    rate = 22050
    t = 0.0
    paras_out: list[list[dict]] = []
    for pi, para in enumerate(paragraphs(clean(raw))):
        sents_out: list[dict] = []
        for si, sent in enumerate(split_sentences(para)):
            seg, rate = piper_pcm(voice, sent)
            dur = len(seg) / 2 / rate
            sents_out.append({
                "text": sent,
                "t": round(t, 3),
                "d": round(dur, 3),
                "words": word_times(sent, t, dur),
            })
            pcm += seg
            t += dur
            # gap after sentence
            gap = SENT_GAP
            pcm += b"\x00\x00" * int(rate * gap)
            t += gap
        # extra gap between paragraphs
        extra = PARA_GAP - SENT_GAP
        if extra > 0:
            pcm += b"\x00\x00" * int(rate * extra)
            t += extra
        paras_out.append(sents_out)

    # write wav -> mp3
    os.makedirs(AUDIO_DIR, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wavp = os.path.join(tmp, "c.wav")
        with wave.open(wavp, "w") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
            w.writeframes(bytes(pcm))
        mp3 = os.path.join(AUDIO_DIR, chap["id"] + ".mp3")
        subprocess.run([ffmpeg_exe(), "-y", "-i", wavp, "-codec:a", "libmp3lame",
                        "-b:a", "128k", "-ar", "44100",
                        "-metadata", f"title={chap['title']}", mp3],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  {chap['id']}: {t/60:.1f} min, {sum(len(p) for p in paras_out)} sentences")
    return {
        "id": chap["id"], "label": chap["label"], "title": chap["title"],
        "summary": chap["summary"], "points": chap["points"], "dur": chap["dur"],
        "audio": f"audio/{chap['id']}.mp3", "paras": paras_out,
    }


PAGE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>OPERATOR — Read &amp; Listen</title>
<style>
:root{--bg:#0c0e12;--panel:#151a21;--panel2:#1c232c;--ink:#e9eef3;--muted:#9aa7b4;
--accent:#ffd76a;--accent2:#5ad1a0;--line:#2a333d;--word:#ffd76a;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:17px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header{padding:26px 20px 16px;text-align:center;border-bottom:1px solid var(--line);
background:radial-gradient(700px 280px at 50% -90px,rgba(255,215,106,.12),transparent)}
header h1{margin:0 0 4px;font-size:30px;letter-spacing:-.02em}
header p{margin:0;color:var(--muted);font-size:14px}
.tabs{display:flex;gap:8px;overflow-x:auto;padding:14px 16px;border-bottom:1px solid var(--line);
position:sticky;top:0;background:rgba(12,14,18,.96);backdrop-filter:blur(6px);z-index:5}
.tab{white-space:nowrap;border:1px solid var(--line);background:var(--panel);color:var(--ink);
border-radius:999px;padding:8px 14px;font-size:13px;cursor:pointer}
.tab.active{border-color:var(--accent);color:var(--accent)}
.wrap{max-width:780px;margin:0 auto;padding:18px 18px 140px}
.cardtitle{font-size:24px;font-weight:700;margin:8px 0 2px}
.tagline{color:var(--muted);margin:0 0 14px}
.artifact{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:0 0 22px}
.artifact h3{margin:0 0 10px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent2)}
.artifact ul{margin:0;padding-left:20px}.artifact li{margin:6px 0;color:var(--ink)}
.reader p{margin:0 0 18px}
.s{border-radius:6px;transition:background .12s}
.s.active{background:rgba(255,215,106,.10)}
.w{cursor:pointer;border-radius:5px;padding:0 1px}
.w.active{background:var(--word);color:#1a1407;font-weight:600;box-shadow:0 0 0 2px var(--word)}
.w:hover{background:rgba(255,215,106,.22)}
.bar{position:fixed;left:0;right:0;bottom:0;background:rgba(18,22,28,.97);
border-top:1px solid var(--line);backdrop-filter:blur(8px);padding:10px 14px 14px;z-index:9}
.bar .row{max-width:780px;margin:0 auto;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
audio{flex:1 1 320px;min-width:220px;height:38px}
.bar button,.bar select{background:var(--panel2);color:var(--ink);border:1px solid var(--line);
border-radius:10px;padding:8px 12px;font-size:14px;cursor:pointer}
.bigplay{background:var(--accent);color:#1a1407;border:none;font-weight:700}
.tlabel{color:var(--muted);font-size:12px;font-variant-numeric:tabular-nums}
.hint{max-width:780px;margin:0 auto 14px;color:var(--muted);font-size:13px}
</style></head><body>
<header><h1>OPERATOR</h1><p>Read &amp; listen — the words light up as they're spoken. Tap any word to jump.</p></header>
<div class="tabs" id="tabs"></div>
<div class="wrap">
  <div class="hint" id="hint"></div>
  <div class="cardtitle" id="ctitle"></div>
  <p class="tagline" id="ctag"></p>
  <div class="artifact"><h3>The takeaways</h3><ul id="points"></ul></div>
  <div class="reader" id="reader"></div>
</div>
<div class="bar"><div class="row">
  <button class="bigplay" id="big">▶ Play</button>
  <audio id="audio" controls preload="none"></audio>
  <label class="tlabel">Speed
    <select id="rate"><option>0.85</option><option selected>1</option><option>1.15</option><option>1.3</option><option>1.5</option></select>
  </label>
  <button id="follow">Follow: on</button>
  <span class="tlabel" id="time">0:00</span>
</div></div>
<script>
const BOOK = __DATA__;
const $=id=>document.getElementById(id);
const audio=$('audio'),reader=$('reader'),tabsEl=$('tabs');
let cur=0,wordEls=[],wordList=[],sentEls=[],sentList=[],follow=true,activeW=-1,activeS=-1;

function fmt(t){t=t||0;const m=Math.floor(t/60),s=Math.floor(t%60).toString().padStart(2,'0');return m+':'+s;}

function buildTabs(){
  tabsEl.innerHTML='';
  BOOK.chapters.forEach((c,i)=>{
    const b=document.createElement('button');b.className='tab'+(i===cur?' active':'');
    b.textContent=c.label+' · '+c.title;b.onclick=()=>load(i,true);tabsEl.appendChild(b);
  });
}

function load(i,scrollTop){
  cur=i;buildTabs();
  const c=BOOK.chapters[i];
  $('ctitle').textContent=c.label+' — '+c.title;
  $('ctag').textContent=c.summary;
  $('points').innerHTML=c.points.map(p=>'<li>'+esc(p)+'</li>').join('');
  // build reader with sentence + word spans
  wordEls=[];wordList=[];sentEls=[];sentList=[];
  let html='';let wi=0,sidx=0;
  c.paras.forEach(par=>{
    html+='<p>';
    par.forEach(se=>{
      html+='<span class="s" data-s="'+sidx+'">';
      sentList.push({t:se.t,d:se.d});
      se.words.forEach(w=>{
        html+='<span class="w" data-i="'+wi+'" data-t="'+w.t+'">'+esc(w.w)+'</span> ';
        wordList.push({t:w.t,d:w.d,s:sidx});wi++;
      });
      html+='</span> ';sidx++;
    });
    html+='</p>';
  });
  reader.innerHTML=html;
  wordEls=[...reader.querySelectorAll('.w')];
  sentEls=[...reader.querySelectorAll('.s')];
  wordEls.forEach(el=>el.onclick=()=>{audio.currentTime=parseFloat(el.dataset.t)+0.001;if(audio.paused)audio.play();});
  activeW=-1;activeS=-1;
  audio.src=c.audio;audio.load();
  const key='pos:'+c.id;const saved=parseFloat(localStorage.getItem(key)||'0');
  if(saved>1){audio.addEventListener('loadedmetadata',function r(){audio.currentTime=saved;audio.removeEventListener('loadedmetadata',r);});}
  if(scrollTop)window.scrollTo({top:0,behavior:'smooth'});
}

function hi(){
  const t=audio.currentTime;
  // word: last word whose start <= t
  let lo=0,hi=wordList.length-1,idx=-1;
  while(lo<=hi){const m=(lo+hi)>>1;if(wordList[m].t<=t){idx=m;lo=m+1;}else hi=m-1;}
  if(idx!==activeW){
    if(activeW>=0&&wordEls[activeW])wordEls[activeW].classList.remove('active');
    if(idx>=0&&wordEls[idx]){wordEls[idx].classList.add('active');
      const s=wordList[idx].s;
      if(s!==activeS){
        if(activeS>=0&&sentEls[activeS])sentEls[activeS].classList.remove('active');
        if(sentEls[s]){sentEls[s].classList.add('active');
          if(follow){const r=sentEls[s].getBoundingClientRect();
            if(r.top<90||r.bottom>window.innerHeight-160)sentEls[s].scrollIntoView({block:'center',behavior:'smooth'});}}
        activeS=s;
      }
    }
    activeW=idx;
  }
  $('time').textContent=fmt(t)+' / '+fmt(audio.duration);
}

function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

audio.addEventListener('timeupdate',()=>{hi();const c=BOOK.chapters[cur];localStorage.setItem('pos:'+c.id,audio.currentTime);});
audio.addEventListener('play',()=>$('big').textContent='❚❚ Pause');
audio.addEventListener('pause',()=>$('big').textContent='▶ Play');
$('big').onclick=()=>{audio.paused?audio.play():audio.pause();};
$('rate').onchange=e=>audio.playbackRate=parseFloat(e.target.value);
$('follow').onclick=()=>{follow=!follow;$('follow').textContent='Follow: '+(follow?'on':'off');};
buildTabs();load(0,false);
</script></body></html>
"""


def main() -> None:
    from piper import PiperVoice
    voice = PiperVoice.load(VOICE)
    print("Rendering read-along audio + timing for", len(CHAPTERS), "chapters")
    data = {"title": "OPERATOR", "chapters": [render_chapter(voice, c) for c in CHAPTERS]}
    out = os.path.join(ROOT, "readalong.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(PAGE.replace("__DATA__", json.dumps(data, ensure_ascii=False)))
    size = os.path.getsize(out) / 1024
    print(f"Wrote {os.path.relpath(out, ROOT)} ({size:.0f} KB)")


if __name__ == "__main__":
    main()
