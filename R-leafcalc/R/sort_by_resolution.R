#' Sort images by resolution
#'
#' Some image-processing programs assume that ones images are sorted by resolution. LS needs to be told what the scale for each image is. It can't guess that. So, I need to read that information in, using exiftool (ie, identify function in Image Magick.) But, it analyses a whole folder at a time. So, I need to look up the resolutions, and move files into folders to be analysed.
#'
#' @param path Name of folder in which to sort images.
#' @param batch How many images should be put into each sub-folder? Defaults to no sorting.
#'
#' @examples
#' input_dir <- area_example("raw")
#' sort_images(input_dir)
#' sort_images(input_dir, 2)

sort_images <- function (path, batch = NA) {
  files <- list.files(path, recursive = F, full.names = T)
  stopifnot(length(files) > 0)
  temp <- unique(sub("/[^/]*.jpg", "/\\1*.jpg", files))
  if(Sys.info()[1] == 'Windows' & system("where magick") != 0) {
    print("This system does not appear to have ImageMagick installed, which is necessary to run this function. ")
  }
  if(Sys.info()[1] != 'Windows' & system("which magick") != 0){
    print("This system does not appear to have ImageMagick installed, which is necessary to run this function. ")
  }

  resolutions <- as.numeric(strsplit(system(paste0('magick identify -format "%x ',  temp, '"'), intern = T), " ")[[1]]) # grabs the resolution of the image
  res <- unique(resolutions)

  for(i in 1:length(unique(res))){
    dir.create(file.path(path, unique(res)[i]))
  }

  # copy the files into folders for their resolutions
  for(j in 1:length(files)){
    dest_file_path.j <- sub("(.*/)(.*?.jpg)", paste0("\\1", resolutions[j], "/\\2"), files[j])
    system(paste0("cp '", files[j], "' '", dest_file_path.j,  "'"))
  }

  # move files around to make batches, if requested by the user
  if(!is.na(batch)){
    for(i in 1:length(res)){
      files.i <- list.files(file.path(path, res[i]), recursive = F, full.names = T)

      starts <- seq(1, length(files.i), by = batch)
      ends <- c(starts[-1]-1, length(files.i))
      for(j in 1:length(starts)){
        files.j <- files.i[starts[j]:ends[j]]
        dest_file_paths.j <- sub("(.*/)(.*?.jpg)", paste0("\\1", j, "/\\2"), files.j)
        system(paste0("mkdir -v -p '", file.path(getwd(), sub("[^/]*jpg", "", dest_file_paths.j)), "'")) # make directory if necessary

        for(k in 1:length(files.j)){
          system(paste0("mv '", files.j[k], "' '", dest_file_paths.j[k],  "'")) # move the relevant files
        }
      }
    }
  }
}

