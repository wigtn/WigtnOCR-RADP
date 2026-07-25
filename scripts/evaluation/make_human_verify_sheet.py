"""Build a self-contained HTML sheet for BLIND human verification of the KoGov QA.

R1/R3 flag that the 94/100 accept rate was LLM-assisted, so the residual noise in
the reference/answer spans is "unclear". This produces a click-through sheet so a
human grades the SAME 100-QA sample the LLM graded — giving a human vs LLM
agreement number that directly answers the concern.

The grader sees only: question, gold answer_span, and the reference context
(answer_chunk). They do NOT see the parser name or the LLM's verdict (blind).
For each item they mark three axes + accept, exactly the LLM's rubric:
  - question_natural : is the question well-posed / unambiguous?
  - answer_correct   : is the gold answer_span a correct answer to the question?
  - span_located     : does the answer_span actually appear in the context?
  - accept           : overall keep this QA?
Progress autosaves to localStorage; a Download button emits a JSONL to merge back.

Usage:
  python scripts/evaluation/make_human_verify_sheet.py \
      --sample output/human_verify/qa_verification_sample_v1.jsonl \
      --out output/human_verify/verify_sheet.html
Open the HTML in a browser, grade, click Download → verify_human_<name>.jsonl.
Then: python scripts/evaluation/score_human_verify.py (agreement vs LLM).
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def _esc(s: str) -> str:
    return html.escape(s or "")


def build(rows: list[dict]) -> str:
    # Blind: strip the LLM verdict from what the page embeds for grading; keep qa_id
    # only as a hidden key so results can be merged back.
    items = [{
        "qa_id": r["qa_id"],
        "question_type": r.get("question_type", ""),
        "difficulty": r.get("difficulty", ""),
        "question": r.get("question", ""),
        "answer_span": r.get("answer_span", ""),
        "context": r.get("answer_chunk", ""),
    } for r in rows]
    data = json.dumps(items, ensure_ascii=False)
    tmpl = r"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>KoGov QA — 사람 검증 (blind)</title>
<style>
 body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:820px;margin:0 auto;padding:20px;color:#1a2233}
 .bar{position:sticky;top:0;background:#fff;border-bottom:1px solid #ddd;padding:10px 0;display:flex;gap:12px;align-items:center}
 .card{border:1px solid #dfe3ea;border-radius:10px;padding:16px;margin:14px 0}
 .meta{color:#8892a0;font-size:12px;margin-bottom:6px}
 .q{font-weight:500;font-size:14px;margin:6px 0}
 .a{background:#eef6ff;border:1px solid #cfe3ff;border-radius:6px;padding:6px 10px;display:inline-block;margin:6px 0}
 .ctx{background:#f7f8fa;border:1px solid #e6e9ef;border-radius:6px;padding:10px;white-space:pre-wrap;font-size:13px;max-height:240px;overflow:auto}
 .axis{margin:5px 0;font-size:13px;display:flex;align-items:center}
 .axis b{display:inline-block;width:210px;font-weight:500}
 button{cursor:pointer;border:1px solid #cbd2dc;background:#fff;border-radius:5px;padding:2px 10px;margin-right:5px;font-size:12px}
 button.on{background:#2d6cdf;color:#fff;border-color:#2d6cdf}
 .no.on{background:#d9534f;border-color:#d9534f}
 #dl{background:#1c7c3b;color:#fff;border-color:#1c7c3b;padding:8px 16px}
 .note{width:100%;margin-top:6px;border:1px solid #dfe3ea;border-radius:6px;padding:6px}
 .prog{font-weight:600}
</style></head><body>
<div class="bar">
 <span class="prog" id="prog">0 / 0</span>
 <span>채점자명: <input id="grader" placeholder="이름" style="border:1px solid #ccc;border-radius:5px;padding:4px 8px"></span>
 <button id="dl">결과 다운로드 (JSONL)</button>
 <span style="color:#8892a0;font-size:12px">진행은 자동 저장됨</span>
</div>
<p style="color:#556;font-size:13px">각 항목: <b>질문</b>과 <b>정답</b>을 보고, 아래 <b>컨텍스트(원문)</b>에서 그 정답을 확인할 수 있는지 판단해 3축 + 최종 accept를 누르세요. 파서명·기존 판정은 보이지 않습니다(blind).</p>
<div id="root"></div>
<script>
const DATA=__DATA__;
const KEY="kogov_human_verify_v1";
let saved=JSON.parse(localStorage.getItem(KEY)||"{}");
const AX=[["question_natural","질문이 자연스럽고 명확한가?"],["answer_correct","정답이 질문에 맞는가?"],["span_located","정답이 컨텍스트에 실제로 있는가?"],["accept","최종: 이 QA를 채택?"]];
function setv(id,ax,val){saved[id]=saved[id]||{};saved[id][ax]=val;localStorage.setItem(KEY,JSON.stringify(saved));render();}
function setnote(id,v){saved[id]=saved[id]||{};saved[id].notes=v;localStorage.setItem(KEY,JSON.stringify(saved));}
function render(){
 const root=document.getElementById("root");root.innerHTML="";
 let done=0;
 DATA.forEach((it,i)=>{
  const s=saved[it.qa_id]||{};
  if(AX.every(([a])=>s[a]!==undefined))done++;
  const c=document.createElement("div");c.className="card";
  let axh=AX.map(([a,label])=>{
   const cur=s[a];
   return `<div class="axis"><b>${label}</b>`+
     `<button class="${cur===true?'on':''}" onclick="setv('${it.qa_id}','${a}',true)">예</button>`+
     `<button class="no ${cur===false?'on':''}" onclick="setv('${it.qa_id}','${a}',false)">아니오</button></div>`;
  }).join("");
  c.innerHTML=`<div class="meta">#${i+1} · ${it.question_type} · ${it.difficulty}</div>`+
    `<div class="q">Q. ${esc(it.question)}</div>`+
    `<div class="a">정답: ${esc(it.answer_span)}</div>`+
    `<div class="ctx">${esc(it.context)}</div>`+axh+
    `<input class="note" placeholder="메모(선택)" value="${esc(s.notes||'')}" oninput="setnote('${it.qa_id}',this.value)">`;
  root.appendChild(c);
 });
 document.getElementById("prog").textContent=done+" / "+DATA.length;
}
function esc(s){const d=document.createElement("div");d.textContent=s||"";return d.innerHTML;}
document.getElementById("dl").onclick=()=>{
 const g=document.getElementById("grader").value||"anon";
 const lines=DATA.map(it=>{const s=saved[it.qa_id]||{};return JSON.stringify({qa_id:it.qa_id,grader:g,
   question_natural:s.question_natural??null,answer_correct:s.answer_correct??null,
   span_located:s.span_located??null,accept:s.accept??null,notes:s.notes||""});});
 const blob=new Blob([lines.join("\n")],{type:"application/x-jsonlines"});
 const a=document.createElement("a");a.href=URL.createObjectURL(blob);
 a.download="verify_human_"+g+".jsonl";a.click();
};
render();
</script></body></html>"""
    return tmpl.replace("__DATA__", data)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", default="output/human_verify/qa_verification_sample_v1.jsonl")
    ap.add_argument("--out", default="output/human_verify/verify_sheet.html")
    args = ap.parse_args()
    rows = [json.loads(l) for l in Path(args.sample).read_text(encoding="utf-8").splitlines() if l.strip()]
    Path(args.out).write_text(build(rows), encoding="utf-8")
    print(f"wrote {args.out} ({len(rows)} items). Open it in a browser, grade, Download.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
