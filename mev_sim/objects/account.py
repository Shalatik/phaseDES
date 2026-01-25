from dataclasses import dataclass

@dataclass
class Account:
    eth_wei: int
    usdc_units: int
    nonce: int = 0
    last_received_amount: int = 0

    def snapshot(self) -> dict:
        return {
            "eth_wei": self.eth_wei,
            "usdc": self.usdc_units,
            "nonce": self.nonce,
            "last_recv": self.last_received_amount,
        }