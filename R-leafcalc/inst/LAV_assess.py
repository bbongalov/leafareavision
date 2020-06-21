import sys
if sys.version_info[0] < 3 |(sys.version_info[0] == 3 & sys.version_info[1] < 5):
    raise Exception("Python 3.5 or a more recent version is required.")
try:
    import os
except ImportError:
    sys.exit("This function requires the Python module 'os'. Hint: Install it by typing 'python3 -m pip install os --user' (without the quotation marks) at the command line.")
try:
    import numpy as np
except ImportError:
    sys.exit("This function requires the Python module 'numpy'. Hint: Install it by typing 'python3 -m pip install numpy --user' (without the quotation marks) at the command line.")
try:
    import pandas as pd
except ImportError:
    sys.exit("This function requires the Python module 'pandas'. Hint: Install it by typing 'python3 -m pip install pandas --user' (without the quotation marks) at the command line.")
try:
    import cv2
except ImportError:
    sys.exit("This function requires the Python module 'cv2'. Hint: Install it by typing 'python3 -m pip install opencv-python --user' (without the quotation marks) at the command line.")
try:
    from exif import Image
except ImportError:
    sys.exit("This function requires the Python module 'exif'. Hint: Install it by typing 'python3 -m pip install exif --user' (without the quotation marks) at the command line.")
try:
    from skimage import measure
except ImportError:
    sys.exit("This function requires the Python module 'scikit-image'. Hint: Install it by typing 'python3 -m pip install scikit-image --user' (without the quotation marks) at the command line.")
try:
    from glob import glob
except ImportError:
    sys.exit("This function requires the Python module 'glob'. Hint: Install it by typing 'python3 -m pip install glob --user' (without the quotation marks) at the command line.")
try:
    import multiprocessing
except ImportError:
    sys.exit("This function requires the Python module 'multiprocessing'. Hint: Install it by typing 'python3 -m pip install multiprocessing --user' (without the quotation marks) at the command line.")
try:
    import argparse
except ImportError:
    sys.exit("This function requires the Python module 'argparse'. Hint: Install it by typing 'python3 -m pip install argparse --user' (without the quotation marks) at the command line.")

# Parse the arguments
parser = argparse.ArgumentParser(description="Assess images of leaves to determine their areas.")
source = parser.add_mutually_exclusive_group()
source.add_argument("--img", type=str, help="Path to the image of interest. Respects tilde expansion.")
source.add_argument("--input_dir", type=str,
                    help="Folder to list images in. Respects tilde expansion.")
parser.add_argument("--output_dir", type=str, help="The directory where to save the processed images. Respects tilde expansion. By default, processed images are not saved", default = "")
parser.add_argument("-t", "--threshold", type=int,
                    help="A value between 0 (black) and 255 (white) for classification of background and leaf pixels. Default = 120", default=120)
parser.add_argument("--cut_off", type=int, help="Clusters with fewer pixels than this value will be discarded. Default is 10000",
                    default=10000)
parser.add_argument("-c", "--combine", type=bool, help="If true the total area will be returned; otherwise each segment will be returned separately",
                    default=False)
parser.add_argument("--res", type=int,
                    help="Image resolution, in dots per inch (DPI); if False the resolution will be read from the exif tag",
                    default=0)
parser.add_argument("-w", "--workers", type=int,
                    help="How many cores to use? Default is to use all available minus one. Only relevant when assessing a folder, ignored otherwise.", default = multiprocessing.cpu_count() - 1)
args = parser.parse_args()


# Usage:
# get the help file
# python3 LAV_assess.py -h
#
# To assess the leaf area in a single image
# python3 LAV_assess.py --output_dir "processed" --img "out/BEL-T20-B1S-L10.jpg" --res 300
# python3 LAV_assess.py --img "out/BEL-T20-B1S-L10.jpg" # this version does not save the processed image

# To assess leaf area of a folder full of images
# python3 LAV_assess.py --output_dir "processed" --input_dir "out" -w 2 -c True
# python3 LAV_assess.py  --input_dir "out" --res 300 -w 2 -c True # this version does not save the processed images.



def estimate(img, threshold, cut_off, output_dir, combine, res):
    """
    estimate leaf area for a given image
    :param img: path to the scan. respects tilde expansion.
    :param threshold: a value between 0 (black) and 255 (white) for classification of background and leaf pixels
    :param cut_off: integer; clusters with nimber of pixels lower than this value will be discarded
    :param output_dir: path, if specified, the classified image will be saved there, respects tilde expansion
    :param combine: boolean; if true the total area will be returned; otherwise each segment will be returned separately
    :param res: image resolution; if False the resolution will be read from the exif tag
    :return: pandas dataframe with the file name of the input and the estimated area(s)
    """

    # read the image resolution
    if not res:
        with open(os.path.expanduser(img), 'rb') as image_meta:
            metadata = Image(image_meta)
        if not metadata.has_exif:
            raise ValueError("Image of unknown resolution. Please specify the res argument in dpi.")
        if not metadata.x_resolution == metadata.y_resolution:
            raise ValueError("X and Y resolutions differ in Image. This is unusual, and may indicate a problem.")
        else:
            res = metadata.x_resolution

            # read the scan
    scan = cv2.imread(os.path.expanduser(img))

    # transfer to grayscale
    scan = cv2.cvtColor(scan, cv2.COLOR_BGR2GRAY)

    # classify leaf and background
    if threshold < 0 or threshold > 255:
        raise ValueError("Threshold must be an integer between 0 and 255.")
    scan = cv2.threshold(scan, threshold, 255, cv2.THRESH_BINARY_INV)[1]

    # label leaflets
    leaflets = measure.label(scan, background=0)

    # count number of pixels in each label
    leaflets = np.unique(leaflets, return_counts=True)

    # create mask to remove dirt and background
    mask = np.ones(len(leaflets[1]), dtype=bool)

    # remove small patches
    if cut_off < 0:
        raise ValueError("cutoff for small specks must not be negative.")
    mask[leaflets[1] < cut_off] = False

    # remove background pixels
    mask[leaflets[0] == 0] = False  # background is labeled as 0

    # apply mask
    areas = leaflets[1][mask]

    # convert from pixels to cm^2
    res = res / 2.54  # 2.54 cm in an inch
    res = res * res   # pixels per cm^2
    areas = areas / res

    # save image
    if output_dir:
        write_to = os.path.join(output_dir, os.path.basename(img))
        cv2.imwrite(write_to, scan)

    if combine:
        return pd.DataFrame(data={'Area': [areas.sum()]})
    else:
        return pd.DataFrame(data={'Area': areas})
    # TODO: It seems that the combine argument is not working - the areas are always returned combined - one area per image!
    
    
def estimate_multicore(args):
    """
    a wrapper for estimate() so that it can accept listed arguments from map_async
    there might be a more intelligent work-around
    """
    return estimate(args[0], args[1], args[2], args[3], args[4], args[5])

def batch(input_dir, workers, threshold, cut_off, output_dir, combine, res):
    """
    :param input_dir: folder to list images in; specifying file format (e.g. *.jpg) is expected
    :param workers: how many cores to use - default is to use all available minus one.
    :param threshold: a value between 0 (black) and 255 (white) for classification of background and leaf pixels
    :param cut_off: integer; clusters with number of pixels lower than this value will be discarded
    :param output_dir: path, if specified, the classified image will be saved there
    :param combine: boolean; if true the total area will be returned; otherwise each segment will be returned separately
    :param res: image resolution; if False the resolution will be read from the exif tag
    :return: pandas dataframe with the file names of the input and the estimated areas
    """

    # obtain a list of images
    images = glob(input_dir, recursive=True)

    # create list of all arguments to pass
    arguments = []
    for image in images:
        arguments.append([image, threshold, cut_off, output_dir, combine, res])

    # create a workers pool and start processing
    pool = multiprocessing.Pool(workers)
    results = pool.map_async(estimate_multicore, arguments)
    pool.close()
    pool.join()

    # unify the results into a single dataframe
    return pd.concat(results._value)

def main (args):
    if args.output_dir:
        output_dir = os.path.expanduser(args.output_dir)
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
            print('NOTE: Directory', output_dir, 'created')
        else:
            raise NameError(
                "Output directory already exists. Output files may overwrite existing files. Please choose a different output directory.")
        if args.img:
            if os.path.dirname(args.img) == output_dir:
                raise NameError(
                    'You have provided identical paths for the source and destination images. This would cause your file to be overwritten. Execution has been halted. ')
        elif args.input_dir:
            if os.path.expanduser(args.input_dir) == output_dir:
                raise NameError(
                    'You have provided identical paths for the source and destination directories. This would cause your files to be overwritten. Execution has been halted. ')
    if args.img:
        output = estimate(args.img, threshold=args.threshold, cut_off=args.cut_off, output_dir=args.output_dir, combine=args.combine, res=args.res)
    elif args.input_dir:
        input_dir = os.path.expanduser(os.path.join(args.input_dir, '*.jpg'))
        output = batch(input_dir=input_dir, workers=args.workers, threshold=args.threshold, cut_off=args.cut_off, output_dir=args.output_dir, combine=args.combine, res=args.res)
    print(output)
    return output

if __name__ == '__main__':
    main(args)
