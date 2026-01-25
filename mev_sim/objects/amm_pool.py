# mev_sim/domain/amm.py
from dataclasses import dataclass
from mev_sim.config.blockchain_constants import *

@dataclass
class AMMPool:
    name: str
    eth_reserve: int
    usdc_reserve: int

    def snapshot(self) -> dict:
        return {
            "name": self.name,
            "eth": self.eth_reserve,
            "usdc": self.usdc_reserve,
        }

    def execute_swap(self, amount_in, target_token) -> int:
        amount_out = self.calculate_out(amount_in, target_token)
				
        if target_token == ETH_TO_USDC:
            self.eth_reserve += amount_in
            self.usdc_reserve -= amount_out
        else:
            self.usdc_reserve += amount_in
            self.eth_reserve -= amount_out

        return True, amount_out
    
    def calculate_out(self, amount_in, target_token):
        if amount_in <= 0: return 0
        
        if target_token == ETH_TO_USDC:
            res_in, res_out = (self.eth_reserve, self.usdc_reserve)
        else:
          res_in, res_out = (self.usdc_reserve, self.eth_reserve)
        
        amount_in_with_fee = amount_in * 997
        numerator = amount_in_with_fee * res_out
        denominator = (res_in * 1000) + amount_in_with_fee
        return numerator // denominator
    
