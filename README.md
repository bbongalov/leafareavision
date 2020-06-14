# leafareavision
leafareavision is a simple collection of functions to aid with the estimation of leaf area from scanned images. It can process single scnas or multiple images in a directory using one or multople cores. leafareavision returns estimates for all leaf fragments in an image or for each of them individually. 

leafareavision is written in python and utilises the power of the [OpenCV](https://opencv.org/) library to quickly analyse your images. You can interface with the functions via python, R or command line interfaces to best match your workflow. Instructions on how to get going can be found below. 

This package was developed by [Boris Bongalov](https://bongalov.com) with substantial input from [Sabine Both](https://www.une.edu.au/staff-profiles/ers/sabine-both) and [Tim Paine](https://www.une.edu.au/staff-profiles/ers/timothy-paine). Consider referencing our article introducing the tool if you find it useful:

Paine CET, Bongalov B, and Both S. "How big are these leaves? Optimal methods for assessing leaf area" (in prep).

Please report any bugs or problems to [boris@bongalov.com](mailto:boris@bongalov.com). Pull requests are welcome!

# Installation

leafareavision can be installed via [pip](https://pip.pypa.io/en/stable/). It requires you to have python 3 set up on your system, which should be already in your computer if you are using Mac, Linux or updated version of Windows 10. All additional packages that leafareavision needs will be automatically installed by pip. 

```
pip3 install https://github.com/bbongalov/leafareavision/archive/master.zip
```

# Functions
The leafareavision package ships two functions that you might find useful. The estimate() function analysises a single scan and the batch() function handles a whole directory on multiple cores. 

## preprocess()
The preprocess() function reads an image, giving the user the opportunity to edit it to prepare it for analysis. Common modifications include placing a mask over an existing scale bar, adding a scale bar of a given size, and cropping away the margins of an image. 

The function accepts the following arguments: 
* img: path to the scan
* path: folder to save the modified image in; specifying file format (e.g. *.jpg) is expected; defaults to jpg files in the current directory (i.e. "./*jpg")
* crop: False, in which case no cropping is done, or four integers, giving the number of pixels to be removed form (top, bottom, left, right) of the image
* red_scale: whether a scale bar should be inserted into the image, as required by some area estimating routines. 
* red_scale_pixels: if a scale bar should be inserted into the image, how many pixels should it have on each side.  
* mask_scale: whether to mask an existing scale. Most routines, including leafareavision, do NOT need one to be present.
* mask_offset_x: offset for positioning the masking window in number of pixels from right to left of the image, defaults to 0
* mask_offset_y: offset for positioning the masking window in number of pixels from top to bottom of the image, defaults to 0
* mask_pixels: how many pixels each side of the masking window should be, defaults to 500

## estimate()
The estimate() function reads an image and returns a dataframe with the image name and leaf area estimate. It combines all leaf pathces by default but it can also return the area of each leaf(let) if needed. Currently, there is no way to know which area corresponds to each leaf fragment, but this functionality may be added in the future. 

The function accepts the following arguments: 
* img: path to the scan
* threshold: a value between 0 (black) and 255 (white) for classification of background and leaf pixels
* cut_off: integer; clusters with nimber of pixels lower than this value will be discarded
* output_dir: path, if specified, the classified image will be saved there
* combine: boolean; if true the total area will be returned; otherwise each segment will be returned separately
* res: image resolution; if False the resolution will be read from the exif tag

## batch()

The batch() function lists all images from a specified directory and calls the estimate() function on each image. It processes the images on multiple cores to speed up the analysis. By default, it uses all but one cores in your system. If you are limited by RAM or wish to do other computationally-intensive work while you are processing the images, you may wish to reduce the number of cores made available to the function. All arguments that modify the behaviour of estimate() can be passed onto batch() with the exception of img. In addition, the following arguments can be passed to batch():
* path: folder to list images in; specifying file format (e.g. *.jpg) is expected; defaults to jpg files in the current directory (i.e. "./*jpg")
* workers: how many cores to use - default is to use one


# python interface
Once the package is installed, its functions can be called directly in Python:

```python 
# import the package
import leafareavision

# process a single scan and save the estimate to a variable and the processed image to the current working directory
est = leafareavision.estimate("./images/image.jpg", output_dir="./")

# process all jpg images from the ./images folder and save the estimates to a variable while the processed scans will be saved to the "processed" folder
est = leafareavision.batch("./images/*jpg", output_dir="./")

```

# command line interface

leafareavision includes two command line tools to processes single images or batch process entire directories. On Mac and Linux, pip will make those available to your command line interface as long as your path is set up correctly. pip will issue a warning if this is not the case. I am not sure how thigs work on windows systems, feedback from your experiments is appreciated. 

Running the scripts with an -h argument will print help message with instructions on how to use them.

For individual scnas use scanLA:
```bash
usage: scanLA [-h] [-threshold THRESHOLD] [-cut_off CUT_OFF]
              [-output_dir OUTPUT_DIR] [-crop_top CROP_TOP]
              [-crop_bottom CROP_BOTTOM] [-crop_left CROP_LEFT]
              [-crop_right CROP_RIGHT] [-combine COMBINE] [-res RES]
              [-csv CSV]
              img

Estimate the area of a scanned leaf

positional arguments:
  img                   path to the scan

optional arguments:
  -h, --help            show this help message and exit
  -threshold THRESHOLD  a value between 0 (black) and 255 (white) for
                        classification of background and leaf pixels
  -cut_off CUT_OFF      integer; clusters with number of pixels lower than
                        this value will be discarded
  -output_dir OUTPUT_DIR
                        path, if specified, the classified image will be saved
                        there
  -crop_top CROP_TOP    four integers; number of pixels to be removed form
                        (top, bottom, left, right) of the image
  -crop_bottom CROP_BOTTOM
                        four integers; number of pixels to be removed form
                        (top, bottom, left, right) of the image
  -crop_left CROP_LEFT  four integers; number of pixels to be removed form
                        (top, bottom, left, right) of the image
  -crop_right CROP_RIGHT
                        four integers; number of pixels to be removed form
                        (top, bottom, left, right) of the image
  -combine COMBINE      boolean; if true the total area will be returned;
                        otherwise each segment will be returned separately
  -res RES              image resolution; if False the resolution will be read
                        from the exif tag
  -csv CSV              path to a csv file to save the output

```

For folders of scans use batchLA:
```bash
usage: batchLA [-h] [-workers WORKERS] [-threshold THRESHOLD]
               [-cut_off CUT_OFF] [-output_dir OUTPUT_DIR]
               [-crop_top CROP_TOP] [-crop_bottom CROP_BOTTOM]
               [-crop_left CROP_LEFT] [-crop_right CROP_RIGHT]
               [-combine COMBINE] [-res RES] [-csv CSV]
               path

Estimate the area of a scanned leaves in batch

positional arguments:
  path                  folder to list images in; specifying file format (e.g.
                        *.jpg) is expected

optional arguments:
  -h, --help            show this help message and exit
  -workers WORKERS      how many cores to use - default is all available but
                        one
  -threshold THRESHOLD  a value between 0 (black) and 255 (white) for
                        classification of background and leaf pixels
  -cut_off CUT_OFF      integer; clusters with number of pixels lower than
                        this value will be discarded
  -output_dir OUTPUT_DIR
                        path, if specified, the classified image will be saved
                        there
  -crop_top CROP_TOP    four integers; number of pixels to be removed form
                        (top, bottom, left, right) of the image
  -crop_bottom CROP_BOTTOM
                        four integers; number of pixels to be removed form
                        (top, bottom, left, right) of the image
  -crop_left CROP_LEFT  four integers; number of pixels to be removed form
                        (top, bottom, left, right) of the image
  -crop_right CROP_RIGHT
                        four integers; number of pixels to be removed form
                        (top, bottom, left, right) of the image
  -combine COMBINE      boolean; if true the total area will be returned;
                        otherwise each segment will be returned separately
  -res RES              image resolution; if False the resolution will be read
                        from the exif tag
  -csv CSV              path to a csv file to save the output

```

# R interface

You can call python functions from R using the excellent [reticulate](https://rstudio.github.io/reticulate/) package. This interface is not extensively tested, please report any bugs as you encounter them. 

Install reticulate from CRAN:
```R
install.packages("reticulate")
```

Load the package and specify the python path if needed. On many linux machine the python command currently calls python 2.7. In order to interface with python 3, you may need to specify the python 3 path:

```R
library(reticulate)
use_python("/usr/bin/python3.7")
```

You can load the leafareavision to an R object and call the package funtions from there.

```R
leafareavision <- import("leafareavision")

single_image <- leafareavision$estimate(img = "/images/scan.jpg")

many_images <- leafareavision$batch(path = "/images/*jpg")

```









