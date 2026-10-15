"""Reproduce the current figures for version 2026-10-14.

Earlier NCV14 and five-class implementations remain in preserved Git history,
not competing current builders. No model is fitted by this command.
"""
import argparse


def main():
    from build_current_suite_p2 import main as adopted_p2_suite
    adopted_p2_suite()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--portable',action='store_true',help='Reuse hash-bound saved inputs; no physical archives required.')
    parser.add_argument('--rebuild',action='store_true',help='Replay the adopted frozen artwork and verify deterministic hashes.')
    parser.parse_args()
    main()
