"""Blind human-verification sheet for L1-absent cases (P/D/A adjudication).

Builds a 100-case blind sheet per `docs/ADJUDICATION_absent_criteria.md`:
MinerU table-ON 50 + Prod 30 + PaddleOCR 20, sampled with a fixed seed from each
parser's L1-absent set (the paper's matcher, `absent_matchers.l1_normalized`),
shuffled, parser names stripped. The grader sees: page image, question, gold
answer span, and the parser's page markdown; they mark P(resent) / D(egraded) /
A(bsent) + memo. `answer_key.json` (case_id -> parser, qa_id) is written
separately and MUST NOT be shared with graders.

Determinism: per-parser sampling uses `Random(f"{seed}|{parser}")` over the
qa_id-sorted absent frame; slot order uses `Random(f"{seed}|shuffle")` over the
fixed slot template — so case_ids and the MinerU picks are stable across re-runs,
and pending parsers fill in later WITHOUT renumbering existing cases.

A parser with no usable local predictions (e.g. 0-byte stub copies, <90%
non-empty) gets placeholder rows marked "WSL predictions 도착 후 채움" unless
`--absent-list NAME=json` supplies its L1-absent qa_ids (e.g. extracted from the
WSL `absent_llm_judge_cache.jsonl`); page markdown still requires predictions.

Usage (local, MinerU table-ON only):
    .venv/bin/python scripts/analysis/make_absent_blind_sheet.py

Usage (WSL, all three filled):
    uv run python scripts/analysis/make_absent_blind_sheet.py \
        --parser-dir Prod=/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/v1_val/predictions \
        --parser-dir PaddleOCR=/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/paddleocr_val/predictions
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import random
from pathlib import Path

from wigtnocr_radp.evaluation.absent_matchers import LADDER
from wigtnocr_radp.evaluation.parser_outputs import load_parser_outputs
from wigtnocr_radp.evaluation.rcps import load_qa_pairs

SEED = 42
# (blind-internal name, sample size, default predictions dir)
PLAN = [
    ("MinerU-tableON", 50, "results/kogovdoc/mineru_val_tableon/predictions"),
    ("Prod", 30, "/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/v1_val/predictions"),
    ("PaddleOCR", 20, "/mnt/data1/work/wigtnOCR-v1/results/kogovdoc/paddleocr_val/predictions"),
]
MIN_NONEMPTY_FRAC = 0.9  # below this the dir is treated as a stub copy, not real output


def image_rel_path(image_abs: str, images_root: Path, out_dir: Path) -> str:
    """Map a val.jsonl image path to a path relative to the sheet's directory."""
    sub = image_abs.split("/images/", 1)[1]
    return os.path.relpath((images_root / sub).resolve(), out_dir.resolve())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--qa", default="data/KoGovDoc-RAG/qa_pairs_v1.jsonl")
    ap.add_argument("--val", default="data/KoGovDoc-Bench/val.jsonl")
    ap.add_argument("--images-root", type=Path, default=Path("data/KoGovDoc-Bench/images"))
    ap.add_argument("--out-dir", type=Path, default=Path("output/human_verify"))
    ap.add_argument("--parser-dir", action="append", default=[], metavar="NAME=DIR",
                    help="override a parser's predictions dir")
    ap.add_argument("--absent-list", action="append", default=[], metavar="NAME=JSON",
                    help="qa_id list for a parser whose predictions are unavailable")
    ap.add_argument("--embed-images", action="store_true",
                    help="inline page images as base64 data URIs — the sheet becomes "
                         "location-independent (larger file, good for handing to graders)")
    args = ap.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    dir_override = dict(s.split("=", 1) for s in args.parser_dir)
    list_override = dict(s.split("=", 1) for s in args.absent_list)

    qa_pairs = load_qa_pairs(args.qa)
    qa_by_id = {qa.qa_id: qa for qa in qa_pairs}
    l1 = LADDER["L1_normalized"]

    # page_id -> image path (from val.jsonl)
    page_image: dict[str, str] = {}
    with Path(args.val).open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if line.strip():
                page_image[f"val_{i:04d}"] = json.loads(line)["images"][0]

    # -- per-parser absent frame + sample ------------------------------------
    samples: dict[str, list[str]] = {}   # parser -> sampled qa_ids (or [] if pending)
    pages_by_parser: dict[str, dict[str, str]] = {}
    manifest: dict[str, dict] = {}

    for name, n, default_dir in PLAN:
        pdir = Path(dir_override.get(name, default_dir))
        pages: dict[str, str] = {}
        usable = False
        if pdir.is_dir():
            pages = load_parser_outputs(pdir, args.val)
            nonempty = sum(1 for v in pages.values() if v.strip())
            usable = bool(pages) and nonempty / len(pages) >= MIN_NONEMPTY_FRAC
            if pages and not usable:
                print(f"[{name}] {pdir}: {nonempty}/{len(pages)} non-empty — "
                      f"treating as stub copy, NOT computing absent from it")
        pages_by_parser[name] = pages if usable else {}

        if usable:
            frame = sorted(
                qa.qa_id for qa in qa_pairs
                if not (pages.get(qa.page_id) and l1(qa.answer_span, pages[qa.page_id]))
            )
        elif name in list_override:
            frame = sorted(json.loads(Path(list_override[name]).read_text()))
        else:
            frame = []

        if frame:
            rng = random.Random(f"{SEED}|{name}")
            samples[name] = rng.sample(frame, min(n, len(frame)))
        else:
            samples[name] = []
        manifest[name] = {
            "predictions_dir": str(pdir), "dir_usable": usable,
            "absent_frame_size": len(frame) if frame else None,
            "sampled": len(samples[name]), "planned": n,
            "sampled_qa_ids": samples[name],
        }
        print(f"[{name}] frame={len(frame) or 'PENDING'} sampled={len(samples[name])}/{n}")

    # -- fixed slot template, deterministic shuffle --------------------------
    slots = [(name, i) for name, n, _ in PLAN for i in range(n)]
    random.Random(f"{SEED}|shuffle").shuffle(slots)

    cases, key = [], {}
    for case_id, (name, i) in enumerate(slots, 1):
        qa_id = samples[name][i] if i < len(samples[name]) else None
        key[str(case_id)] = {"parser": name, "qa_id": qa_id,
                             "status": "filled" if qa_id else "pending"}
        if qa_id:
            qa = qa_by_id[qa_id]
            page_md = pages_by_parser[name].get(qa.page_id, "")
            if args.embed_images:
                sub = page_image[qa.page_id].split("/images/", 1)[1]
                img_path = args.images_root / sub
                if not img_path.exists() and img_path.suffix == ".png":
                    # allow a pre-compressed .jpg mirror (sheet-size control)
                    alt = img_path.with_suffix(".jpg")
                    if alt.exists():
                        img_path = alt
                mime = mimetypes.guess_type(img_path.name)[0] or "image/png"
                b64 = base64.b64encode(img_path.read_bytes()).decode()
                img_src = f"data:{mime};base64,{b64}"
            else:
                img_src = image_rel_path(page_image[qa.page_id], args.images_root, out_dir)
            cases.append({
                "case_id": case_id,
                "image": img_src,
                "question": qa.question, "answer_span": qa.answer_span,
                "parser_output": page_md or "(이 파서는 이 페이지 출력을 내지 못함 — 빈 출력)",
                "pending": False,
            })
        else:
            cases.append({"case_id": case_id, "image": "", "question": "",
                          "answer_span": "", "parser_output": "", "pending": True})

    # -- outputs -------------------------------------------------------------
    (out_dir / "answer_key.json").write_text(
        json.dumps({"seed": SEED, "key": key}, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "sampling_manifest.json").write_text(
        json.dumps({"seed": SEED, "parsers": manifest}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    # <-escape so parser output containing "</script>" cannot break the inline block
    data_js = json.dumps(cases, ensure_ascii=False).replace("<", "\\u003c")
    (out_dir / "verification_sheet.html").write_text(
        SHEET_TMPL.replace("__DATA__", data_js), encoding="utf-8")
    filled = sum(1 for c in cases if not c["pending"])
    print(f"wrote {out_dir}/verification_sheet.html ({filled}/{len(cases)} filled), "
          f"answer_key.json (검수자 비공개), sampling_manifest.json")
    return 0


SHEET_TMPL = r"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>Absent 판정 사람 검증 (blind)</title>
<style>
 body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a2233}
 .bar{position:sticky;top:0;background:#fff;border-bottom:1px solid #ddd;padding:10px 16px;display:flex;gap:14px;align-items:center;z-index:5}
 .prog{font-weight:600}
 .rubric{background:#f7f8fa;border:1px solid #e6e9ef;border-radius:8px;margin:12px 16px;padding:10px 14px;font-size:13px}
 .wrap{display:flex;gap:14px;padding:0 16px 16px;height:calc(100vh - 210px)}
 .pane{flex:1;overflow:auto;border:1px solid #dfe3ea;border-radius:10px;padding:12px}
 .pane img{max-width:100%}
 .q{font-weight:500;margin:6px 0}
 .a{background:#eef6ff;border:1px solid #cfe3ff;border-radius:6px;padding:6px 10px;display:inline-block;margin:6px 0}
 pre{white-space:pre-wrap;font-size:12.5px;line-height:1.45;margin:0}
 .judge{padding:10px 16px;display:flex;gap:10px;align-items:center;border-top:1px solid #eee}
 .judge button.opt{font-size:14px;padding:8px 18px;border-radius:6px;border:1px solid #cbd2dc;background:#fff;cursor:pointer}
 .judge button.on{background:#2d6cdf;color:#fff;border-color:#2d6cdf}
 .judge input{flex:1;border:1px solid #dfe3ea;border-radius:6px;padding:8px}
 .nav button{padding:6px 14px;border-radius:6px;border:1px solid #cbd2dc;background:#fff;cursor:pointer}
 #dl{background:#1c7c3b;color:#fff;border-color:#1c7c3b}
 .pending{color:#a33;font-weight:600;padding:40px;text-align:center}
</style></head><body>
<div class="bar">
 <span class="nav"><button onclick="go(-1)">◀ 이전</button> <button onclick="go(1)">다음 ▶</button></span>
 <span class="prog" id="prog"></span>
 <span>검수자: <input id="grader" placeholder="이름" style="border:1px solid #ccc;border-radius:5px;padding:4px 8px"></span>
 <button id="dl">결과 다운로드 (JSON)</button>
 <span style="color:#8892a0;font-size:12px">진행 자동 저장</span>
</div>
<div class="rubric"><b>판정 기준 (docs/ADJUDICATION_absent_criteria.md):</b>
 <b>P</b>(present) = 질문이 묻는 사실이 파서 출력에 있고, 표기가 달라도 검색으로 찾을 수 있는 형태 ·
 <b>D</b>(degraded) = 글자는 있으나 값이 행/헤더와 분리·훼손·파편화되어 검색 불가 ·
 <b>A</b>(absent) = 내용 자체가 출력에 없음.
 P/D 사이에서 애매하면 <b>P</b>를 선택(보수적 방향). 왼쪽 = 원본 페이지 이미지, 오른쪽 = 파서 출력 전문.</div>
<div id="case"></div>
<script>
const DATA=__DATA__;
const KEY="absent_blind_v1";
let saved=JSON.parse(localStorage.getItem(KEY)||"{}");
let cur=parseInt(localStorage.getItem(KEY+"_pos")||"0");
function esc(s){const d=document.createElement("div");d.textContent=s||"";return d.innerHTML;}
function save(){localStorage.setItem(KEY,JSON.stringify(saved));localStorage.setItem(KEY+"_pos",cur);}
function setj(id,v){saved[id]=saved[id]||{};saved[id].judgment=v;save();render();}
function setm(id,v){saved[id]=saved[id]||{};saved[id].memo=v;save();}
function go(d){
 let i=cur;
 do{i=Math.min(Math.max(i+d,0),DATA.length-1);}while(DATA[i].pending&&i>0&&i<DATA.length-1);
 if(!DATA[i].pending)cur=i;
 save();render();}
function render(){
 const it=DATA[cur], s=saved[it.case_id]||{};
 const done=DATA.filter(c=>!c.pending&&(saved[c.case_id]||{}).judgment).length;
 const fillable=DATA.filter(c=>!c.pending).length;
 document.getElementById("prog").textContent=`case ${cur+1}/${DATA.length} — 판정 ${done}/${fillable}`;
 const el=document.getElementById("case");
 if(it.pending){
  el.innerHTML=`<div class="pending">case #${it.case_id} — WSL predictions 도착 후 채움 (자리 예약)</div>`;
  return;
 }
 el.innerHTML=
  `<div style="padding:8px 16px"><span class="q">Q. ${esc(it.question)}</span> &nbsp;`+
  `<span class="a">정답 span: ${esc(it.answer_span)}</span></div>`+
  `<div class="wrap"><div class="pane"><img src="${it.image}" alt="page"></div>`+
  `<div class="pane"><pre>${esc(it.parser_output)}</pre></div></div>`+
  `<div class="judge">`+
  ["P","D","A"].map(v=>`<button class="opt ${s.judgment===v?'on':''}" onclick="setj(${it.case_id},'${v}')">${v}</button>`).join("")+
  `<input placeholder="메모(선택)" value="${esc(s.memo||'')}" oninput="setm(${it.case_id},this.value)"></div>`;
}
document.getElementById("dl").onclick=()=>{
 const g=document.getElementById("grader").value||"anon";
 const rows=DATA.filter(c=>!c.pending).map(c=>{const s=saved[c.case_id]||{};
  return {case_id:c.case_id,grader:g,judgment:s.judgment||null,memo:s.memo||""};});
 const blob=new Blob([JSON.stringify(rows,null,1)],{type:"application/json"});
 const a=document.createElement("a");a.href=URL.createObjectURL(blob);
 a.download="absent_blind_"+g+".json";a.click();
};
document.addEventListener("keydown",e=>{if(e.key==="ArrowLeft")go(-1);if(e.key==="ArrowRight")go(1);});
render();
</script></body></html>"""


if __name__ == "__main__":
    raise SystemExit(main())
