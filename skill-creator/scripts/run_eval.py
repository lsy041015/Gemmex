#!/usr/bin/env python3
"""스킬 설명의 트리거 평가를 실행합니다.

Gemma에게 스킬 설명을 보여주고, 각 쿼리에 대해 해당 스킬을
트리거해야 하는지 직접 판단하게 합니다.
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from google import genai
from google.genai import types

from scripts.api_pool import KeyPool, load_api_keys
from scripts.utils import parse_skill_md

DEFAULT_MODEL = "gemma-4-31b-it"
MAX_RETRIES   = 5
POOL          = KeyPool(load_api_keys())


def _is_rate_limit(e: Exception) -> bool:
    msg = str(e)
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower()


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    model: str,
) -> bool:
    """단일 쿼리에 대해 스킬 트리거 여부를 판단합니다."""
    prompt = (
        f"당신은 AI 어시스턴트입니다. 현재 다음 스킬을 사용할 수 있습니다.\n\n"
        f"스킬명: {skill_name}\n"
        f"설명: {skill_description}\n\n"
        f"---\n\n"
        f"사용자 쿼리: \"{query}\"\n\n"
        f"이 쿼리를 받았을 때 위 스킬을 활성화(트리거)해야 합니까?\n"
        f"스킬 설명과 사용자의 의도를 비교하여 판단하세요.\n"
        f"반드시 \"예\" 또는 \"아니오\"로만 답하세요. 다른 말은 하지 마세요."
    )

    for attempt in range(MAX_RETRIES):
        key, key_idx = POOL.get()
        try:
            response = genai.Client(api_key=key).models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=10,
                ),
            )
            text = (response.text or "").strip().lower()
            return text.startswith("예") or text.startswith("yes")
        except Exception as e:
            if _is_rate_limit(e) and attempt < MAX_RETRIES - 1:
                POOL.block(key_idx)
                avail = POOL.available()
                wait  = 2.0 if avail > 0 else 4.0 * (2 ** attempt)
                print(f"경고: 429 — {POOL.status()}, {wait:.0f}초 후 재시도", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"경고: 쿼리 실행 오류 — {e}", file=sys.stderr)
                return False
    return False


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int = 3,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
    **kwargs,  # timeout, project_root 등 호환성 인자 수용
) -> dict:
    """전체 eval 셋을 실행하고 결과를 반환합니다."""
    _model = model or DEFAULT_MODEL

    query_triggers: dict[str, list[bool]] = {}
    query_items: dict[str, dict]          = {}

    with ThreadPoolExecutor(max_workers=min(num_workers, 5)) as executor:
        future_to_info: dict = {}
        for item in eval_set:
            for _ in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    description,
                    _model,
                )
                future_to_info[future] = item

        for future in as_completed(future_to_info):
            item  = future_to_info[future]
            query = item["query"]
            query_items.setdefault(query, item)
            query_triggers.setdefault(query, [])
            try:
                query_triggers[query].append(future.result())
            except Exception as e:
                print(f"경고: 쿼리 실패 — {e}", file=sys.stderr)
                query_triggers[query].append(False)

    results = []
    for query, triggers in query_triggers.items():
        item           = query_items[query]
        trigger_rate   = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        did_pass       = (trigger_rate >= trigger_threshold) if should_trigger else (trigger_rate < trigger_threshold)
        results.append({
            "query":          query,
            "should_trigger": should_trigger,
            "trigger_rate":   trigger_rate,
            "triggers":       sum(triggers),
            "runs":           len(triggers),
            "pass":           did_pass,
        })

    passed = sum(1 for r in results if r["pass"])
    total  = len(results)

    return {
        "skill_name":  skill_name,
        "description": description,
        "results":     results,
        "summary": {
            "total":  total,
            "passed": passed,
            "failed": total - passed,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="스킬 설명 트리거 평가 실행")
    parser.add_argument("--eval-set",          required=True,               help="eval 셋 JSON 파일 경로")
    parser.add_argument("--skill-path",         required=True,               help="스킬 디렉토리 경로")
    parser.add_argument("--description",        default=None,                help="테스트할 설명 (없으면 SKILL.md에서 읽기)")
    parser.add_argument("--num-workers",        type=int,   default=3,       help="병렬 워커 수 (기본값: 3)")
    parser.add_argument("--runs-per-query",     type=int,   default=3,       help="쿼리당 실행 횟수")
    parser.add_argument("--trigger-threshold",  type=float, default=0.5,     help="트리거 판단 임계값")
    parser.add_argument("--model",              default=DEFAULT_MODEL,       help=f"사용할 Gemma 모델 (기본값: {DEFAULT_MODEL})")
    parser.add_argument("--verbose",            action="store_true",         help="진행 상황 출력")
    args = parser.parse_args()

    eval_set   = json.loads(Path(args.eval_set).read_text())
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"오류: SKILL.md를 찾을 수 없습니다: {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, _ = parse_skill_md(skill_path)
    description = args.description or original_description

    if args.verbose:
        print(f"평가 중: {description[:80]}", file=sys.stderr)

    output = run_eval(
        eval_set         = eval_set,
        skill_name       = name,
        description      = description,
        num_workers      = args.num_workers,
        runs_per_query   = args.runs_per_query,
        trigger_threshold= args.trigger_threshold,
        model            = args.model,
    )

    if args.verbose:
        s = output["summary"]
        print(f"결과: {s['passed']}/{s['total']} 통과", file=sys.stderr)
        for r in output["results"]:
            status   = "통과" if r["pass"] else "실패"
            rate_str = f"{r['triggers']}/{r['runs']}"
            print(f"  [{status}] rate={rate_str} 예상={r['should_trigger']}: {r['query'][:70]}", file=sys.stderr)

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
