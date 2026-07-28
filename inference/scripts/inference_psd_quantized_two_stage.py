"""Run quantized See-through inference and PSD assembly as three Python processes.

Defaults are tuned for this local GTX 1070 setup. Running this script without
extra arguments is equivalent to the stable low-VRAM three-stage command.
"""

import argparse
import os
import os.path as osp
import subprocess
import sys


DEFAULT_SRC = 'assets/test_image5.png'
DEFAULT_SAVE_DIR = 'workspace/layerdiff_output'
DEFAULT_LAYERDIFF_RESOLUTION = 768
DEFAULT_LAYERDIFF_RESOLUTION_DEPTH = 512
DEFAULT_MARIGOLD_RESOLUTION = 640
DEFAULT_MARIGOLD_RESOLUTION_DEPTH = 384
DEFAULT_SEED = 42
DEFAULT_NUM_INFERENCE_STEPS = 30


def output_dir_from_src(srcp: str, save_dir: str) -> str:
    srcname = osp.basename(osp.splitext(srcp)[0])
    return osp.join(save_dir, srcname)


def output_dir_has_files(path: str) -> bool:
    if not osp.isdir(path):
        return False
    with os.scandir(path) as entries:
        return any(entries)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Three-stage quantized inference with local low-VRAM defaults.",
    )
    parser.add_argument('--srcp', type=str, default=DEFAULT_SRC,
                        help=f'input image (default: {DEFAULT_SRC})')
    parser.add_argument('--save_dir', type=str, default=DEFAULT_SAVE_DIR,
                        help=f'output directory (default: {DEFAULT_SAVE_DIR})')
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED)
    parser.add_argument('--resolution', type=int, default=DEFAULT_LAYERDIFF_RESOLUTION,
                        help=f'LayerDiff resolution (default: {DEFAULT_LAYERDIFF_RESOLUTION})')
    parser.add_argument('--marigold_resolution', type=int, default=DEFAULT_MARIGOLD_RESOLUTION,
                        help=f'Marigold wrapper resolution argument (default: {DEFAULT_MARIGOLD_RESOLUTION})')
    parser.add_argument('--resolution_depth', type=int, default=DEFAULT_MARIGOLD_RESOLUTION_DEPTH,
                        help=f'Marigold depth resolution (default: {DEFAULT_MARIGOLD_RESOLUTION_DEPTH})')
    parser.add_argument('--num_inference_steps', type=int, default=DEFAULT_NUM_INFERENCE_STEPS)
    parser.add_argument('--quant_mode', type=str, default='nf4', choices=['nf4', 'none'])
    parser.add_argument('--repo_id_layerdiff', type=str, default=None)
    parser.add_argument('--repo_id_depth', type=str, default=None)
    parser.add_argument('--cpu_offload', action='store_true', default=False)
    parser.add_argument('--no_cpu_offload', action='store_false', dest='cpu_offload')
    parser.add_argument('--group_offload', action='store_true', default=False)
    parser.add_argument('--no_group_offload', action='store_false', dest='group_offload')
    parser.add_argument('--tblr_split', action='store_true', default=True,
                        help='enable left-right part splitting during PSD assembly (default: enabled)')
    parser.add_argument('--no_tblr_split', action='store_false', dest='tblr_split',
                        help='disable left-right part splitting')
    parser.add_argument('--rotate', action='store_true',
                        help='rotate loaded parts during PSD assembly')
    args = parser.parse_args()

    script_dir = osp.dirname(osp.abspath(__file__))
    main_script = osp.join(script_dir, 'inference_psd_quantized.py')
    assemble_script = osp.join(script_dir, 'assemble_psd.py')

    common_model_args = [
        '--srcp', args.srcp,
        '--save_dir', args.save_dir,
        '--seed', str(args.seed),
        '--num_inference_steps', str(args.num_inference_steps),
        '--quant_mode', args.quant_mode,
    ]
    if args.repo_id_layerdiff:
        common_model_args.extend(['--repo_id_layerdiff', args.repo_id_layerdiff])
    if args.repo_id_depth:
        common_model_args.extend(['--repo_id_depth', args.repo_id_depth])
    common_model_args.append('--cpu_offload' if args.cpu_offload else '--no_cpu_offload')
    common_model_args.append('--group_offload' if args.group_offload else '--no_group_offload')

    stage1_cmd = [
        sys.executable,
        main_script,
        *common_model_args,
        '--resolution', str(args.resolution),
        '--resolution_depth', str(DEFAULT_LAYERDIFF_RESOLUTION_DEPTH),
        '--skip_marigold',
        '--skip_psd',
    ]

    stage2_cmd = [
        sys.executable,
        main_script,
        *common_model_args,
        '--resolution', str(args.marigold_resolution),
        '--resolution_depth', str(args.resolution_depth),
        '--skip_layerdiff',
        '--skip_psd',
    ]

    stage3_cmd = [
        sys.executable,
        assemble_script,
        '--srcp', args.srcp,
        '--save_dir', args.save_dir,
    ]
    if args.tblr_split:
        stage3_cmd.append('--tblr_split')
    if args.rotate:
        stage3_cmd.append('--rotate')

    output_dir = output_dir_from_src(args.srcp, args.save_dir)
    if output_dir_has_files(output_dir):
        print(f'Stage 1/3: skipping LayerDiff because output folder is not empty: {output_dir}')
    else:
        print('Stage 1/3: running LayerDiff without Marigold or PSD assembly...')
        subprocess.run(stage1_cmd, check=True)

    print('\nStage 2/3: running Marigold without LayerDiff or PSD assembly...')
    subprocess.run(stage2_cmd, check=True)

    print('\nStage 3/3: assembling PSD in a fresh process...')
    subprocess.run(stage3_cmd, check=True)


if __name__ == '__main__':
    main()
