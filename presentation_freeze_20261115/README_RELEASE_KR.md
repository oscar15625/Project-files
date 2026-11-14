# 발표용 최종 동결 — FROZEN_BASELINE_ONLY

FINAL_EVIDENCE_SUMMARY_KR.md → ONE_PAGE_SLIDE_NUMBERS.md → CLAIM_LEDGER.csv → figures/ 순서로 확인하십시오. C1의 presentation_release snapshot은 이 릴리스 루트이며 중복 폴더 대신 단일 manifest로 잠근다.

검증: `python verify_presentation_release.py`. 의존성은 requirements.txt. 기본 작업은 저장해 검증이며 최적화하지 않는다. Windows에서 검증했고 Linux 호환 코드를 제공하지만 Linux 실제 실행을 주장하지 않는다.

baseline/에는 기존 공개 VI 전달 패키지를 그대로 보존했다. states/에는 E01/E03 및 v6 기타 결과, M01 실패, M03, 클라우드 상태를 추가 보존했다. 각 원출처/해시는 baseline_audit/에 있다. 최신 Root 24개 중21 STRICT PASS/3실패; E05 신규0회이다. 기존 결과 및 실패를 덮어쓰지 않았다.

원자료 PDF, 개인 프롬프트, 개인 절대경로, 불필요한 대형 파일은 배포하지 않는다. 기존 전체 연구 Git 이력은 공개하지 않고 이미 공개된 4d9bbc4 기반의 새 브랜치에 이 폴더만 추가한다. ZIP hash 및 최종 커밋은 릴리스 외부 DELIVERY.json에 기록한다(자기참조 해시 방지).
