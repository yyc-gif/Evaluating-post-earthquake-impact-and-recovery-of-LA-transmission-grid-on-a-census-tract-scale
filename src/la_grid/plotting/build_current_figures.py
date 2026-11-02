"""Reproduce the current figures for version 2026-10-14.

Earlier NCV14 and five-class implementations remain in preserved Git history,
not competing current builders. No model is fitted by this command.
"""
import argparse


def main(output_dir=None, mirror_dir=None):
    from build_current_suite_p2 import main as adopted_p2_suite
    adopted_p2_suite(output_dir=output_dir, mirror_dir=mirror_dir)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--portable',action='store_true',help='Reuse hash-bound saved inputs; no physical archives required.')
    parser.add_argument('--rebuild',action='store_true',help='Replay the adopted frozen artwork and verify deterministic hashes.')
    parser.add_argument('--output-dir',help='Write the suite to a separate review directory under the repository.')
    parser.add_argument('--mirror-dir',help='Write artwork mirrors, index and gallery to a separate review directory.')
    args=parser.parse_args()
    main(output_dir=args.output_dir, mirror_dir=args.mirror_dir)
