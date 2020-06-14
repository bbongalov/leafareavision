#!/usr/bin/env python

import argparse
import multiprocessing
import os

from leafareavision import EstimateLeafArea

# parse the arguments
parser = argparse.ArgumentParser(description="Pre-process images of leaves so that their areas can be assessed.")
parser.add_argument("output_dir", type=str, help="Add a directory where to save the output. Respects tilde expansion.")
parser.add_argument("input", type=str, help="Path to an image or a directory of images. Respects tilde expansion.")
parser.add_argument("-c", "--crop", type=int,
                    help="Number of pixels to crop off the margins of the image? Cropping occurs before the other "
                         "operations, so that they are performed on the cropped image.", default=0)
parser.add_argument("--red_scale", type=int, help="How many pixels wide should the side of the scale should be?",
                    default=0)
parser.add_argument("--mask_scale", type=int, help="How many pixels should each side of the masking window be?",
                    default=0)
parser.add_argument("--mask_offset_x", type=int,
                    help="Offset for positioning the masking window in number of pixels "
                         "from right to left of the image",
                    default=0)
parser.add_argument("--mask_offset_y", type=int,
                    help="Offset for positioning the masking window in number of pixels from "
                         "top to bottom of the image",
                    default=0)
parser.add_argument("-w", "--workers", type=int,
                    help="How many cores to use? Default is to use all available minus one. "
                         "Only relevant when processing a folder, ignored otherwise.",
                    default = multiprocessing.cpu_count() - 1)
args = parser.parse_args()


# Usage:
# To pre-process a single image
# python3 LAV_pp.py "~/Desktop/temp/out" --img "~/Desktop/temp/BEL-T20-B1S-L10.jpg" \
#                   -c 300 --red_scale 200 --mask_scale 1000 --mask_offset_x 300 --mask_offset_y 300
#
# To pre-process a folder full of images
# python3 LAV_pp.py "~/Desktop/temp/out" --input_dir "~/Desktop/temp" \
#                   -c 300 --red_scale 200 --mask_scale 1000 --mask_offset_x 300 --mask_offset_y 300 -w 2

if __name__ == '__main__':
    estimator = EstimateLeafArea()
    output_dir = os.path.abspath(args.output_dir)
    if not os.path.exists(output_dir):
        estimator.output_dir = output_dir
        os.makedirs(output_dir)
        print(f'directory {output_dir} created')
    else:
        raise NameError(
            "Output directory already exists. Output files may overwrite existing files. "
            "Please choose a different output directory.")

    if os.path.split(os.path.abspath(args.input))[0] == output_dir:
        raise NameError(
            'You have provided identical paths for the source and destination directories. '
            'This would cause your files to be overwritten. Execution has been halted. ')

    estimator.crop = args.crop
    estimator.red_scale = args.red_scale
    estimator.mask_scale = args.mask_scale
    estimator.mask_offset_x = args.mask_offset_x
    estimator.mask_offset_y = args.mask_offset_y
    estimator.workers = args.workers

    estimator.preprocess(args.input)