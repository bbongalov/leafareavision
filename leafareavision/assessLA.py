#!/usr/bin/env python3

import argparse
import multiprocessing
import os

from leafareavision import EstimateLeafArea

# Parse the arguments
parser = argparse.ArgumentParser(description="Assess images of leaves to determine their areas.")
parser.add_argument("input", type=str,
                    help="Path to image or folder with images. Respects tilde expansion.")
parser.add_argument("--output_dir", type=str,
                    help="Add a directory where to save the output. Respects tilde expansion.")
parser.add_argument("-t", "--threshold", type=int,
                    help="a value between 0 (black) and 255 (white) for classification of background and leaf pixels. "
                         "Default = 120",
                    default=120)
parser.add_argument("--cut_off", type=int,
                    help="Clusters with fewer pixels than this value will be discarded. Default is 10000",
                    default=10000)
parser.add_argument("-c", "--combine", type=bool,
                    help="If true the total area will be returned; otherwise each segment will be returned separately",
                    default=False)
parser.add_argument("--res", type=int,
                    help="image resolution, in dots per inch (DPI); "
                         "if False the resolution will be read from the exif tag",
                    default=0)
parser.add_argument("-w", "--workers", type=int,
                    help="How many cores to use? Default is to use all available minus one. "
                         "Only relevant when assessing a folder, ignored otherwise.",
                    default=multiprocessing.cpu_count() - 1)
parser.add_argument('--csv', type=str, help='name of output csv (to be saved in pwd)')
args = parser.parse_args()


# Usage:
# get the help message
# python3 assessLA.py -h
#
# To assess the leaf area in a single image
# python3 assessLA.py --output_dir "~/Desktop/temp/processed" --input "~/Desktop/temp/out/BEL-T20-B1S-L10.jpg" --res 300
# python3 assessLA.py --input "~/Desktop/temp/out/BEL-T20-B1S-L10.jpg" # this version does not save the processed image

# To assess leaf area of a folder full of images
# python3 assessLA.py --output_dir "~/Desktop/temp/processed" --input "~/Desktop/temp/out" -w 2 -c True
# python3 assessLA.py  --input "~/Desktop/temp/out" --res 300 -w 2 -c True # does not save the processed images.

if __name__ == '__main__':
    estimator = EstimateLeafArea()

    if args.output_dir:
        output_dir = os.path.abspath(args.output_dir)
        estimator.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f'directory {output_dir} created')
        else:
            raise NameError("Output directory already exists. Output files may overwrite existing files. "
                            "Please choose a different output directory.")

        if os.path.split(os.path.abspath(args.input))[0] == output_dir:
            raise NameError(
                'You have provided identical paths for the source and destination directories. '
                'This would cause your files to be overwritten. Execution has been halted. ')

    estimator.res = args.res
    estimator.workers = args.workers
    estimator.combine = args.combine
    estimator.cut_off = args.cut_off
    estimator.threshold = args.threshold

    output = estimator.estimate(args.input)
    print(output)
    if args.csv:
        output.to_csv(args.csv)
