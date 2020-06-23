#' Determine the version of Python available
#'
#'This function assesses which version of Python is available. It first searches for Python 3, then for Python 2. The user is urged to update their Python installation if it is out of date.
#'#'
#' @examples
#' python_version()
#'
#'
#'
python_version <- function(){

  V3 <- try(system2("python3", "--version", stdout = TRUE), silent = T)
  V3 <- as.numeric(gsub("Python |\\.\\d$", "", V3))
  if(is.na(V3)){V3 <- 0}
  if(V3 >= 3 & V3 < 3.5){
    print(paste("It appears that Python", V3, "is installed on this system. Please update it to Python 3.5 or newer, from https://www.python.org/downloads/"))
    return(NULL)
  } else {
    if (V3 >= 3.5){
      return('python3')
    } else {
      V2 <- try(system2("python", "--version", stdout = TRUE), silent = T)
      V2 <- as.numeric(gsub("Python |\\.\\d$", "", V2))
      if(is.na(V2)){V2 <- 0}
      if(V2 >= 3 & V2 < 3.5){
        print(paste("It appears that Python", V2, "is installed on this system. Please update it to Python 3.5 or newer, from https://www.python.org/downloads/"))
        return(NULL)
      } else{
        if(V2 >= 3.5){
          return('python')
        } else {
          print("It appears that Python 3.5 or newer is not installed on this system. Please install it from https://www.python.org/downloads/, and try again")
        }
      }
    }
  }
}
python_version()
