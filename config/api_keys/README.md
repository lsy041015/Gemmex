# API Key Folder

이 폴더는 API 키 파일 저장용입니다.

- `gemma_api_key.txt`: 단일 키 1개
- `gemma_api_keys.txt`: 멀티 키(쉼표 또는 줄바꿈 구분)

우선순위:
1. 환경변수 `GEMMA_API_KEYS`, `GEMMA_API_KEY`
2. `config/settings.env`
3. 이 폴더의 키 파일
