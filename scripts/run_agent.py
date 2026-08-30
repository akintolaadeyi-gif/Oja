import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.agent import run_agent

if __name__ == "__main__":
    description = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else \
        "A zobo hibiscus drink in 50cl PET bottles sold in Lagos supermarkets."
    run_agent(description, save_trajectory=True)
