# 🐿️ DotoriBot (도토리봇)
### 2026.03.27 기준
### 이 README.md는 Google Antigravity의 Gemini 3 Flash를 사용하여 작성되었습니다.

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.4.0+-7289da.svg)](https://github.com/Rapptz/discord.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**DotoriBot**은 디스코드 커뮤니티를 위한 다기능 엔터테인먼트 및 유틸리티 봇입니다. 
로스트아크 유저들을 위한 편의 기능부터 전용 경제 시스템, 모의 주식 투자, 음악 재생까지 다양한 기능을 제공합니다.

---

## 🚀 주요 기능 (Key Features)

### 🎮 도토리 경제 시스템 & 미니게임
- **도토리 경제**: `/돈줘` 명령어로 기초자산을 획득하고 커뮤니티 활동을 통해 부를 쌓으세요.
- **도박 미니게임**: `/게임 [베팅]`을 통해 획득한 도토리를 걸고 승부를 벌입니다.
- **아이템 상점**: 게임의 확률을 높여주는 '사기주사위'나 이자가 붙는 '적금통장' 등 다양한 아이템을 구매할 수 있습니다.
- **복리 이자**: 보유한 적금통장에 따라 매일 자정 자동으로 이자가 지급됩니다.

### 📈 모의 주식 투자
- **실시간 주가 조회**: 국장(KOSPI, ETF)의 실시간 시세를 조회합니다.
- **모의 거래**: 도토리를 이용해 주식을 매수/매도하며 포트폴리오를 관리합니다.
- **수익률 추적**: `/내주식` 명령어로 현재 보유 종목의 실시간 수익률을 확인할 수 있습니다.

### ⚔️ 로스트아크(Lost Ark) 특화 유틸리티
- **공략 및 시트**: 공대 시간표 시트, 로아투두, 인벤 등 링크 바로가기 제공.
- **경매 계산기**: `/쌀`, `/선점쌀` 명령어로 레이드 종료 후 최적의 입찰가를 계산합니다.
- **콘텐츠 예측**: 가디언 보스 및 카드 예측 등 게임 내 일정 분석 도우미.
- **공지 자동화**: 매주 화요일 시간표 작성 알림 등 자동화 기능을 포함합니다.

### 🎵 멀티미디어 & AI
- **음악 재생**: YouTube 링크를 통한 고품질 음악 스트리밍 및 대기열 관리.
- **Gemini AI**: Google Gemini 모델을 활용한 스마트한 대화 엔진 탑재.
- **뽑기 시뮬레이터**: 원신, 붕괴: 스타레일 등 주요 게임의 가차 시뮬레이션 제공.

---

## 🛠 기술 스택 (Tech Stack)

- **Language**: Python 3.8+
- **Framework**: [discord.py](https://github.com/Rapptz/discord.py)
- **Database**: SQLite3 (Game data, Market data)
- **APIs**:
  - `Google Gemini API` (Generative AI)
  - `FinanceDataReader` (Stock Market Data)
  - `yt-dlp` & `ffmpeg` (Music Streaming)

---

## 📂 프로젝트 구조 (Project Structure)

```text
dotoribot/
├── main.py              # 봇 진입점 및 코어 로직
├── game.py              # 메인 게임 시스템 엔진
├── logic.py             # 비즈니스 로직 처리
├── dotori_stock_core.py # 주식 데이터 및 거래 코어
├── features/            # 기능별 모듈화된 명령어
│   ├── dotori_game.py   # 미니게임 명령어
│   ├── dotori_stock.py  # 주식 투자 명령어
│   ├── singing_dotori.py# 음악 재생 모듈
│   └── kakao_map_utils.py# 지도 및 위치 검색
├── system_prompts.json  # AI 페르소나 설정
└── requirements.txt     # 의존성 패키지 목록
```

---

## ⚙️ 설치 및 실행 방법 (Setup & Run)

### 1. 요구사항 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일을 루트 디렉토리에 생성하고 아래 정보를 입력합니다:
```env
DOTORI_BOT_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_google_gemini_api_key
# 기타 필요한 채널 ID 및 로아 시트 주소 등
```

### 3. 실행
```bash
python main.py
```

---

## 📝 명령어 목록 (Commands)
명령어의 전체 목록은 봇 채팅창에서 `!사용법` 또는 `/사용법`을 입력하여 확인할 수 있습니다.

- `!안녕`: 봇과 인사하기
- `/게임 [베팅]`: 도토리 게임 실행
- `/주식 [종목명]`: 주가 정보 조회
- `/노래 [URL]`: 유튜브 음악 재생
- `/쌀 [가격] [인원]`: 경매 입찰가 계산

---

## ⚖️ License
This project is licensed under the [MIT License](LICENSE).