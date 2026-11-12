"""Reproduce the current eight-main/eight-supplement review collection.

Earlier NCV14 and five-class implementations remain in preserved Git history,
not competing current builders. No model is fitted by this command.
"""
import argparse


def main(output_dir=None, mirror_dir=None, historical_p2=False):
    if historical_p2:
        from build_current_suite_p2 import main as build
    else:
        from build_s6_main4_review import main as build
    build(output_dir=output_dir, mirror_dir=mirror_dir)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--portable',action='store_true',help='Reuse hash-bound saved inputs; no physical archives required.')
    parser.add_argument('--rebuild',action='store_true',help='Rebuild the current artwork from saved inputs.')
    parser.add_argument('--output-dir',help='Write the suite to a separate review directory under the repository.')
    parser.add_argument('--mirror-dir',help='Write artwork mirrors, index and gallery to a separate review directory.')
    parser.add_argument('--historical-p2',action='store_true',help='Explicitly reproduce the earlier seven-main/nine-supplement collection.')
    args=parser.parse_args()
    main(output_dir=args.output_dir, mirror_dir=args.mirror_dir,historical_p2=args.historical_p2)
