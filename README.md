# 🎮 Terminal Games Collection

터미널에서 즐기는 클래식 게임 모음집

## 📋 게임 목록

### 1. 2048
숫자 타일을 합쳐 2048을 만드는 퍼즐 게임

**실행 방법:**
```bash
python 2048.py
```

**조작법:**
- `↑/↓/←/→` 방향키로 타일 이동
- `Q` 종료

**게임 규칙:**
- 같은 숫자끼리 합쳐서 더 큰 숫자 생성
- 2048 타일을 만들면 승리
- 더 이상 이동할 수 없으면 게임 오버

---

### 2. 1945 (슈팅 게임)
세로 스크롤 비행 슈팅 게임

**실행 방법:**
```bash
python 1945.py
```

**조작법:**
- `A/D` 또는 `←/→` 방향키로 레인 이동
- `SPACE` 총알 발사
- `Q` 종료

**게임 특징:**
- 5개 레인 방식의 비행 슈팅
- 다양한 적 유닛 (일반 적, 보스)
- 아이템 시스템
  - `P` (파워): 공격력 증가
  - `R` (연사력): 발사 속도 증가
  - `S` (실드): 피격 무효화
  - `$` (보너스): 추가 점수
- 보스 등장 시스템
- 체력, 점수, 레벨 시스템

---

### 3. 블랙잭 온라인 (Blackjack Online)
WebSocket 기반 1대1 온라인 블랙잭

**실행 방법:**

**서버 (호스트):**
```bash
cd blackjack_online
pip install -r requirements.txt
python server.py
```

**클라이언트 (플레이어):**
```bash
cd blackjack_online
pip install websockets
python client.py

# 또는 서버 주소 지정
python client.py ws://192.168.1.100:8000 Player1
```

**실행 파일 빌드 (Python 없는 PC용):**
```bash
cd blackjack_online
python build_client.py
# dist/ 폴더에 실행 파일 생성됨
```

**게임 특징:**
- 1:1 플레이어 대결 (딜러 없음)
- WebSocket 기반 실시간 멀티플레이
- 독특한 카드 값 시스템 (Q=11, K=12)
- 턴제 시스템
- 승/패/무승부 통계 기록

자세한 규칙은 [blackjack_online/README.md](blackjack_online/README.md) 참고

---

## 🔧 시스템 요구사항

### 공통
- Python 3.7 이상
- 터미널 환경 (Windows CMD/PowerShell, macOS Terminal, Linux Terminal)

### 게임별 의존성

**2048:**
- 기본 Python 라이브러리만 사용 (추가 설치 불필요)

**1945:**
- `curses` (Linux/macOS 기본 포함, Windows는 `windows-curses` 필요)
```bash
# Windows만
pip install windows-curses
```

**블랙잭 온라인:**
- 서버: `fastapi`, `uvicorn`, `websockets`
- 클라이언트: `websockets`
```bash
cd blackjack_online
pip install -r requirements.txt
```

---

## 🎯 각 게임 특징 요약

| 게임 | 장르 | 플레이어 | 난이도 | 특징 |
|------|------|---------|--------|------|
| **2048** | 퍼즐 | 1인 | ⭐⭐ | 전략적 사고, 중독성 |
| **1945** | 슈팅 | 1인 | ⭐⭐⭐ | 실시간 액션, 아이템 시스템 |
| **블랙잭** | 카드 | 2인 | ⭐ | 온라인 멀티플레이, PvP |

---

## 📝 라이선스

이 프로젝트는 개인 학습 및 재미를 위한 프로젝트입니다.

---

## 🐛 버그 제보 및 기여

버그를 발견하거나 개선 사항이 있다면 이슈를 등록해주세요!

---

## 💡 팁

- **2048**: 한 방향으로 몰아가는 전략 추천 (예: 항상 아래쪽으로)
- **1945**: 적 총알 패턴을 익히고, 아이템을 적극 활용하세요
- **블랙잭**: 상대방의 카드 장수를 보고 전략을 세우세요

즐거운 게임 되세요! 🎮
