# -*- coding: utf-8 -*-
import asyncio
import json
from typing import Dict, Optional, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from game_logic import BlackjackGame, GameState

app = FastAPI(title="Blackjack Online Server", version="1.0.0")


# 게임 세션 관리
class GameSession:
    def __init__(self, game: BlackjackGame, ws1: WebSocket, ws2: WebSocket, p1_id: str, p2_id: str):
        self.game = game
        self.ws1 = ws1
        self.ws2 = ws2
        self.p1_id = p1_id
        self.p2_id = p2_id
        self.continue_votes: Set[str] = set()

    def get_ws(self, player_id: str) -> WebSocket:
        return self.ws1 if player_id == self.p1_id else self.ws2


# 게임 매칭 대기열
waiting_player: Optional[WebSocket] = None
waiting_player_id: Optional[str] = None

# 진행 중인 게임들 {game_id: GameSession}
active_sessions: Dict[str, GameSession] = {}


async def send_message(websocket: WebSocket, msg_type: str, data: dict):
    """클라이언트에게 메시지 전송"""
    try:
        message = {
            "type": msg_type,
            "data": data
        }
        await websocket.send_text(json.dumps(message, ensure_ascii=False))
    except Exception:
        # WebSocket이 이미 닫혔거나 에러 발생 시 무시
        pass


async def broadcast_game_state(game: BlackjackGame, ws1: WebSocket, ws2: WebSocket):
    """두 플레이어에게 게임 상태 전송"""
    state1 = game.get_game_state(game.player1.player_id)
    state2 = game.get_game_state(game.player2.player_id)

    await send_message(ws1, "game_state", state1)
    await send_message(ws2, "game_state", state2)


def get_round_result(game: BlackjackGame, player_id: str) -> dict:
    """라운드 결과 메시지 생성"""
    player = game.player1 if game.player1.player_id == player_id else game.player2
    opponent = game.player2 if game.player1.player_id == player_id else game.player1

    player_value = player.hand.get_value()
    opponent_value = opponent.hand.get_value()
    player_bust = player.hand.is_bust()
    opponent_bust = opponent.hand.is_bust()

    # 결과 판정
    if player_bust and opponent_bust:
        result = "draw"
        message = "Both Burst! Draw!"
    elif player_bust:
        result = "lose"
        message = "Burst! Lose!"
    elif opponent_bust:
        result = "win"
        message = "Opponent burst! Win!"
    elif player_value > opponent_value:
        result = "win"
        message = f"Win! ({player_value} vs {opponent_value})"
    elif player_value < opponent_value:
        result = "lose"
        message = f"Lose! ({player_value} vs {opponent_value})"
    else:
        result = "draw"
        message = f"Draw! ({player_value} vs {opponent_value})"

    return {
        "result": result,
        "message": message,
        "my_value": player_value,
        "opponent_value": opponent_value,
        "my_record": {"wins": player.wins, "losses": player.losses, "draws": player.draws},
        "opponent_record": {"wins": opponent.wins, "losses": opponent.losses, "draws": opponent.draws}
    }


@app.websocket("/blackjack/{player_id}")
async def blackjack_endpoint(websocket: WebSocket, player_id: str):
    global waiting_player, waiting_player_id

    await websocket.accept()
    print(f"[서버] {player_id} 접속")

    game_id = None

    try:
        # 매칭 시스템
        if waiting_player is None:
            # 첫 번째 플레이어 대기
            waiting_player = websocket
            waiting_player_id = player_id
            await send_message(websocket, "waiting", {"message": "wait for opponent..."})
            print(f"[서버] {player_id} 대기 중...")

            # 상대방이 올 때까지 대기
            while waiting_player == websocket:
                await asyncio.sleep(0.5)

            # 매칭 완료 후 game_id 찾기
            for gid, session in active_sessions.items():
                if session.p1_id == player_id or session.p2_id == player_id:
                    game_id = gid
                    break

            # 메시지 핸들러 시작
            if game_id:
                await handle_client_messages(websocket, player_id, game_id)

        else:
            # 두 번째 플레이어 - 게임 시작
            player1_ws = waiting_player
            player1_id = waiting_player_id
            player2_ws = websocket
            player2_id = player_id

            # 대기열 초기화
            waiting_player = None
            waiting_player_id = None

            # 게임 세션 생성
            game = BlackjackGame(player1_id, player2_id)
            game_id = f"{player1_id}_vs_{player2_id}"
            session = GameSession(game, player1_ws, player2_ws, player1_id, player2_id)
            active_sessions[game_id] = session

            print(f"[서버] 게임 시작: {player1_id} vs {player2_id}")

            # 매칭 완료 알림
            await send_message(player1_ws, "matched", {"opponent": player2_id})
            await send_message(player2_ws, "matched", {"opponent": player1_id})

            # 첫 라운드 시작
            await start_new_round(session)

            # 두 번째 플레이어의 메시지 핸들러 시작
            await handle_client_messages(player2_ws, player2_id, game_id)

    except WebSocketDisconnect:
        print(f"[서버] {player_id} 연결 종료")
        # 대기 중이었다면 대기열에서 제거
        if waiting_player == websocket:
            waiting_player = None
            waiting_player_id = None

    except Exception as e:
        print(f"[서버] 에러 발생: {e}")
        await send_message(websocket, "error", {"message": str(e)})

    finally:
        # 게임 세션 정리
        if game_id and game_id in active_sessions:
            del active_sessions[game_id]
            print(f"[서버] 게임 세션 {game_id} 정리")


async def start_new_round(session: GameSession):
    """새 라운드 시작"""
    session.game.start_round()
    session.continue_votes.clear()

    print(f"[서버] 라운드 {session.game.round_number} 시작")
    await send_message(session.ws1, "round_start", {"round": session.game.round_number})
    await send_message(session.ws2, "round_start", {"round": session.game.round_number})

    # 카드 배분
    session.game.deal_initial_cards()
    print(f"[서버] 카드 배분 완료")
    await broadcast_game_state(session.game, session.ws1, session.ws2)


async def handle_player_action(session: GameSession, player_id: str, action: str):
    """플레이어 액션 처리"""
    game = session.game

    print(f"[서버] {player_id} 액션: {action}")

    # 턴 확인
    if game.state != GameState.PLAYER_TURN or not game.current_player or game.current_player.player_id != player_id:
        print(f"[서버] {player_id} 턴이 아님 - 무시")
        return

    # 액션 처리
    if action == "hit":
        game.hit(player_id)
        await broadcast_game_state(game, session.ws1, session.ws2)
    elif action == "stand":
        game.stand(player_id)
        await broadcast_game_state(game, session.ws1, session.ws2)

    # 라운드 종료 체크
    if game.state == GameState.FINISHED:
        await handle_round_end(session)


async def handle_round_end(session: GameSession):
    """라운드 종료 처리"""
    print(f"[서버] 라운드 {session.game.round_number} 종료")
    await broadcast_game_state(session.game, session.ws1, session.ws2)

    # 결과 메시지 전송
    p1_result = get_round_result(session.game, session.p1_id)
    p2_result = get_round_result(session.game, session.p2_id)
    await send_message(session.ws1, "round_result", p1_result)
    await send_message(session.ws2, "round_result", p2_result)

    # 계속 플레이 여부 묻기
    await asyncio.sleep(2)
    await send_message(session.ws1, "ask_continue", {})
    await send_message(session.ws2, "ask_continue", {})


async def handle_continue_vote(session: GameSession, player_id: str, wants_continue: bool):
    """계속 플레이 투표 처리"""
    if wants_continue:
        session.continue_votes.add(player_id)
        print(f"[서버] {player_id} 계속 플레이 동의")

        # 양쪽 모두 투표했는지 확인
        if len(session.continue_votes) == 2:
            # 둘 다 동의 - 새 라운드 시작
            await start_new_round(session)
    else:
        # 한 명이라도 거부 - 게임 즉시 종료
        print(f"[서버] {player_id} 계속 플레이 거부 - 게임 종료")

        # 게임 종료 메시지 전송
        await send_message(session.ws1, "game_over", {"reason": f"{player_id} 플레이어가 게임을 종료했습니다"})
        await send_message(session.ws2, "game_over", {"reason": f"{player_id} 플레이어가 게임을 종료했습니다"})

        # WebSocket 연결 종료
        try:
            await session.ws1.close()
        except Exception:
            pass
        try:
            await session.ws2.close()
        except Exception:
            pass

        # 세션 정리
        game_id = f"{session.p1_id}_vs_{session.p2_id}"
        if game_id in active_sessions:
            del active_sessions[game_id]
            print(f"[서버] 게임 세션 {game_id} 정리 완료")


async def handle_client_messages(websocket: WebSocket, player_id: str, game_id: str):
    """클라이언트 메시지 핸들러"""
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            action = data.get("action")

            if game_id not in active_sessions:
                break

            session = active_sessions[game_id]

            if action in ["hit", "stand"]:
                await handle_player_action(session, player_id, action)
            elif action == "continue":
                await handle_continue_vote(session, player_id, True)
            elif action == "quit":
                await handle_continue_vote(session, player_id, False)

    except WebSocketDisconnect:
        print(f"[서버] {player_id} 연결 끊김")
    except Exception as e:
        print(f"[서버] {player_id} 메시지 처리 에러: {e}")


if __name__ == "__main__":
    import uvicorn
    print("="*50)
    print("블랙잭 온라인 서버 시작")
    print("포트: 8000")
    print("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
