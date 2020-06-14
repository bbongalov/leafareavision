import sys
if sys.version_info[0] < 3 |(sys.version_info[0] == 3 & sys.version_info[1] < 5):
    raise Exception("Python 3.5 or a more recent version is required.")
try:
    import os
except ImportError:
    sys.exit("This function requires the Python module 'os'. Hint: Install it by typing 'python3 -m pip install os --user' (without the quotation marks) at the command line.")
try:
    import cv2
except ImportError:
    sys.exit("This function requires the Python module 'cv2'. Hint: Install it by typing 'python3 -m pip install opencv-python --user' (without the quotation marks) at the command line.")
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
try:
    import exif
except ImportError:
    sys.exit("This function requires the Python module 'exif'. Hint: Install it by typing 'python3 -m pip install exif --user' (without the quotation marks) at the command line.")
try:
    from PIL import Image
except ImportError:
    sys.exit("This function requires the Python module 'pillow'. Hint: Install it by typing 'python3 -m pip install pillow --user' (without the quotation marks) at the command line.")

# parse the arguments
parser = argparse.ArgumentParser(description="Pre-process images of leaves so that their areas can be assessed.")
parser.add_argument("output_dir", type=str, help="Add a directory where to save the output. Respects tilde expansion.")
source = parser.add_mutually_exclusive_group()
source.add_argument("--img", type=str, help="Path to the image of interest. Respects tilde expansion.")
source.add_argument("--input_dir", type=str, help="Folder to list images in. Respects tilde expansion.")
parser.add_argument("-c", "--crop", type=int,
                    help="Number of pixels to crop off the margins of the image? Cropping occurs before the other operations, so that they are performed on the cropped image.", default=0)
parser.add_argument("--red_scale", type=int, help="How many pixels wide should the side of the scale should be?",
                    default=0)
parser.add_argument("--mask_scale", type=int, help="How many pixels should each side of the masking window be?",
                    default=0)
parser.add_argument("--mask_offset_x", type=int,
                    help="Offset for positioning the masking window in number of pixels from right to left of the image",
                    default=0)
parser.add_argument("--mask_offset_y", type=int,
                    help="Offset for positioning the masking window in number of pixels from top to bottom of the image",
                    default=0)
parser.add_argument("-w", "--workers", type=int,
                    help="How many cores to use? Default is to use all available minus one. Only relevant when processing a folder, ignored otherwise.", default = multiprocessing.cpu_count() - 1)
args = parser.parse_args()


# Usage:
# To pre-process a single image
# python3 LAV_pp.py "out" --img "data/BEL-T20-B1S-L10.jpg" -c 300 --red_scale 200 --mask_scale 1000 --mask_offset_x 300 --mask_offset_y 300
#
# To pre-process a folder full of images
# python3 LAV_pp.py "out2" --input_dir "data" -c 300 --red_scale 200 --mask_scale 1000 --mask_offset_x 300 --mask_offset_y 300 -w 2

# Define the function that processes the images
def preprocess(img, output_dir, crop, red_scale, mask_scale, mask_offset_x, mask_offset_y):
    """
    Function that pre-processes an image by cropping its edges, adding a red scale, masking existing scales and converting to jpg
    :param img - path to the image of interest. sRespects tilde expansion.
    :param output_dir - where to save the output. Respects tilde expansion.
    :param crop - Should the margins of the image be cropped? Cropping occurs before the other operations, so that they are performed on the cropped image. Value is one integer; number of pixels to be removed from (top, bottom, left, right) of the image.
    :param red_scale - How many pixels wide should the side of the scale should be?
    :param mask_scale - whether to mask an existing scale
    :param mask_offset_x - offset for positioning the masking window in number of pixels from right to left of the image
    :param mask_offset_y - offset for positioning the masking window in number of pixels from top to bottom of the image
    """
    # read the image resolution
    with open(img, 'rb') as image_meta:
        metadata = exif.Image(image_meta)
    if not metadata.has_exif:
        raise ValueError("Image of unknown resolution. Please specify the res argument in dpi.")
    if not metadata.x_resolution == metadata.y_resolution:
        raise ValueError("X and Y resolutions differ in Image. This is unusual, and may indicate a problem.")
    else:
        res = metadata.x_resolution

    # read the image
    scan = cv2.imread(img)
    dims = scan.shape

    # crop the edges
    if crop > 0:
        if crop > dims[0] or crop > dims[1]:
            raise ValueError('You have attempted to crop away more pixels than are available in the image.')
        scan = scan[crop:dims[0] - crop, crop:dims[1] - crop]

    # mask scale
    if mask_scale > 0:
        if mask_offset_y < 0 or mask_offset_x < 0 or mask_scale < 0:
            raise ValueError("You have attempted to mask a negative number of pixels.")
        if mask_offset_y + mask_scale > dims[0] or mask_offset_x + mask_scale > dims[1]:
            raise ValueError("You have attempted to mask more pixels than are available in the image.")
        scan[mask_offset_y:mask_offset_y + mask_scale, mask_offset_x:mask_offset_x + mask_scale, 0] = 255  # b channel
        scan[mask_offset_y:mask_offset_y + mask_scale, mask_offset_x:mask_offset_x + mask_scale, 1] = 255  # g channel
        scan[mask_offset_y:mask_offset_y + mask_scale, mask_offset_x:mask_offset_x + mask_scale, 2] = 255  # r channel

    # add scale
    if red_scale > 0:
        if red_scale > dims[0] or red_scale > dims[1]:
            raise ValueError("You have attempted to place a scale bar beyond the margins of the image.")
        scan[0:red_scale, 0:red_scale, 0] = 0  # b channel
        scan[0:red_scale, 0:red_scale, 1] = 0  # g channel
        scan[0:red_scale, 0:red_scale, 2] = 255  # red channel

    # file name
    fname = os.path.basename(img)
    fname = os.path.splitext(fname)[0]
    fname = fname + ".jpg"
    fname = os.path.join(output_dir, fname)

    # save as jpg
    cv2.imwrite(fname, scan)

    # Set the resolution in the image. This is a hack to make up for the fact that openCV destroys the resolution data of the image!
#    im = Image.open(fname)
#    im.x_resolution = res
#    im.y_resolution = res
#    with open(fname, 'wb') as new_image_file:
#        new_image_file.write(im.get_file())

    # TODO: Currently, this DOES wrote resolution into the file ( I can see it in preview), but it DOES NOT do so in a way that's then visible n the assessment script. So wierd!

# Define a wrapper for preprocess that allows it to be run in parallel
def preprocess_multicore(args):
    """
    a wrapper for preprocess() so that it can accept listed arguments from map_async
    there might be a more intelligent work-around. THis is not to be called by the user.
    """
    return preprocess(args[0], args[1], args[2], args[3], args[4], args[5], args[6])

# Define a function that does the parallel analysis of all files in a folder.
def preprocess_batch(input_dir, output_dir, workers, crop, red_scale, mask_scale, mask_offset_x, mask_offset_y):
    """
    :param input_dir: folder to list images in; specifying file format (e.g. *.jpg) is expected
    :param output_dir - where to save the output. Respects tilde expansion.
    :param workers: how many cores to use - default is to use all available minus one.
    :param crop - four integers; number of pixels to be removed from (top, bottom, left, right) of the image. Cropping occurs before the other operations, so that they are performed
    on the cropped image.
    :param red_scale - How many pixels wide should the side of the scale should be?
    :param mask_scale - whether to mask an existing scale
    :param mask_offset_x - offset for positioning the masking window in number of pixels from right to left of the image
    :param mask_offset_y - offset for positioning the masking window in number of pixels from top to bottom of the image
    :param mask_pixels - how many pixels each side of the masking window should be
    """

    # obtain a list of images
    images = glob(input_dir, recursive=True)

    # create list of all arguments to pass
    arguments = []
    for image in images:
        arguments.append([image, output_dir, crop, red_scale, mask_scale, mask_offset_x, mask_offset_y])

    # create a workers pool and start processing
    if args.workers > multiprocessing.cpu_count():
        args.workers = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(workers)
    pool.map_async(preprocess_multicore, arguments)
    pool.close()
    pool.join()


def main(args):
    output_dir = os.path.expanduser(args.output_dir)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
        print('directory', output_dir, 'created')
    else:
        raise NameError("Output directory already exists. Output files may overwrite existing files. Please choose a different output directory.")

    if args.img:
        if os.path.dirname(args.img) == output_dir:
            raise NameError(
                'You have provided identical paths for the source and destination images. This will cause your file to be overwritten. Execution has been halted. ')
        preprocess(img=os.path.expanduser(args.img), output_dir=output_dir, crop=args.crop, red_scale=args.red_scale,
                   mask_scale=args.mask_scale, mask_offset_x=args.mask_offset_x, mask_offset_y=args.mask_offset_y)
    elif args.input_dir:
        input_dir = os.path.expanduser(args.input_dir)
        if input_dir == output_dir:
            raise NameError(
                'You have provided identical paths for the source and destination directories. This would cause your files to be overwritten. Execution has been halted. ')
        input_dir = os.path.join(input_dir, '*.jpg')
        # TODO: currently the batch processing FAILS! it makes a folder, but does not process any images into it!
        preprocess_batch(input_dir=input_dir, output_dir=args.output_dir, workers=args.workers, crop=args.crop,
                         red_scale=args.red_scale, mask_scale=args.mask_scale, mask_offset_x=args.mask_offset_x,
                         mask_offset_y=args.mask_offset_y)


if __name__ == '__main__':
    main(args)
