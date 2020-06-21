#!/usr/bin/env python3

import argparse
import multiprocessing
import os
import sys

from leafcalc import EstimateLeafArea, static


class ErrorParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


# Parse arguments
parser = ErrorParser(prog='LeafCalc.py')
subparsers = parser.add_subparsers(dest='command')
subparsers.required = True

pre_processing_parser = subparsers.add_parser('preprocess',
                                              help='Pre-process images of leaves so that their areas can be assessed.')
pre_processing_parser.add_argument("-c", "--crop", type=int, default=0,
                                   help="Number of pixels to crop off the margins of the image? Cropping occurs before "
                                        "the other operations, so that they are performed on the cropped image.")
pre_processing_parser.add_argument("--red_scale", type=int, default=0,
                                   help="How many pixels wide should the side of the scale should be?")
pre_processing_parser.add_argument("--mask_scale", type=int, default=0,
                                   help="How many pixels should each side of the masking window be?")
pre_processing_parser.add_argument("--mask_offset_x", type=int, default=0,
                                   help="Offset for positioning the masking window in number of pixels from right to "
                                        "left of the image")
pre_processing_parser.add_argument("--mask_offset_y", type=int, default=0,
                                   help="Offset for positioning the masking window in number of pixels from top to "
                                        "bottom of the image")


estimate_parser = subparsers.add_parser('estimate', help='Assess images of leaves to determine their areas.')
estimate_parser.add_argument("-t", "--threshold", type=int, default=120,
                             help="a value between 0 (black) and 255 (white) for classification of background "
                                  "and leaf pixels. Default = 120")
estimate_parser.add_argument("--cut_off", type=int, default=10000,
                             help="Clusters with fewer pixels than this value will be discarded. Default is 10000",)
estimate_parser.add_argument("-c", "--combine", action='store_true',
                             help="If true the total area will be returned; otherwise each segment will "
                                  "be returned separately")
estimate_parser.add_argument("--res", type=int, default=0,
                             help="image resolution, in dots per inch (DPI); if False the resolution will be "
                                  "read from the exif tag")
estimate_parser.add_argument('--csv', type=str, help='name of output csv (to be saved in pwd)')


for p in [pre_processing_parser, estimate_parser]:
    p.add_argument("input", type=str, help="Path to image or folder with images. Respects tilde expansion.")
    p.add_argument("--output_dir", type=str, help="Where to save the output. Respects tilde expansion.")
    p.add_argument("-w", "--workers", type=int, default=multiprocessing.cpu_count() - 1,
                   help="How many cores to use? Default is to use all available minus one. "
                        "Only relevant when assessing a folder, ignored otherwise.")
    p.add_argument("-v", "--verbose", action='store_true', help="Enable verbose screen output.")


where_parser = subparsers.add_parser('example', help='Print the directory where example images are saved.')

args = parser.parse_args()


if __name__ == '__main__':
    estimator = EstimateLeafArea()

    if args.command == 'estimate':
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

    elif args.command == 'preprocess':
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

    elif args.command == 'example':
        print(static)