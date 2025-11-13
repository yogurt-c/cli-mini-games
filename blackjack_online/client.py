# -*- coding: utf-8 -*-
import asyncio
import json
import curses
import locale
import sys
import time

import websockets
from typing import Optional


class BlackjackClient:
    def __init__(self, stdscr, server_url: str, player_id: str):
        self.server_url = server_url
        self.player_id = player_id
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.game_state = None
        self.stdscr = stdscr

    def print(self, msg: str):
        # print("\033[2J")
        # print("\033[H")
        # print("=" * 60)
        # print("블랙잭 온라인 게임 클라이언트")
        # print("=" * 60)
        # print(msg)
        display_screen(self.stdscr, msg)

    async def connect(self):
        """서버 연결"""
        uri = f"{self.server_url}/blackjack/{self.player_id}"
        try:
            self.websocket = await websockets.connect(uri)
            self.print(f"[클라이언트] 서버에 접속했습니다: {self.server_url}")
        except (OSError, ConnectionRefusedError) as e:
            text = f"\n[연결 실패] 서버에 연결할 수 없습니다."
            text += f"서버 주소: {self.server_url}"
            text += f"\n가능한 원인:"
            text += f"  1. 서버가 실행되지 않았습니다"
            text += f"  2. 서버 주소가 올바르지 않습니다"
            text += f"  3. 방화벽이 연결을 차단하고 있습니다"
            text += f"\n해결 방법:"
            text += f"  - 서버 PC에서 'python server.py'를 실행하세요"
            text += f"  - 서버 주소를 확인하세요 (예: ws://192.168.1.100:8000)"
            self.print(text)
            raise

    async def send_action(self, action: str, **kwargs):
        """서버에 액션 전송"""
        message = {"action": action, **kwargs}
        await self.websocket.send(json.dumps(message))

    def display_game_state(self, state: dict):
        """게임 상태 출력"""
        text = "\n" + "=" * 60
        # print("\n" + "="*60)

        # 상대 정보
        opp = state.get("opponent_info", {})
        opp_cards = " ".join([f"{c['rank']}{c['suit']}" for c in opp.get("hand", {}).get("cards", [])])
        opp_value = opp.get("hand", {}).get("value", "?")
        # print(f"상대방 ({opp.get('player_id', '?')}): {opp_cards} (값: {opp_value})")
        # print(f"  승: {opp.get('wins', 0)} | 패: {opp.get('losses', 0)} | 무: {opp.get('draws', 0)}")
        text += f"\nopponent ({opp.get('player_id', '?')}): {opp_cards} (value: {opp_value})"
        text += f"\n  Win: {opp.get('wins', 0)} | Lose: {opp.get('losses', 0)} | Draw: {opp.get('draws', 0)}"

        # print("-"*60)
        text += "\n" + "-" * 60

        # 내 정보
        my = state.get("my_info", {})
        my_cards = " ".join([f"{c['rank']}{c['suit']}" for c in my.get("hand", {}).get("cards", [])])
        my_value = my.get("hand", {}).get("value", "?")
        # print(f"나 ({my.get('player_id', '?')}): {my_cards} (값: {my_value})")
        # print(f"  승: {my.get('wins', 0)} | 패: {my.get('losses', 0)} | 무: {my.get('draws', 0)}")
        text += f"\nme ({my.get('player_id', '?')}): {my_cards} (value: {my_value})"
        text += f"\n  Win: {my.get('wins', 0)} | Lose: {my.get('losses', 0)} | Draw: {my.get('draws', 0)}"

        # 특수 상태
        if my.get("hand", {}).get("is_blackjack"):
            # print("  🎉 블랙잭!")
            text += "\n  🎉 blackjack!"
        if my.get("hand", {}).get("is_bust"):
            # print("  💥 버스트!")
            text += "\n  💥 burst!"

        # print("="*60)
        text += "\n" + "=" * 60

        # 턴 정보
        if state.get("is_my_turn"):
            # print(">>> 당신의 차례입니다!")
            text += "\n>>> it's your turn"
        elif state.get("current_turn"):
            # print(f">>> {state.get('current_turn')}의 차례입니다...")
            text += f"\n>>> {state.get('current_turn')}'s turn'..."

        self.print(text)

        self.game_state = state

    async def play(self):
        """게임 플레이 메인 루프"""
        try:
            await self.connect()
        except (OSError, ConnectionRefusedError):
            return  # 연결 실패 시 종료

        try:

            while True:
                # 서버 메시지 수신
                message = await self.websocket.recv()
                data = json.loads(message)
                msg_type = data.get("type")
                msg_data = data.get("data", {})

                if msg_type == "waiting":
                    self.print(f"\n[wait] {msg_data.get('message')}")

                elif msg_type == "matched":
                    self.print(f"\n[matched] matched with opposite: {msg_data.get('opponent')}")

                elif msg_type == "round_start":
                    # print(f"\n{'='*60}")
                    # print(f"라운드 {msg_data.get('round')} 시작!")
                    # print(f"{'='*60}")
                    text = f"\n{'=' * 60}"
                    text += f"\nround {msg_data.get('round')} start"
                    text += f"\n{'=' * 60}"
                    self.print(text)

                elif msg_type == "game_state":
                    self.display_game_state(msg_data)

                    # 상태에 따른 액션
                    game_state = msg_data.get("state")

                    if game_state == "player_turn" and msg_data.get("is_my_turn"):
                        # Hit or Stand
                        while True:
                            action = get_user_input(self.stdscr, 15, 1, "[H]it or [S]tand? ").upper()
                            # action = input("\n[H]it or [S]tand? ").strip().upper()
                            if action in ['H', 'S']:
                                act = "hit" if action == 'H' else "stand"
                                await self.send_action(act)
                                break
                            else:
                                # print("H 또는 S를 입력하세요.")
                                append_screen(self.stdscr, "value must be in H or S.")
                                time.sleep(0.5)

                    elif game_state == "finished":
                        # 라운드 종료
                        pass

                elif msg_type == "round_result":
                    # 라운드 결과 표시
                    my_rec = msg_data.get('my_record', {})
                    text = f"\n{'=' * 60}"
                    text += f"\nround result: {msg_data.get('message')}"
                    text += f"\nmy: {msg_data.get('my_value')} | opponent: {msg_data.get('opponent_value')}"
                    text += f"\nmy history - Win: {my_rec.get('wins', 0)} | Lose: {my_rec.get('losses', 0)} | Draw: {my_rec.get('draws', 0)}"
                    text += f"\n{'=' * 60}"
                    self.print(text)

                elif msg_type == "ask_continue":
                    # 계속 플레이 여부
                    while True:
                        choice = get_user_input(self.stdscr, 15, 1, "keep playing? [Y/N]: ").upper()
                        if choice in ['Y', 'N']:
                            if choice == 'Y':
                                await self.send_action("continue")
                            else:
                                await self.send_action("quit")
                                self.print("\ngame quit.")
                            break
                        else:
                            append_screen(self.stdscr, "value must be in Y or N.")
                            time.sleep(0.5)

                elif msg_type == "game_over":
                    text = f"\n{'=' * 60}"
                    text += "game over"
                    if "winner" in msg_data:
                        winner = msg_data.get("winner")
                        if winner == self.player_id:
                            text += "🎉 you win!"
                        else:
                            text += "you lose."
                    if "reason" in msg_data:
                        text += f"reason: {msg_data.get('reason')}"
                    text += f"{'=' * 60}"
                    self.print(text)
                    break

                elif msg_type == "error":
                    self.print(f"[error] {msg_data.get('message')}")

        except websockets.exceptions.ConnectionClosed:
            self.print("\n[연결 종료] 서버와의 연결이 끊어졌습니다.")
        except KeyboardInterrupt:
            self.print("\n[종료] 게임을 종료합니다.")
        finally:
            if self.websocket:
                await self.websocket.close()


def display_screen(stdscr, message: str):
    # 1. 화면 초기화
    stdscr.clear()

    # 터미널 크기 가져오기
    height, width = stdscr.getmaxyx()

    # 2. 내용 출력

    # 제목 영역 출력
    header = "=" * width
    title = "secret table"

    stdscr.addstr(0, 0, header)
    # 제목 중앙 정렬
    stdscr.addstr(1, (width - len(title)) // 2, title)
    stdscr.addstr(2, 0, header)

    # 주 메시지 출력 (화면 중앙 상단에 배치)
    stdscr.addstr(5, 0, message)

    # 3. 화면 갱신
    stdscr.refresh()


def append_screen(stdscr, message: str):
    stdscr.move(16, 0)
    stdscr.clrtoeol()
    stdscr.addstr(16, 0, message)


def get_user_input(stdscr, prompt_y, prompt_x, prompt_text, clear=False):
    if clear:
        stdscr.clear()

    # 1. 문자열 입력에 필요한 설정으로 변경
    curses.curs_set(1)  # 커서 보이기
    curses.echo()  # 에코 모드 활성화
    stdscr.nodelay(False)  # 입력이 들어올 때까지 차단(Blocking)

    # 제목 영역 출력
    height, width = stdscr.getmaxyx()
    header = "=" * width
    title = "secret table"

    stdscr.addstr(0, 0, header)
    # 제목 중앙 정렬
    stdscr.addstr(1, (width - len(title)) // 2, title)
    stdscr.addstr(2, 0, header)

    # 프롬프트 출력
    stdscr.addstr(prompt_y, prompt_x, prompt_text)
    stdscr.refresh()

    # getstr()으로 입력 받기
    input_bytes = stdscr.getstr(prompt_y, prompt_x + len(prompt_text) + 15, 30)

    # 2. 실시간 모니터링에 필요한 원래 설정으로 복구
    curses.curs_set(0)  # 커서 숨기기
    curses.noecho()  # 에코 모드 비활성화
    stdscr.nodelay(True)  # 비차단 모드 활성화# 디코딩 시도

    try:
        # 시스템 로케일로 설정된 인코딩을 사용하여 디코딩합니다.
        return input_bytes.decode(locale.getpreferredencoding())
    except UnicodeDecodeError:
        # 디코딩 실패 시, fallback으로 'utf-8'을 사용합니다.
        return input_bytes.decode('utf-8', errors='ignore')


def initialize_locale():
    """
    Python이 터미널의 인코딩을 올바르게 감지하도록 로케일을 설정합니다.
    """
    # 시스템의 기본 로케일 설정을 가져와 적용합니다. (Mac 환경에서 UTF-8 인코딩 문제를 해결)
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error as e:
        print(f"Warning: Failed to set locale to system default: {e}. Using UTF-8.")
        # 실패 시, 명시적으로 UTF-8 로케일을 사용하도록 설정 (Mac에서 일반적으로 작동)
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


async def main(stdscr):
    # curses 초기 설정
    curses.curs_set(0)  # 커서 숨기기
    stdscr.nodelay(True)  # 비차단 입력 모드 설정

    # curses가 멀티바이트 문자를 올바르게 처리하도록 설정합니다.
    curses.noqiflush()

    # 서버 주소 입력
    if len(sys.argv) > 1:
        server = sys.argv[1]
    else:
        server = get_user_input(stdscr, 10, 1, "type server host (default: ws://192.168.1.10:8000): ", True)
        # server = input("서버 주소 입력 (기본값: ws://192.168.1.10:8000): ").strip()
        if not server:
            server = "ws://192.168.1.10:8000"

    # 플레이어 ID 입력
    if len(sys.argv) > 2:
        player_id = sys.argv[2]
    else:
        # player_id = input("플레이어 이름 입력: ").strip()
        player_id = get_user_input(stdscr, 10, 1, "player name: ", True)
        if not player_id:
            player_id = f"Player_{id(object())}"

    # 게임 시작
    client = BlackjackClient(stdscr, server, player_id)
    await client.play()


def main_wrapper(stdscr):
    # asyncio.run() 대신, 이벤트 루프를 얻어 동기 함수 내에서 비동기 함수를 실행
    asyncio.run(main(stdscr))


if __name__ == "__main__":
    initialize_locale()

    curses.wrapper(main_wrapper)
    # asyncio.run(main())
