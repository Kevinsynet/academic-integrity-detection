#!/usr/bin/env python3
"""Command-line entry point for batch integrity screening."""

import argparse
import logging
import sys
from pathlib import Path

from src.config import Config
from src.pipeline import discover, discover_skipped, run_pipeline


def _parser():
    parser = argparse.ArgumentParser(
        description="Multimodal academic integrity screening prototype"
    )
    parser.add_argument("--input_dir", default="./sample_submissions")
    parser.add_argument("--output_dir", default="./reports")
    parser.add_argument("--threshold", type=float, default=0.60)
    parser.add_argument("--chunk_size", type=int, default=300)
    parser.add_argument("--overlap", type=int, default=45)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--reference_dir", default="./reference_data")
    parser.add_argument(
        "--risk_medium", type=float, default=10.0,
        help="Coverage percentage at which risk becomes MEDIUM",
    )
    parser.add_argument(
        "--risk_high", type=float, default=25.0,
        help="Coverage percentage at which risk becomes HIGH",
    )
    parser.add_argument("--skip_video", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def _configuration(parser, args):
    config = Config(
        threshold=args.threshold,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        device=args.device,
        batch_size=args.batch_size,
        risk_medium=args.risk_medium,
        risk_high=args.risk_high,
    )
    if not 0 <= config.threshold <= 1:
        parser.error("--threshold must be between 0 and 1")
    if config.chunk_size <= 0 or not 0 <= config.overlap < config.chunk_size:
        parser.error("--chunk_size must be positive and --overlap must be in [0, chunk_size)")
    if not 0 <= config.risk_medium < config.risk_high <= 100:
        parser.error("Risk thresholds must satisfy 0 <= --risk_medium < --risk_high <= 100")
    if config.batch_size <= 0:
        parser.error("--batch_size must be positive")
    return config


def main(argv=None):
    parser = _parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        parser.error(f"Input directory does not exist: {input_dir}")
    config = _configuration(parser, args)
    skipped = discover_skipped(input_dir)
    paths = discover(input_dir)
    for path in skipped:
        print(f"Skipped unsupported file: {path}")
    if not paths:
        print(f"No supported PDF, DOCX, or MP4 files found; skipped {len(skipped)} unsupported files.")
        return 2

    try:
        reports, _ = run_pipeline(
            input_dir,
            args.output_dir,
            config=config,
            reference_dir=args.reference_dir,
            skip_video=args.skip_video,
            skipped_files=skipped,
        )
    except Exception as exc:
        logging.exception("Pipeline failed")
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1

    failed = sum(report["extraction_status"] == "error" for report in reports)
    empty = sum(report["extraction_status"] == "empty" for report in reports)
    video_skipped = sum(report["extraction_status"] == "video_skipped" for report in reports)
    failure_label = "per-file extraction failure" if failed == 1 else "per-file extraction failures"
    skipped_label = "unsupported file" if len(skipped) == 1 else "unsupported files"
    print(
        f"Completed batch: {len(reports)} supported files; {failed} {failure_label}; "
        f"{empty} empty/no-speech; {video_skipped} videos skipped; "
        f"{len(skipped)} {skipped_label} skipped. Reports: {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
