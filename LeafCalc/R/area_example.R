#' Get Path to Example Image
#'
#' LAV comes bundled with a number of sample files in its inst/extdata directory. This function make them easy to access.
#'
#' @param path Name of file. If NULL, the example files will be listed.
#'
#' @examples
#' area_example()
#' area_example("raw/img5.jpg")


area_example <- function (path = NULL) {
  if (is.null(path)) {
    dir(system.file("extdata", package = "area"))
  }
  else {
    system.file("extdata", path, package = "area", mustWork = TRUE)
  }
}
