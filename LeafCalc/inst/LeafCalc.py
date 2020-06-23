#!/usr/bin/env python3

import argparse
import sys
import multiprocessing
import os
import tempfile
import cv2
import numpy as np
import pandas as pd
from exif import Image
from pandas.core.frame import DataFrame
from skimage import measure


class EstimateLeafArea:
    """Calculate leaf area."""

    def __init__(self, red_scale: int = 0, red_scale_pixels: int = 0, mask_pixels: int = 0,
                 mask_scale: int = 0, mask_offset_y: int = 0, mask_offset_x: int = 0,
                 threshold: int = 120, cut_off: int = 10000, output_dir: str = tempfile.TemporaryDirectory().name,
                 crop: int = 0, combine: bool = True, res: int = 0,
                 workers: int = multiprocessing.cpu_count() - 1):
        """
        Initiate (default) variables.
        @param red_scale: whether or not to add a red scale
        @param red_scale_pixels: how many pixels wide the side of the scale should be
        @param mask_scale: whether to mask an existing scale
        @param mask_offset_x: offset for the masking window in number of pixels from top to bottom of the image
        @param mask_offset_y: offset for the masking window in number of pixels from right to left of the image
        @param mask_pixels: how many pixels each side of the masking window should be
        @param threshold: value for contrast analysis
        @param cut_off: patches below this number of pixels will not be counted
        @param output_dir: where to save the images
        @param crop: remove the edges of the image
        @param combine: combine all patches into a single LA estimate T/F
        @param res: specify resolution manually
        @param workers: how many cores to use for multiprocessing; def: all but one
        """
        self.red_scale = red_scale
        self.red_scale_pixels = red_scale_pixels
        self.mask_pixels = mask_pixels
        self.mask_scale = mask_scale
        self.mask_offset_y = mask_offset_y
        self.mask_offset_x = mask_offset_x
        self.threshold = threshold
        self.cut_off = cut_off
        self.output_dir = output_dir
        self.crop = crop
        self.combine = combine
        self.res = res
        self.workers = workers

    def estimate(self, img: str) -> DataFrame:
        """
        Estimate leaf area for a given image or directory of images.

        TO DO: filter images only in the folder - ask the user for extension?

        @param img: path to the scan or images folder. respects tilde expansion
        @return pandas DF with the file name of the input and the estimated area(s)
        """

        if os.path.isfile(img):
            # read the image resolution
            if not self.res:
                with open(os.path.expanduser(img), 'rb') as image_meta:
                    metadata = Image(image_meta)
                if not metadata.has_exif:
                    raise ValueError("Image of unknown resolution. Please specify the res argument in dpi.")
                if not metadata.x_resolution == metadata.y_resolution:
                    raise ValueError(
                        "X and Y resolutions differ in Image. This is unusual, and may indicate a problem.")
                else:
                    self.res = metadata.x_resolution

            # read the scan
            scan = cv2.imread(os.path.expanduser(img))

            # transfer to grayscale
            scan = cv2.cvtColor(scan, cv2.COLOR_BGR2GRAY)

            # classify leaf and background
            if self.threshold < 0 or self.threshold > 255:
                raise ValueError("Threshold must be an integer between 0 and 255.")
            scan = cv2.threshold(scan, self.threshold, 255, cv2.THRESH_BINARY_INV)[1]

            # label leaflets
            leaflets = measure.label(scan, background=0)

            # count number of pixels in each label
            leaflets = np.unique(leaflets, return_counts=True)

            # create mask to remove dirt and background
            mask = np.ones(len(leaflets[1]), dtype=bool)

            # remove small patches
            if self.cut_off < 0:
                raise ValueError("cutoff for small specks must not be negative.")
            mask[leaflets[1] < self.cut_off] = False

            # remove background pixels
            mask[leaflets[0] == 0] = False  # background is labeled as 0

            # apply mask
            areas = leaflets[1][mask]

            # convert from pixels to cm2
            res = self.res / 2.54  # 2.54 cm in an inch
            res = res * res  # pixels per cm^2
            areas = areas / res

            # save image
            if self.output_dir:
                write_to = os.path.join(os.path.expanduser(self.output_dir), os.path.basename(img))
                cv2.imwrite(write_to, scan)

            if self.combine:
                return pd.DataFrame(data={'filename': [img], 'Area': [areas.sum()]})
            else:
                return pd.DataFrame(data={'filename': [img] * areas.shape[0], 'Area': areas})
        elif os.path.isdir(img):
            # obtain a list of images
            images = os.listdir(img)
            images = [os.path.join(img, i) for i in images]

            # create a workers pool and start processing
            pool = multiprocessing.Pool(self.workers)
            results = pool.map(self.estimate, images)
            pool.close()
            pool.join()

            # unify the results into a single dataframe
            return pd.concat(results)
        else:
            raise ValueError(f'Your input {img} needs to be a path to an image or a directory.')

    def preprocess(self, img):
        """
        Pre-processes an image by cropping its edges, adding a red scale, masking existing scales and converting to jpg.

        @param img: path to the image or folder of images to process
        @return None
        """
        if os.path.isfile(img):
            if not self.output_dir:
                output_dir = f'{os.path.split(img)[0]}/preprocessed'
                os.makedirs(output_dir)

            if os.path.split(img)[0] == self.output_dir:
                raise ValueError(
                    'You have provided identical paths for the source and destination images.' +
                    'This would cause your file to be overwritten. Execution has been halted.')
            # read the image
            scan = cv2.imread(os.path.expanduser(img))
            dims = scan.shape

            # crop the edges
            if self.crop:
                if self.crop < 0:
                    raise ValueError('You have attempted to crop a negative number of pixels.')
                if self.crop > dims[0] or self.crop > dims[1]:
                    raise ValueError('You have attempted to crop away more pixels than are available in the image.')
                scan = scan[self.crop:dims[0] - self.crop, self.crop:dims[1] - self.crop]

            # mask scale
            if self.mask_scale:
                if self.mask_offset_y < 0 or self.mask_offset_x < 0 or self.mask_pixels < 0:
                    raise ValueError("You have attempted to mask a negative number of pixels.")
                if self.mask_offset_y + self.mask_pixels > dims[0] or self.mask_offset_x + self.mask_pixels > dims[1]:
                    raise ValueError("You have attempted to mask more pixels than are available in the image.")

                scan[self.mask_offset_y:self.mask_offset_y + self.mask_pixels,
                     self.mask_offset_x:self.mask_offset_x + self.mask_pixels,
                     0] = 255  # b channel
                scan[self.mask_offset_y:self.mask_offset_y + self.mask_pixels,
                     self.mask_offset_x:self.mask_offset_x + self.mask_pixels,
                     1] = 255  # g channel
                scan[self.mask_offset_y:self.mask_offset_y + self.mask_pixels,
                     self.mask_offset_x:self.mask_offset_x + self.mask_pixels,
                     2] = 255  # r channel

            # add scale
            if self.red_scale:
                if self.red_scale_pixels > dims[0] or self.red_scale_pixels > dims[1]:
                    raise ValueError("You have attempted to place a scale bar beyond the margins of the image.")
                scan[0:self.red_scale_pixels, 0:self.red_scale_pixels, 0] = 0  # b channel
                scan[0:self.red_scale_pixels, 0:self.red_scale_pixels, 1] = 0  # g channel
                scan[0:self.red_scale_pixels, 0:self.red_scale_pixels, 2] = 255  # red channel

            # file name
            file_name = os.path.basename(img)
            file_name = f'{os.path.splitext(file_name)[0]}.jpg'
            file_name = os.path.join(os.path.expanduser(self.output_dir), file_name)

            # save as jpg
            cv2.imwrite(file_name, scan)
        elif os.path.isdir(img):
            images = os.listdir(img)
            images = [os.path.join(img, i) for i in images]

            # create a workers pool and start processing
            pool = multiprocessing.Pool(self.workers)
            pool.map_async(self.preprocess, images)
            pool.close()
            pool.join()
        else:
            raise ValueError(f'Your input {img} needs to be either a file or a directory')


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