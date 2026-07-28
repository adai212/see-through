"""Assemble a See-through PSD from existing layer and depth PNG outputs.

This script does not run LayerDiff or Marigold. It reads an existing output
folder such as workspace/layerdiff_output/test_image5 and writes PSD files in
the parent save_dir.
"""

import argparse
import os
import os.path as osp
import sys

REPO_ROOT = osp.dirname(osp.dirname(osp.dirname(osp.abspath(__file__))))
sys.path.append(osp.join(REPO_ROOT, 'common'))
sys.path.append(osp.join(REPO_ROOT, 'inference'))

from utils.inference_utils import further_extr


DEFAULT_SRC = 'assets/test_image5.png'
DEFAULT_SAVE_DIR = 'workspace/layerdiff_output'


def output_dir_from_args(srcp: str, save_dir: str) -> str:
    srcname = osp.basename(osp.splitext(srcp)[0])
    return osp.join(save_dir, srcname)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assemble PSD files from an existing See-through output directory."
    )
    parser.add_argument('--srcp', type=str, default=DEFAULT_SRC,
                        help=f'input image path used to derive the output folder name (default: {DEFAULT_SRC})')
    parser.add_argument('--save_dir', type=str, default=DEFAULT_SAVE_DIR,
                        help=f'directory containing the per-image output folder (default: {DEFAULT_SAVE_DIR})')
    parser.add_argument('--tblr_split', action='store_true', default=True,
                        help='try split parts (handwear, eyes, etc) into left-right components (default: enabled)')
    parser.add_argument('--no_tblr_split', action='store_false', dest='tblr_split',
                        help='disable left-right part splitting')
    parser.add_argument('--rotate', action='store_true',
                        help='rotate loaded parts during PSD assembly')
    args = parser.parse_args()

    saved = output_dir_from_args(args.srcp, args.save_dir)
    existing_source = osp.join(saved, 'src_img.png')
    if not osp.isfile(existing_source):
        raise FileNotFoundError(
            f'Cannot assemble PSD: expected existing output at {existing_source}'
        )

    print(f'Assembling PSD from {saved}')
    further_extr(saved, rotate=args.rotate, save_to_psd=True, tblr_split=args.tblr_split)
    print('Done.')


if __name__ == '__main__':
    main()
