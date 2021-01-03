# python_video_converter
this file compress all the video files inside a folder to the defined file format and ffmpeg settings defined into the convertTo dictionary,it follows all the ffmp and python-ffmpeg directives,but automatize and simplify the conversion of multiples files

this uses only a few libs to work,just uses native libs for python 3.9+
this also uses ffmpeg and the related applications
if you using linux with nvidia try to install `libffmpeg-nvenc-dev` ,this will enable nvidia gpu the easy way
btw: `linux so is recommended SO`,in tests it presents at last twice the speed in conversion using same hardware

this lib automatize coversion of tons of files ,using the right parameters it will speedup any necessary process of conversion of files
together it is associated an class that can identify and fill all the file metadata for videos existing in imdb ~by now only movies works~,to enable this you will need an tmdb api,one is provided with the exemple,and you will also need install some libs using pip: `tmdbsimple` `imdbpie`

the necessary parameters to instance the class are:
```
extension_convert:the extension you want to use as the end of conversion ex: "mkv"~dows not support empty or does not change yet~
resolution: the final resolution height,it accepts this values:[240,360,480,720,1080],more values will easily be added in future,but the idea is to reduce the video sizes,not expand them,so if necessary just add this later,the code will always keep the original file aspect ratio
codec: the codec that will be used by ffmpeg,accepts the codec "copy" also,but is not recommended if you change the extension file name,by default it will works with h264
fps: the output fps desired for file,by default it will uses 24 fps,the minimum used to see an fluid moviment in movies
crf: [the quality parameter of ffmpeg](https://trac.ffmpeg.org/wiki/Encode/H.264),this will be ignored if you resize the file,if resize it will uses the [youtube recomended](https://support.google.com/youtube/answer/1722171) bitrate for video files
preset: [the quality parameter of ffmpeg](https://trac.ffmpeg.org/wiki/Encode/H.264),this will be ignored if you resize the file,if resize it will uses the [youtube recomended](https://support.google.com/youtube/answer/1722171) bitrate for video files
hwaccel: the hardware acceleration method,most commonly will be one of this: nvenc,qsv,opencl,openmax. respecivly: nvidia gpu,intel cpu,amd cpu or gpu,raspberry pi hardware acceleration
threads:total of threads the ffmpeg will create in your cpu,high values in weak cpu may crash the system
log_level:[ffmepg log system](https://ffmpeg.org/ffmpeg.html#Generic-options),default value is 32: "Show informative messages during processing. This is in addition to warnings and errors. This is the default value."
input_folder:the input folder where all the input files will be
output_folder:the output folder where all the output files will be
resize_log:the log file that informs all the converted files that ends correctly,if deleted or moved from the informed dir,it will restart all the conversion process
resized_log:the redundant log file that informs all the converted files that ends correctly,if deleted or moved from the informed dir,it will restart all the conversion process
```

the parameters for the conversion function(convert_all_files_sequential) are:
```
resize:will inform if the files will or not be resized,if false it will use the crf parameter and keep the same size and shape of the original file
remove:if true it will delete the original file at the end of the process
current_dir: if true it will create a sub dir in current dir and put all the converted files there
no_hierarchy:if false it will keep all the files hierarchy of the input file,if true it will put all the files in the root of the output folder
force_change_fps:it will force the fps to change,even if the original file fps is slower than the fps value inserted here
debug:if enabled will print lots of debug while converting the file
```
