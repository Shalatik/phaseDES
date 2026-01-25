from mev_sim.run import run_sim
from mev_sim.utils.logging import setup_logging

def main():
    setup_logging("outputs/output_log.txt")
    run_sim()

if __name__ == "__main__":
    main()