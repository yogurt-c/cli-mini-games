# -*- coding: utf-8 -*-
import random
from typing import List, Dict, Optional
from enum import Enum


class GameState(Enum):
    WAITING = "waiting"
    DEALING = "dealing"
    PLAYER_TURN = "player_turn"
    FINISHED = "finished"


class Card:
    """카드 클래스"""
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank}{self.suit}"

    def get_value(self) -> int:
        """카드의 값 반환"""
        if self.rank == 'J':
            return 10
        elif self.rank == 'Q':
            return 11
        elif self.rank == 'K':
            return 12
        elif self.rank == 'A':
            return 1
        else:
            return int(self.rank)

    def to_dict(self) -> Dict:
        return {"suit": self.suit, "rank": self.rank}


class Deck:
    """덱 클래스"""
    suits = ['♠', '♥', '♦', '♣']
    ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

    def __init__(self):
        self.cards: List[Card] = []
        self.build()

    def build(self):
        """52장의 카드로 덱 생성"""
        self.cards = [Card(suit, rank) for suit in self.suits for rank in self.ranks]

    def shuffle(self):
        """덱 섞기"""
        random.shuffle(self.cards)

    def deal(self) -> Card:
        """카드 한 장 뽑기"""
        return self.cards.pop()


class Hand:
    """핸드 클래스"""
    def __init__(self):
        self.cards: List[Card] = []

    def add_card(self, card: Card):
        """카드 추가"""
        self.cards.append(card)

    def get_value(self) -> int:
        """핸드의 총 값 계산 (Ace 처리 포함)"""
        value = sum(card.get_value() for card in self.cards)
        # aces = sum(1 for card in self.cards if card.rank == 'A')

        # Ace를 1로 계산해야 하는 경우
        # while value > 21 and aces:
        #     value -= 10
        #     aces -= 1

        return value

    def is_blackjack(self) -> bool:
        """블랙잭 판정 (처음 2장으로 21)"""
        return len(self.cards) == 2 and self.get_value() == 21

    def is_bust(self) -> bool:
        """버스트 판정"""
        return self.get_value() > 21

    def to_dict(self, hide_first: bool = False) -> Dict:
        """핸드 정보를 딕셔너리로 반환"""
        if hide_first and len(self.cards) > 0:
            cards = [{"suit": "?", "rank": "?"}] + [c.to_dict() for c in self.cards[1:]]
        else:
            cards = [c.to_dict() for c in self.cards]

        return {
            "cards": cards,
            "value": self.get_value() if not hide_first else "?",
            "is_blackjack": self.is_blackjack() if not hide_first else False,
            "is_bust": self.is_bust() if not hide_first else False
        }


class Player:
    """플레이어 클래스"""
    def __init__(self, player_id: str):
        self.player_id = player_id
        self.hand = Hand()
        self.wins = 0
        self.losses = 0
        self.draws = 0

    def win(self):
        """승리"""
        self.wins += 1

    def lose(self):
        """패배"""
        self.losses += 1

    def draw(self):
        """무승부"""
        self.draws += 1

    def reset_hand(self):
        """핸드 초기화"""
        self.hand = Hand()

    def to_dict(self) -> Dict:
        return {
            "player_id": self.player_id,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "hand": self.hand.to_dict()
        }


class BlackjackGame:
    """블랙잭 게임 로직"""
    def __init__(self, player1_id: str, player2_id: str):
        self.deck = Deck()
        self.player1 = Player(player1_id)
        self.player2 = Player(player2_id)
        self.state = GameState.WAITING
        self.current_player: Optional[Player] = None
        self.round_number = 0

    def start_round(self):
        """라운드 시작"""
        self.round_number += 1
        self.player1.reset_hand()
        self.player2.reset_hand()

        # 덱 리셋 및 섞기
        if len(self.deck.cards) < 15:
            self.deck.build()
        self.deck.shuffle()

    def deal_initial_cards(self):
        """초기 카드 배분"""
        self.state = GameState.DEALING
        for _ in range(2):
            self.player1.hand.add_card(self.deck.deal())
            self.player2.hand.add_card(self.deck.deal())

        # 플레이어1부터 시작
        self.current_player = self.player1
        self.state = GameState.PLAYER_TURN

    def hit(self, player_id: str) -> bool:
        """카드 받기"""
        if self.state != GameState.PLAYER_TURN:
            return False

        player = self.player1 if self.player1.player_id == player_id else self.player2
        if player != self.current_player:
            return False

        player.hand.add_card(self.deck.deal())

        # 버스트 체크
        if player.hand.is_bust():
            self._switch_player()

        return True

    def stand(self, player_id: str) -> bool:
        """스탠드"""
        if self.state != GameState.PLAYER_TURN:
            return False

        player = self.player1 if self.player1.player_id == player_id else self.player2
        if player != self.current_player:
            return False

        self._switch_player()
        return True

    def _switch_player(self):
        """다음 플레이어로 전환"""
        if self.current_player == self.player1:
            self.current_player = self.player2
        else:
            # 두 플레이어 모두 턴 종료
            self.state = GameState.FINISHED
            self._determine_winners()

    def _determine_winners(self):
        """승자 결정 - 플레이어끼리 비교"""
        p1_value = self.player1.hand.get_value()
        p2_value = self.player2.hand.get_value()
        p1_bust = self.player1.hand.is_bust()
        p2_bust = self.player2.hand.is_bust()

        # 둘 다 버스트
        if p1_bust and p2_bust:
            self.player1.draw()
            self.player2.draw()
        # 플레이어1만 버스트
        elif p1_bust:
            self.player1.lose()
            self.player2.win()
        # 플레이어2만 버스트
        elif p2_bust:
            self.player1.win()
            self.player2.lose()
        # 둘 다 안 터짐 - 점수 비교
        elif p1_value > p2_value:
            self.player1.win()
            self.player2.lose()
        elif p1_value < p2_value:
            self.player1.lose()
            self.player2.win()
        else:
            # 동점
            self.player1.draw()
            self.player2.draw()

    def get_game_state(self, for_player_id: str) -> Dict:
        """게임 상태 반환"""
        is_player1 = for_player_id == self.player1.player_id
        other_player = self.player2 if is_player1 else self.player1
        my_player = self.player1 if is_player1 else self.player2

        return {
            "state": self.state.value,
            "round": self.round_number,
            "my_info": my_player.to_dict(),
            "opponent_info": {
                "player_id": other_player.player_id,
                "wins": other_player.wins,
                "losses": other_player.losses,
                "draws": other_player.draws,
                "hand": other_player.hand.to_dict() if self.state == GameState.FINISHED else {
                    "cards": [{"suit": "?", "rank": "?"}] * len(other_player.hand.cards),
                    "value": "?",
                    "is_blackjack": False,
                    "is_bust": False
                }
            },
            "current_turn": self.current_player.player_id if self.current_player else None,
            "is_my_turn": self.current_player == my_player if self.current_player else False
        }
