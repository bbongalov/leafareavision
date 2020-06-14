#' Assess Leaf Area for a Single Image
#'
#'This function assesses the area of leaves taken from a single image. Ideally, the image will be obtained from a flatbed scanner, and will include resolution information in the exif metadata. Images derived from cameras can also be used, but in that case, you will probably need to supply the resolution explictly, using the argument res.
#'
#' @param img The path to the image on which you want to assess the leaf area
#' @param output_dir The directory where to save the processed images. Respects tilde expansion. By default, processed images are not saved. This must not be a directory that already exists, so that existing files are not over-written.
#' @param threshold A value between 0 (black) and 255 (white) for classification of background and leaf pixels. Default = 120
#' @param cut_off Clusters with fewer pixels than this value will be discarded. Default is 10000, which is about 3.3 pixels x 3.3 pixels, in a 300 dots per inch image.
#' @param combine If true the total area will be returned; otherwise each segment will be returned separately
#' @param res Image resolution, in dots per inch (DPI); if False the resolution will be read from the exif tag. Default is 300 DPI.
#'
#' @return The assessed leaf area for a single image or entire folder of images, in cm^2 is returned as a \code{data.frame}.
#'
#' @examples
#' img <- area_example("prepared/img1.jpg")
#' output_dir <- area_example("processed")
#'
#'
#' # If the argument output_dir is omitted,  do not save  processed images
#' assess(img, res = 400, combine = TRUE)
#' \dontrun{
#' assess(img, output_dir = output_dir, res = 400, combine = F)
#' }

assess <- function(img, threshold = 120, cut_off = 10000, output_dir = NULL, combine = FALSE, res = 300) {
  path_to_python <- python_version()
  path_to_script <- paste(system.file(package="area"), "LAV_assess.py", sep="/")
  args <- paste(shQuote(path_to_script), "--img", shQuote(img), "--threshold", threshold, "--cut_off", cut_off, "--res", res)
  if(!is.null(output_dir)){args <- paste(args, "--output_dir", shQuote(output_dir))}
  if(combine){args <- paste(args, "--combine", combine)}

  out <- system2(command = path_to_python, args = args, stdout = TRUE)

  out2 <- out[grep("NOTE: ", out, invert = T)] # drop the directory creation notes
  out2 <- out2[-1] # drop the header row off the output
  out3 <- matrix(unlist(strsplit(out2, " {2,}")), byrow= T, ncol = 3)
  colnames(out3) <- c('Count', 'Image',  'Area')
  out3 <- data.frame(out3)
  out3$Count <- 1 + out3$Count
  out3$Area <- as.numeric(as.character(out3$Area))
  return(out3)
}
