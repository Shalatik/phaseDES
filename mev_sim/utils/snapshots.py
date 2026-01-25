from mev_sim.config.blockchain_constants import *

def format_pools(state) -> str:
    a = state.amm_pool_a.snapshot()
    b = state.amm_pool_b.snapshot()

    lines = [
        "pool | eth | usdc",
        f"A | {a['eth']} | {a['usdc']}",
        f"B | {b['eth']} | {b['usdc']}",
    ]
    return "\n"+ "\n".join(lines) + "\n"


def format_users(state, user_ids) -> str:
    lines = ["id | eth | usdc | nonce"]
    for uid in user_ids:
        acc = state.accounts[uid]
        lines.append(
            f"{uid} | {acc.eth_wei // ETH_TO_WEI} | {acc.usdc_units} | {acc.nonce}"
        )
    return "\n"+"\n".join(lines) + "\n"
