#!/usr/bin/env python3
"""
IS211 Assignment 8 - Game of Pig with Design Patterns (Proxy & Factory)
"""

import argparse
import random
import time
import sys


class Player:
    """Base player class."""

    def __init__(self, name: str):
        self.name = name
        self.score = 0

    def decide_action(self, turn_total: int) -> str:
        """Determines whether to roll ('r') or hold ('h').

        Must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement decide_action.")

    def reset(self):
        """Resets the player score."""
        self.score = 0


class HumanPlayer(Player):
    """Represents a human-controlled player."""

    def decide_action(self, turn_total: int) -> str:
        while True:
            choice = input(
                f"[{self.name}] Total: {self.score}, Turn: {turn_total}. "
                "Roll (r) or Hold (h)? "
            ).strip().lower()
            if choice in ("r", "h"):
                return choice
            print("Invalid input. Please enter 'r' to roll or 'h' to hold.")


class ComputerPlayer(Player):
    """Represents an automated player using a predefined strategy."""

    def decide_action(self, turn_total: int) -> str:
        # Strategy: Hold at min(25, 100 - x), otherwise roll
        target = min(25, 100 - self.score)
        if turn_total >= target:
            return "h"
        return "r"


class PlayerFactory:
    """Factory to instantiate the appropriate Player subclass."""

    @staticmethod
    def create_player(player_type: str, name: str) -> Player:
        normalized_type = player_type.strip().lower()
        if normalized_type == "human":
            return HumanPlayer(name)
        elif normalized_type == "computer":
            return ComputerPlayer(name)
        else:
            raise ValueError(f"Unknown player type: {player_type}. Choose 'human' or 'computer'.")


class Die:
    """Standard six-sided die."""

    def __init__(self, sides: int = 6):
        self.sides = sides

    def roll(self) -> int:
        return random.randint(1, self.sides)


class Game:
    """Core Pig game implementation."""

    def __init__(self, player1: Player, player2: Player, target_score: int = 100):
        self.players = [player1, player2]
        self.current_player_idx = 0
        self.die = Die()
        self.target_score = target_score
        self.winner = None

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_idx]

    def switch_turn(self):
        self.current_player_idx = 1 - self.current_player_idx

    def play_turn(self) -> bool:
        """Executes a single turn.

        Returns True if a player has won the game, False otherwise.
        """
        player = self.current_player
        turn_total = 0
        print(f"\n--- {player.name}'s turn (Total: {player.score}) ---")

        while True:
            action = player.decide_action(turn_total)
            if action == "r":
                roll = self.die.roll()
                print(f"{player.name} rolled a {roll}.")
                if roll == 1:
                    print(f"Bust! {player.name} loses turn points.")
                    self.switch_turn()
                    return False
                else:
                    turn_total += roll
                    if player.score + turn_total >= self.target_score:
                        player.score += turn_total
                        self.winner = player
                        return True
            elif action == "h":
                player.score += turn_total
                print(f"{player.name} held. Current Total Score: {player.score}")
                if player.score >= self.target_score:
                    self.winner = player
                    return True
                self.switch_turn()
                return False

    def play(self):
        """Starts and runs standard gameplay loop until a winner is found."""
        print("=== Welcome to the Game of Pig ===")
        print(f"{self.players[0].name} vs {self.players[1].name}\n")

        while not self.winner:
            self.play_turn()

        print(f"\nGame Over! {self.winner.name} wins with {self.winner.score} points!")


class TimedGameProxy:
    """Proxy for the Game class that enforces a 60-second time limit."""

    def __init__(self, game: Game, time_limit: float = 60.0):
        self._game = game
        self.time_limit = time_limit
        self.start_time = None

    def __getattr__(self, name):
        """Delegate attribute/method lookups to the underlying Game instance."""
        return getattr(self._game, name)

    def is_time_up(self) -> bool:
        if self.start_time is None:
            return False
        return (time.time() - self.start_time) >= self.time_limit

    def determine_time_up_winner(self) -> Player:
        p1, p2 = self._game.players
        if p1.score > p2.score:
            return p1
        elif p2.score > p1.score:
            return p2
        else:
            return None  # Tie

    def play_turn(self) -> bool:
        """Executes a single roll/hold decision step with real-time expiration checks."""
        if self.is_time_up():
            return True

        player = self._game.current_player
        turn_total = 0
        print(f"\n--- {player.name}'s turn (Total: {player.score}) ---")

        while True:
            if self.is_time_up():
                print("\n[TIME'S UP!] One minute has elapsed.")
                return True

            action = player.decide_action(turn_total)

            # Re-check in case user took long to enter input
            if self.is_time_up():
                print("\n[TIME'S UP!] One minute has elapsed.")
                return True

            if action == "r":
                roll = self._game.die.roll()
                print(f"{player.name} rolled a {roll}.")
                if roll == 1:
                    print(f"Bust! {player.name} loses turn points.")
                    self._game.switch_turn()
                    return False
                else:
                    turn_total += roll
                    if player.score + turn_total >= self._game.target_score:
                        player.score += turn_total
                        self._game.winner = player
                        return True
            elif action == "h":
                player.score += turn_total
                print(f"{player.name} held. Current Total Score: {player.score}")
                if player.score >= self._game.target_score:
                    self._game.winner = player
                    return True
                self._game.switch_turn()
                return False

    def play(self):
        """Runs the game loop bounded by the timer."""
        print("=== Welcome to Timed Pig (60-second limit) ===")
        print(f"{self._game.players[0].name} vs {self._game.players[1].name}\n")
        self.start_time = time.time()

        while not self._game.winner and not self.is_time_up():
            self.play_turn()

        if self._game.winner:
            print(f"\nGame Over! {self._game.winner.name} wins with {self._game.winner.score} points!")
        else:
            # Time expired before 100 points
            winner = self.determine_time_up_winner()
            p1, p2 = self._game.players
            print
