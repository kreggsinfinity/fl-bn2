import sys
import asyncio
from vocab_generator import run_vocab_generation

def main():
    print("Starting Vocabulary Upgrade Studio generator (9:16 Vertical Reel)...")
    video_p, meta = asyncio.run(run_vocab_generation(item_idx=0))
    print(f"Done! Final video generated: {video_p}")

if __name__ == "__main__":
    main()
