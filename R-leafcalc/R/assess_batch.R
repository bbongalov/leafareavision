#' Assess Leaf Area for a Folder of Images
#'
#'This function assesses the area of leaves taken from images. Ideally, the images will be obtained from a flatbed scanner, and will include resolution information in the exif metadata. Images derived from cameras can also be used, but in that case, you will probably need to supply the resolution explictly, using the argument res.
#'
#'
#' @param workers How many cores to use? Default is to use all available minus one. Only relevant when assessing a folder, ignored otherwise. Parallelization occurs within Python.
#' @param input_dir The path to a folder (directory) that contains images, for which you want to assess the leaf area.
#' @inheritParams assess
#'
#' @return The assessed leaf areas for an entire folder of images, in cm^2, is returned as a \code{data.frame}.
#'
#' @examples
#' input_dir <- area_example("prepared")
#' output_dir <- area_example("processed")
#'
#' # If the argument output_dir is omitted,  do not save  processed images
#' assess_batch(input_dir, res = 400, combine = FALSE)
#' \dontrun{
#' assess_batch(input_dir, output_dir = "processed2", cut_off = 10000, res = 400)
#' }
#'
#

assess_batch <- function(input_dir, workers = parallel::detectCores(all.tests = T)-1, threshold = 120, cut_off = 10000, output_dir = NULL, combine = FALSE, res = 300) {
  path_to_python <- python_version()
  path_to_script <- paste(system.file(package="area"), "LAV_assess.py", sep="/")
  args <- paste(shQuote(path_to_script), "--input_dir", shQuote(input_dir), "--workers", workers, "--threshold", threshold, "--cut_off", cut_off, "--res", res)
  if(!is.null(output_dir)){args <- paste(args, "--output_dir", shQuote(output_dir))}
  if(combine){args <- paste(args, "--combine", combine)}

  out <- system2(command = path_to_python, args = args, stdout = TRUE)

  out2 <- out[grep("NOTE: ", out, invert = TRUE)] # drop the directory creation notes
  out2 <- out2[-1] # drop the header row off the output
  out3 <- matrix(unlist(strsplit(out2, " {2,}")), byrow= T, ncol = 3) # THis spilts based on 2 or more spaces in a raow. Which is fine, until someone comes along with a file with 2 more spaces in a row. How to handle this better?
  colnames(out3) <- c('Count', 'Image', 'Area')
  out3 <- data.frame(out3)
  out3[,1] <- 1 + as.numeric(as.character(out3[,1]))
  out3[,3] <- as.numeric(as.character(out3[,3]))
  return(out3)
}

