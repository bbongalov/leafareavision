#' Prepare an Image of Leaves for the Assessment of Leaf Area
#'
#' \code{preprocess} prepares images of leaves for assessment using \code{assess}. Not all images require preprocessing. It provides options to crop away coloured margins from an image, to mask out an un-needed scale bar, or to insert a scale bar of a particular size. Either a single image or single directory of images can be processed at once. If the latter, processing can be performed in parallel.
#'
#' @param img The path to the image on which you want to prepare for assessment.
#' @param output_dir The directory where to save the processed images, so that they can be assessed using \code{assess}. Respects tilde expansion. This must not be a directory that already exists, so that existing files are not over-written.
#' @param crop Should the margins of the image be cropped? Cropping occurs before the other operations, meaning that they are performed on the cropped image. Value is one integer; number of pixels to be removed from (top, bottom, left, right) of the image. Default = 0.
#' @param red_scale How many pixels wide should the side of the scale should be? Default = 0.
#' @param mask_scale How many pixels should each side of the masking window be? Default = 0.
#' @param mask_offset_x  Offset for positioning the masking window in number of pixels from right to left of the image.
#' @param  mask_offset_y for positioning the masking window in number of pixels from bottom to top of the image.
#'
#' @return No value is returned. The side effect is that the processed image is saved in the directory specified in \code{output_dir}.
#'
#' @examples
#' img <- area_example("raw/img4.jpg")
#' output_dir <- area_example("prepared")
#'
#' \dontrun{
#' preprocess(img, output_dir, crop = 30, mask_scale = 500, mask_offset_x = 00, mask_offset_y = 2600)
#' }


preprocess <- function(img, output_dir, crop = 0, red_scale = 0, mask_scale = 0, mask_offset_x = 0, mask_offset_y = 0) {
  path_to_python <- python_version()
  path_to_script <- paste(system.file(package="area"), "LAV_pp.py", sep="/")

  system2(path_to_python, args = paste(shQuote(path_to_script), shQuote(output_dir), "--img ", shQuote(img),  "-c", crop, "--red_scale", red_scale, "--mask_scale", mask_scale, "--mask_offset_x", mask_offset_x, "--mask_offset_y", mask_offset_y))
}
