#' Prepare a Folder of Images for the Assessment of Leaf Area
#'
#' \code{preprocess_batch} prepares images of leaves for assessment using \code{assess}. Not all images require preprocessing. It provides options to crop away coloured margins from an image, to mask out an un-needed scale bar, or to insert a scale bar of a particular size. Either a single image or single directory of images can be processed at once. If the latter, processing can be performed in parallel.
#'
#' @param workers How many cores to use? Default is to use all available minus one. Only relevant when processing a folder, ignored otherwise. Parallelization occurs within Python.
#' @param input_dir The path to a folder (directory) that contains images, that need to be prepared for assessment.
#' @inheritParams preprocess
#'
#' @return No value is returned. The side effect is that processed images are saved in the directory specified in \code{output_dir}.
#'
#' @examples
#' input_dir <- area_example("raw")
#' output_dir <- area_example("prepared")
#'
#' #Demonstrate batch processing
#' \dontrun{
#' preprocess_batch(input_dir, output_dir, crop = 30)
#' preprocess_batch(input_dir, output_dir, workers = 5, crop = 30, mask_scale = 500, mask_offset_x = 0, mask_offset_y = 2600)
#' }

preprocess_batch <- function(input_dir, output_dir, workers = parallel::detectCores(all.tests = T)-1, crop = 0, red_scale = 0, mask_scale = 0, mask_offset_x = 0, mask_offset_y = 0) {
  path_to_python <- python_version()
  path_to_script <- paste(system.file(package="area"), "LAV_pp.py", sep="/")
  system2(path_to_python, args = paste(shQuote(path_to_script), shQuote(output_dir), "--input_dir ", shQuote(input_dir), "--workers", workers, "-c", crop, "--red_scale", red_scale, "--mask_scale", mask_scale, "--mask_offset_x", mask_offset_x, "--mask_offset_y", mask_offset_y))
}


