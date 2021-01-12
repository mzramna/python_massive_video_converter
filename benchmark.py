import os
import shutil
import time

from youtube_dl import YoutubeDL as ydl

from allvideoconverter import converter


def find_file(folder, filename=""):
    structure = os.scandir(path=folder)
    if filename == "":
        return structure
    else:
        for entry in structure:
            if entry.is_file():
                if str(entry.name) == filename:
                    return entry
        structure.close()
        return None


try:
    os.mkdir("./benchmark_files/")
    os.mkdir("./benchmark_files/original/")
except:
    pass
current_dir = str(os.getcwd())
is_new = not os.path.exists("./benchmark_result.csv")
benchmark_log = open(current_dir + "\\benchmark_result.csv", "a+", newline="\n")
if is_new:
    benchmark_log.write("output_file;hwaccel;codec;file_format;total_time;size\n")
benchmark_log.close()
try:
    test_video = find_file(current_dir + "\\benchmark_files\\original",
                           filename="Big Buck Bunny 60fps 4K - Official Blender Foundation Short Film-aqz-KE-bpKQ.webm")
    print(test_video.path)
except:
    YDL = ydl(
        params={"format": "303"})
    download = YDL.download(url_list=["https://youtu.be/aqz-KE-bpKQ"])  # https://github.com/ytdl-org/youtube-dl/blob/master/README.md#options
    shutil.move("./Big Buck Bunny 60fps 4K - Official Blender Foundation Short Film-aqz-KE-bpKQ.webm","./benchmark_files/original/Big Buck Bunny 60fps 4K - Official Blender Foundation Short Film-aqz-KE-bpKQ.webm")
    test_video = find_file(current_dir + "\\benchmark_files\\original", filename="Big Buck Bunny 60fps 4K - Official Blender Foundation Short Film-aqz-KE-bpKQ.webm")
    print(test_video.path)
resolutions = [240, 360, 480, 720, 1080]
codec_files = {"h264": ["MP4", "M4V", "avi", "mkv", "flv", "MTS", "M2TS", "ts", "asf", "3gp", "3g2"],
               "hvec": [ "avi",  "mkv","mp4"],
               "mpeg4": ["MP4",  "M4V",  "avi", "mkv", "MTS", "M2TS", "ts", "asf", "3gp",
                         "3g2"], }
codecs = {
    "cuda": {
    "h264_nvenc": codec_files["h264"],
    "hevc_nvenc": codec_files["hvec"],
    "mpeg4": codec_files["mpeg4"],
},
    "d3d11va": {
        "h264": codec_files["h264"],
        "hvec": codec_files["hvec"],
        "mpeg4": codec_files["mpeg4"],
    },
    # "dxva2": {
    #     "h264": codec_files["h264"],
    #     "hvec": codec_files["hvec"],
    #     "mpeg4": codec_files["mpeg4"],
    # },
    "qsv": {
        "h264": codec_files["h264"],
        "hvec": codec_files["hvec"],
        "mpeg4": codec_files["mpeg4"],
    },
}  # https://en.wikipedia.org/wiki/Video_file_format
# for resolution in resolutions:
for hwaccel in codecs.keys():
    for codec in codecs[hwaccel].keys():
        benchmark = converter(codec=codec, output_folder=str(current_dir + "\\benchmark_files"), crf=23, resolution=720,
                              fps=30, hwaccel=hwaccel, resized_log=str(current_dir + "\\resized.log"))
        for file_format in codecs[hwaccel][codec]:
            benchmark_log = open(current_dir + "\\benchmark_result.csv", "a+", newline="\n")

            output_file = str(current_dir + "\\benchmark_files\\benchmark."+hwaccel+"." + codec + "." + file_format.lower())
            initial_time = time.time()
            if benchmark.convert_video(test_video, output_name=output_file) == 0:
                total_time = time.time() - initial_time
                converted_file = find_file(current_dir + "\\benchmark_files",
                                           str("benchmark." + codec + "." + file_format))
                if converted_file != None:
                    benchmark_log.write(
                        str(str(converted_file.path)+";"+str(hwaccel)+";"+ str(codec)+";"+str(file_format)+";"+str(total_time)+";"+str( converted_file.stat().st_size)+"\n"))

                    benchmark_log.close()

