#!/usr/bin/env python3
"""
A class to process images for leaf area.

Boris Bongalov, Tim C.E Paine, Sabine Both
"""

import multiprocessing
import os
from glob import glob

import cv2
import numpy as np
import pandas as pd
from exif import Image
from pandas.core.frame import DataFrame
from skimage import measure
import tempfile

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
            images = glob(img, recursive=True)

            # create a workers pool and start processing
            pool = multiprocessing.Pool(self.workers)
            results = pool.map_async(self.estimate, images)
            pool.close()
            pool.join()

            # unify the results into a single dataframe
            return pd.concat(results._value)
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
            fname = os.path.basename(img)
            fname = f'{os.path.splitext(fname)[0]}.jpg'
            fname = os.path.join(os.path.expanduser(self.output_dir), fname)

            # save as jpg
            cv2.imwrite(fname, scan)
        elif os.path.isdir(img):
            images = glob(img, recursive=True)

            # create a workers pool and start processing
            pool = multiprocessing.Pool(self.workers)
            pool.map_async(self.preprocess, images)
            pool.close()
            pool.join()
        else:
            raise ValueError(f'Your input {img} needs to be either a file or a directory')
