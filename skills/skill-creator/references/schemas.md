# JSON 스키마 정의

skill-creator에서 사용하는 JSON 파일 구조를 정의합니다.

> **Gemma TUI 환경 참고**
> - 파일 저장: `write_file` 도구 사용 (사용자 확인 후 저장)
> - 파일 읽기: `read_file` 도구 사용
> - 서브에이전트 없음: 모든 작업을 Gemma가 직접 순차 수행
> - 베이스라인 비교(`without_skill`) 미지원: `with_skill` 단독 평가

---

## evals.json

스킬의 eval을 정의합니다. 스킬 디렉토리 내 `evals/evals.json`에 위치합니다.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "사용자의 예시 프롬프트",
      "expected_output": "성공 기준에 대한 사람이 읽을 수 있는 설명",
      "files": ["evals/files/sample1.pdf"],
      "expectations": [
        "출력에 X가 포함되어 있음",
        "스킬이 스크립트 Y를 사용했음"
      ]
    }
  ]
}
```

**필드 설명:**
- `skill_name`: 스킬 프론트매터의 name과 일치해야 함
- `evals[].id`: 고유한 정수 식별자
- `evals[].prompt`: 실행할 태스크
- `evals[].expected_output`: 성공 기준 설명 (사람이 읽는 용도)
- `evals[].files`: 입력 파일 경로 목록 (스킬 루트 기준 상대 경로, 선택)
- `evals[].expectations`: 검증 가능한 어서션 목록

---

## history.json

반복 개선 과정의 버전 이력을 추적합니다. 워크스페이스 루트에 위치합니다.

```json
{
  "started_at": "2026-01-15T10:30:00+09:00",
  "skill_name": "example-skill",
  "current_best": "v2",
  "iterations": [
    {
      "version": "v0",
      "parent": null,
      "expectation_pass_rate": 0.65,
      "grading_result": "baseline",
      "is_current_best": false
    },
    {
      "version": "v1",
      "parent": "v0",
      "expectation_pass_rate": 0.75,
      "grading_result": "improved",
      "is_current_best": false
    },
    {
      "version": "v2",
      "parent": "v1",
      "expectation_pass_rate": 0.85,
      "grading_result": "improved",
      "is_current_best": true
    }
  ]
}
```

**필드 설명:**
- `started_at`: 개선 시작 시각 (ISO 8601, 한국 시간대 `+09:00`)
- `skill_name`: 개선 중인 스킬 이름
- `current_best`: 현재 최고 성능 버전 식별자
- `iterations[].version`: 버전 식별자 (v0, v1, ...)
- `iterations[].parent`: 이 버전이 파생된 부모 버전
- `iterations[].expectation_pass_rate`: 채점 결과의 통과율
- `iterations[].grading_result`: `"baseline"`, `"improved"`, `"regressed"`, `"tie"` 중 하나
- `iterations[].is_current_best`: 현재 최고 버전 여부

> **Gemma TUI 참고:** 서브에이전트 비교(won/lost)가 없으므로 `grading_result`는 이전 버전 대비 통과율 변화로 판단합니다.

---

## grading.json

채점기(`grader.md`) 실행 결과입니다. `<실행-디렉토리>/grading.json`에 위치합니다.

```json
{
  "expectations": [
    {
      "text": "출력에 'John Smith'라는 이름이 포함되어 있음",
      "passed": true,
      "evidence": "출력 파일 3번째 줄: '이름: John Smith, 연락처: ...' 확인됨"
    },
    {
      "text": "스프레드시트의 B10 셀에 SUM 수식이 있음",
      "passed": false,
      "evidence": "스프레드시트가 생성되지 않음. 출력이 텍스트 파일로 저장됨."
    }
  ],
  "summary": {
    "passed": 1,
    "failed": 1,
    "total": 2,
    "pass_rate": 0.50
  },
  "execution_metrics": {
    "tool_calls": {
      "read_file": 5,
      "write_file": 2,
      "list_dir": 3,
      "find_files": 1,
      "search_in_files": 0,
      "code_exec": 4
    },
    "total_tool_calls": 15,
    "errors_encountered": 0,
    "output_chars": 12450
  },
  "timing": {
    "started_at": "2026-01-15T10:30:00+09:00",
    "finished_at": "2026-01-15T10:32:45+09:00",
    "duration_seconds": 165.0,
    "input_tokens": 4200,
    "output_tokens": 1850
  },
  "claims": [
    {
      "claim": "폼에 12개의 채울 수 있는 필드가 있음",
      "type": "factual",
      "verified": true,
      "evidence": "field_info.json에서 12개 필드 직접 확인됨"
    },
    {
      "claim": "모든 필수 필드가 채워졌음",
      "type": "quality",
      "verified": false,
      "evidence": "데이터가 있음에도 참조 섹션이 비어 있음"
    }
  ],
  "user_notes_summary": {
    "uncertainties": ["2023년 데이터 사용 — 오래된 정보일 수 있음"],
    "needs_review": [],
    "workarounds": ["채울 수 없는 필드에 텍스트 오버레이로 대체 처리"]
  },
  "eval_feedback": {
    "suggestions": [
      {
        "assertion": "출력에 'John Smith'라는 이름이 포함되어 있음",
        "reason": "이름을 언급하는 환각된 문서도 통과할 수 있음"
      }
    ],
    "overall": "어서션이 존재 여부는 확인하지만 정확성은 확인하지 않음."
  }
}
```

**필드 설명:**
- `expectations[]`: 근거와 함께 채점된 어서션 목록
- `summary`: 통과/실패 집계
- `execution_metrics`: 도구 사용 현황 및 출력 크기
  - `tool_calls`: Gemma TUI 도구별 호출 횟수
  - `output_chars`: 출력 파일의 총 문자 수
- `timing`: 실행 시간 및 토큰 사용량
  - `input_tokens` / `output_tokens`: run_gemma.py 대화창의 토큰 카운터에서 확인
- `claims[]`: 출력에서 추출하여 검증한 암묵적 주장
- `user_notes_summary`: 실행 중 발견한 문제점 (파일이 없으면 생략)
- `eval_feedback`: eval 개선 제안 (필요한 경우에만 포함)

---

## metrics.json

실행 과정의 도구 사용 메트릭입니다. `<실행-디렉토리>/outputs/metrics.json`에 위치합니다.

```json
{
  "tool_calls": {
    "read_file": 5,
    "write_file": 2,
    "list_dir": 3,
    "find_files": 1,
    "search_in_files": 0,
    "code_exec": 4
  },
  "total_tool_calls": 15,
  "files_created": ["filled_form.pdf", "field_values.json"],
  "errors_encountered": 0,
  "output_chars": 12450
}
```

**필드 설명:**
- `tool_calls`: Gemma TUI 도구별 호출 횟수
  - `read_file`: 파일 읽기
  - `write_file`: 파일 쓰기
  - `list_dir`: 디렉토리 목록 조회
  - `find_files`: 파일 패턴 검색
  - `search_in_files`: 파일 내 키워드 검색
  - `code_exec`: Python/Bash 코드 실행
- `total_tool_calls`: 전체 도구 호출 수의 합계
- `files_created`: 생성된 출력 파일 목록
- `errors_encountered`: 실행 중 발생한 오류 수
- `output_chars`: 출력 파일의 총 문자 수 (토큰의 간접 지표)

---

## timing.json

실행 시간 기록입니다. `<실행-디렉토리>/timing.json`에 위치합니다.

**기록 방법:** 실행 시작 전후에 시각을 기록하고, 대화창에 표시된 토큰 수를 함께 저장합니다. run_gemma.py는 각 응답 후 `토큰: 입력 X / 출력 X (누적 X / X)` 형식으로 토큰을 출력합니다.

```json
{
  "started_at": "2026-01-15T10:30:00+09:00",
  "finished_at": "2026-01-15T10:32:45+09:00",
  "duration_seconds": 165.0,
  "input_tokens": 4200,
  "output_tokens": 1850,
  "total_tokens": 6050
}
```

**필드 설명:**
- `started_at`: 실행 시작 시각 (ISO 8601, 한국 시간대 `+09:00`)
- `finished_at`: 실행 완료 시각
- `duration_seconds`: 총 소요 시간 (초)
- `input_tokens`: 입력 토큰 수 (run_gemma.py 토큰 카운터 기준)
- `output_tokens`: 출력 토큰 수
- `total_tokens`: 입출력 토큰 합계

> **Gemma TUI 참고:** 서브에이전트가 없으므로 executor/grader 구분 없이 단일 실행 시간만 기록합니다.

---

## benchmark.json

벤치마크 실행 결과입니다. `<워크스페이스>/iteration-N/benchmark.json`에 위치합니다.

```json
{
  "metadata": {
    "skill_name": "example-skill",
    "skill_path": "/home/wego/Gemma_ws/skill-creator/skills/example-skill",
    "model": "gemma-4-31b-it",
    "timestamp": "2026-01-15T10:30:00+09:00",
    "evals_run": [1, 2, 3]
  },

  "runs": [
    {
      "eval_id": 1,
      "eval_name": "기본 동작 테스트",
      "configuration": "with_skill",
      "result": {
        "pass_rate": 0.85,
        "passed": 6,
        "failed": 1,
        "total": 7,
        "duration_seconds": 42.5,
        "input_tokens": 3200,
        "output_tokens": 600,
        "errors": 0
      },
      "expectations": [
        {"text": "출력에 이름이 포함되어 있음", "passed": true, "evidence": "..."}
      ],
      "notes": [
        "2023년 데이터 사용 — 오래된 정보일 수 있음"
      ]
    }
  ],

  "run_summary": {
    "with_skill": {
      "pass_rate": {"mean": 0.85, "stddev": 0.05, "min": 0.80, "max": 0.90},
      "duration_seconds": {"mean": 45.0, "stddev": 12.0, "min": 32.0, "max": 58.0},
      "total_tokens": {"mean": 3800, "stddev": 400, "min": 3200, "max": 4100}
    }
  },

  "notes": [
    "어서션 '출력이 PDF 파일임'이 100% 통과 — 변별력이 없을 수 있음",
    "Eval 3이 높은 분산(50% ± 40%) — 불안정한 동작이거나 모델 의존적일 수 있음"
  ]
}
```

**필드 설명:**
- `metadata`: 벤치마크 실행 정보
  - `model`: 사용한 Gemma 모델명 (예: `"gemma-4-31b-it"`, `"gemma-3-27b-it"`)
  - `evals_run`: 실행한 eval ID 또는 이름 목록
- `runs[]`: 개별 실행 결과
  - `eval_id`: eval 번호
  - `eval_name`: 사람이 읽을 수 있는 eval 이름
  - `configuration`: `"with_skill"` (Gemma TUI에서는 베이스라인 미지원)
  - `result`: `pass_rate`, `passed`, `total`, `duration_seconds`, `input_tokens`, `output_tokens`, `errors` 포함
- `run_summary`: 구성별 통계 집계
  - 각 항목은 `mean`, `stddev`, `min`, `max` 포함
- `notes`: 분석기가 생성한 자유 형식 관찰 노트

> **Gemma TUI 참고:** 서브에이전트가 없으므로 `"without_skill"` 구성은 지원되지 않습니다. `run_summary`에 `with_skill` 항목만 기록하고, 반복(iteration) 간 비교로 개선 여부를 판단합니다.

---

## comparison.json

블라인드 비교기(`comparator.md`) 실행 결과입니다. `<채점-디렉토리>/comparison.json`에 위치합니다.

```json
{
  "winner": "A",
  "reasoning": "출력 A는 올바른 형식과 모든 필수 항목을 포함한 완전한 결과물입니다. 출력 B는 날짜 필드가 누락되고 형식이 일관되지 않습니다.",
  "rubric": {
    "A": {
      "content": {"correctness": 5, "completeness": 5, "accuracy": 4},
      "structure": {"organization": 4, "formatting": 5, "usability": 4},
      "content_score": 4.7,
      "structure_score": 4.3,
      "overall_score": 9.0
    },
    "B": {
      "content": {"correctness": 3, "completeness": 2, "accuracy": 3},
      "structure": {"organization": 3, "formatting": 2, "usability": 3},
      "content_score": 2.7,
      "structure_score": 2.7,
      "overall_score": 5.4
    }
  },
  "output_quality": {
    "A": {
      "score": 9,
      "strengths": ["완전한 결과물", "깔끔한 형식", "모든 항목 포함"],
      "weaknesses": ["헤더 스타일 경미한 불일치"]
    },
    "B": {
      "score": 5,
      "strengths": ["읽기 쉬운 출력", "기본 구조 올바름"],
      "weaknesses": ["날짜 필드 누락", "형식 불일치", "부분적 데이터 추출"]
    }
  },
  "expectation_results": {
    "A": {"passed": 4, "total": 5, "pass_rate": 0.80},
    "B": {"passed": 3, "total": 5, "pass_rate": 0.60}
  }
}
```

---

## analysis.json

후처리 분석기(`analyzer.md`) 실행 결과입니다. `<채점-디렉토리>/analysis.json`에 위치합니다.

```json
{
  "comparison_summary": {
    "winner": "A",
    "winner_skill": "path/to/winner/skill",
    "loser_skill": "path/to/loser/skill",
    "comparator_reasoning": "비교기가 승자를 선택한 이유 요약"
  },
  "winner_strengths": [
    "다중 페이지 문서 처리를 위한 명확한 단계별 지침",
    "서식 오류를 잡아낸 검증 스크립트 포함"
  ],
  "loser_weaknesses": [
    "'문서를 적절히 처리하세요'라는 모호한 지침이 일관성 없는 동작으로 이어짐",
    "검증 스크립트 없어 즉흥적으로 처리해 오류 발생"
  ],
  "instruction_following": {
    "winner": {
      "score": 9,
      "issues": ["경미: 선택적 로깅 단계 건너뜀"]
    },
    "loser": {
      "score": 6,
      "issues": [
        "스킬의 서식 템플릿 미사용",
        "3단계 지침 대신 자체 방식 적용"
      ]
    }
  },
  "improvement_suggestions": [
    {
      "priority": "high",
      "category": "instructions",
      "suggestion": "'문서를 적절히 처리하세요'를 명시적 단계로 교체",
      "expected_impact": "일관성 없는 동작의 원인인 모호함을 제거"
    }
  ],
  "transcript_insights": {
    "winner_execution_pattern": "스킬 읽기 → 5단계 절차 수행 → 검증 스크립트 실행",
    "loser_execution_pattern": "스킬 읽기 → 접근법 불명확 → 3가지 방법 시도"
  }
}
```

---

## 스키마 호환성 요약

| 스키마 | Gemma TUI 지원 | 비고 |
|--------|---------------|------|
| `evals.json` | ✅ 완전 지원 | |
| `history.json` | ✅ 완전 지원 | `grading_result` 값 변경됨 |
| `grading.json` | ✅ 완전 지원 | 도구명 및 타이밍 구조 수정됨 |
| `metrics.json` | ✅ 완전 지원 | Gemma TUI 도구명으로 수정됨 |
| `timing.json` | ✅ 완전 지원 | 단일 실행 구조로 단순화됨 |
| `benchmark.json` | ⚠️ 부분 지원 | `without_skill` 구성 미지원 |
| `comparison.json` | ✅ 완전 지원 | |
| `analysis.json` | ✅ 완전 지원 | |
