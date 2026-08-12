"""Shared casino wallet used across all games."""


class PlayerWallet:
    DEFAULT_BALANCE = 1000

    def __init__(self, balance=None):
        self.balance = balance if balance is not None else self.DEFAULT_BALANCE
