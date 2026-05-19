---
name: skill-creator
description: >
  새 스킬을 만들거나, 기존 스킬을 수정·개선하거나, 스킬 성능을 측정할 때
  사용합니다. 사용자가 스킬을 처음부터 만들거나, 기존 스킬을 편집·최적화하거나,
  평가(eval)를 실행해 스킬을 테스트하거나, 벤치마크를 측정하거나, 트리거 정확도를
  높이기 위해 스킬 설명을 최적화하려 할 때 활용합니다.
---

## 역할

사용자가 이 과정의 어느 단계에 있는지 파악하고 적절한 지점에서 진행을 도웁니다.
"스킬을 만들고 싶다" → 의도 파악 → 초안 작성 → 테스트 → 반복.
이미 초안이 있으면 eval/반복 단계로 바로 진입합니다.

---

## 스킬 구조

```
skills/skill-name/
├── SKILL.md          필수. YAML 프론트매터(name, description) + 지침
└── (선택)
    ├── scripts/      반복 작업용 실행 코드
    ├── references/   필요 시 로드되는 문서
    └── assets/       템플릿, 폰트 등
```

**SKILL.md 프론트매터 필수 필드:**
- `name`: kebab-case 식별자 (최대 64자)
- `description`: 트리거 조건 + 역할 요약 (최대 1024자). **이것이 트리거 메커니즘** — "무엇을 할 때 쓰는지" 전부를 여기에 담습니다.

> Gemma는 스킬을 덜 트리거하는 경향이 있으므로 description을 조금 "적극적으로" 작성합니다.

---

## 스킬 만들기 순서

### 1. 의도 파악

확인할 사항:
- 이 스킬이 Gemma에게 무엇을 가능하게 해야 하는가?
- 언제 트리거되어야 하는가?
- 예상 출력 형식은?

### 2. 인터뷰 및 리서치

엣지 케이스, 입출력 형식, 성공 기준을 질문합니다.
`read_file`, `find_files`, `search_in_files`로 관련 문서·유사 스킬을 조사합니다.

### 3. SKILL.md 작성

인터뷰를 바탕으로 `skills/<name>/SKILL.md`를 작성합니다.
지시사항은 명령형으로 작성하고, MUST/NEVER 대신 이유를 설명합니다.

### 4. 테스트 케이스 작성

2-3개의 현실적인 테스트 프롬프트를 `evals/evals.json`에 저장합니다:

```json
{
  "skill_name": "example-skill",
  "evals": [
    {"id": 1, "prompt": "사용자 작업 프롬프트", "expected_output": "예상 결과", "files": []}
  ]
}
```

---

## 테스트 케이스 실행 및 평가

결과는 `<skill-name>-workspace/iteration-N/eval-<ID>/with_skill/`에 저장합니다.

### 1단계: 어서션 초안 작성

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name",
  "prompt": "작업 프롬프트",
  "assertions": [
    {"text": "출력 파일이 생성됐는가", "passed": false, "evidence": ""}
  ]
}
```

### 2단계: 순차 실행

한 번에 하나씩 직접 수행합니다. `read_file`로 스킬 지침을 확인하고 작업을 완수합니다.
시작·종료 시각을 기록합니다:

```python
from datetime import datetime
started_at = datetime.now().isoformat()
# ... 작업 ...
finished_at = datetime.now().isoformat()
```

이전 반복(`iteration-N-1/`)이 있으면 비교 기준으로 활용합니다.

### 3단계: 채점

완료 즉시 인라인으로 채점하고 `grading.json` 저장:

```json
{
  "summary": {"passed": 2, "failed": 1, "total": 3, "pass_rate": 0.67},
  "expectations": [
    {"text": "출력 파일 생성", "passed": true,  "evidence": "output.csv 확인"},
    {"text": "빈 행 없음",     "passed": false, "evidence": "3번째 행 빈 줄"}
  ],
  "timing": {"started_at": "...", "finished_at": "...", "duration_seconds": 45.0}
}
```

### 4단계: 집계 및 정적 뷰어 생성

```bash
python3 -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>

python3 skills/skill-creator/eval-viewer/generate_review.py \
  <workspace>/iteration-N \
  --skill-name "my-skill" \
  --benchmark <workspace>/iteration-N/benchmark.json \
  --static /tmp/review_<skill>_iter<N>.html
```

반복 2 이상에서는 `--previous-workspace <workspace>/iteration-<N-1>` 추가.

### 5단계: 피드백 수집

결과를 TUI 대화에서 직접 제시하고 인라인으로 피드백을 받습니다.

---

## 스킬 개선

- **피드백에서 일반화**: 지금 보이는 몇 가지 예시에만 맞는 스킬은 무용합니다.
- **프롬프트를 간결하게**: 효과 없는 요소는 제거합니다.
- **이유를 설명**: ALWAYS/NEVER 대신 왜 중요한지 설명합니다.
- **반복 작업 찾기**: 여러 eval에서 같은 코드를 반복 작성하면 스킬 번들에 포함합니다.

**반복 루프:**
1. 스킬 개선사항 적용 (`write_file`로 저장)
2. `iteration-<N+1>/`에서 재실행
3. `--previous-workspace`로 비교 뷰어 생성
4. 피드백 수집 → 반복

**종료 조건:** 사용자가 만족 / 피드백이 모두 빔 / 의미 있는 진전 없음

---

## 설명 최적화

### 1단계: eval 쿼리 생성 (20개)

```json
[
  {"query": "사용자 프롬프트", "should_trigger": true},
  {"query": "다른 프롬프트",   "should_trigger": false}
]
```

should-not-trigger는 명백히 무관한 것 말고, 키워드는 비슷하지만 다른 것이 필요한 **근접 미스**를 만드세요.

### 2단계: eval_review.html로 사용자와 검토

```python
# assets/eval_review.html 읽어서 플레이스홀더 교체 후 저장
html = read_file("skills/skill-creator/assets/eval_review.html")
html = html.replace("__EVAL_DATA_PLACEHOLDER__", json.dumps(eval_data))
html = html.replace("__SKILL_NAME_PLACEHOLDER__", skill_name)
html = html.replace("__SKILL_DESCRIPTION_PLACEHOLDER__", description)
write_file("/tmp/eval_review_<skill>.html", html)
```

### 3단계: 수동 최적화

eval 쿼리를 직접 Gemma에 입력해 트리거 여부 확인 → 실패 패턴 파악 → description 수정 → 반복.

---

## 패키징

```bash
python3 -m scripts.package_skill skills/<skill-name>/
```

---

> 고급 지침(블라인드 비교, analyzer 패스, 전체 워크플로우 상세):
> `read_file("skills/skill-creator/skill.md")`
