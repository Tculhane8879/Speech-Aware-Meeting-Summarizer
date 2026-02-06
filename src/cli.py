from __future__ import annotations

import argparse
from pathlib import Path

from meeting_summarizer.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Speech-aware meeting summarizer (CS 582).")
    parser.add_argument("--input", type=str, default="data/raw/example.wav",
                        help="Path to input audio file (can be placeholder for now).")
    parser.add_argument("--output", type=str, default="outputs/run1",
                        help="Directory to write outputs.")
    parser.add_argument("--enable-engagement", action="store_true",
                        help="Enable engagement/emotion stage (optional).")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    result = run_pipeline(input_path=input_path, output_dir=output_dir, enable_engagement=args.enable_engagement)

    print("Pipeline ran (scaffold). Outputs written to:", result.output_dir)
    print()
    print(result.summary_text)


if __name__ == "__main__":
    main()