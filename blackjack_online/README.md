# 블랙잭 온라인 게임

터미널에서 실행되는 1대1 온라인 블랙잭 게임입니다.

## 파일 구성

- `game_logic.py` - 블랙잭 게임 로직 (카드, 덱, 핸드, 게임 규칙)
- `server.py` - WebSocket 기반 게임 서버
- `client.py` - 터미널 클라이언트 (플레이어용)
- `requirements.txt` - 필요한 Python 패키지
- `build_client.py` - 클라이언트 빌드 스크립트 (Python)
- `build.sh` / `build.bat` - 클라이언트 빌드 스크립트 (쉘)

## 설치 방법

### 서버 PC

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python server.py
```

서버는 `0.0.0.0:8000` 포트에서 실행됩니다.

### 클라이언트 PC

**방법 1: Python 스크립트 실행 (Python 설치 필요)**

```bash
# 의존성 설치 (websockets만 필요)
pip install websockets

# 클라이언트 실행
python client.py

# 또는 인자로 서버 주소와 플레이어 이름 지정
python client.py ws://192.168.1.100:8000 Player1
```

**방법 2: 실행 파일 사용 (Python 설치 불필요) ⭐추천**

클라이언트를 실행 파일로 빌드하면 Python이 없는 PC에서도 실행 가능합니다.

#### 빌드 방법:

**Windows:**
```bash
build.bat
```

**Mac/Linux:**
```bash
./build.sh
```

**또는 Python 스크립트:**
```bash
python build_client.py
```

빌드 완료 후 `dist/` 폴더에 실행 파일이 생성됩니다:
- Windows: `dist/blackjack_client.exe`
- Mac/Linux: `dist/blackjack_client`

#### 배포:
생성된 실행 파일만 클라이언트 PC에 복사하여 실행하세요.

## 게임 방법

1. **서버 시작**: 서버 PC에서 `python server.py` 실행
2. **플레이어 접속**:
   - 첫 번째 플레이어: 클라이언트 실행 → 대기
   - 두 번째 플레이어: 클라이언트 실행 → 게임 시작
3. **게임 진행**:
   - 베팅: 칩을 베팅
   - 플레이: Hit(H) 또는 Stand(S) 선택
   - 결과: 승패 확인 후 다음 라운드 여부 선택

## 게임 규칙

- 시작 칩: 1000
- 블랙잭: 1.5배 배당
- 일반 승리: 1배 배당
- 무승부: 베팅 금액 반환
- 딜러는 17 미만일 때 자동으로 카드를 받음

## 포트 변경

서버 포트를 변경하려면 `server.py` 마지막 줄 수정:

```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # 포트 번호 변경
```

## 네트워크 설정

내부망에서 사용 시:
- 서버 PC의 방화벽에서 8000 포트 허용
- 클라이언트는 서버 PC의 내부 IP 주소로 접속 (예: `ws://192.168.1.100:8000`)
