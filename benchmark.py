from allvideoconverter import converter
import os,re,csv,time
from youtube_dl import YoutubeDL as ydl

def find_file(folder,filename=""):
    structure=os.scandir(path=folder)
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
benchmark_log=open("./benchmark_result.csv","w+",newline="\n")
benchmark_result=csv.writer(benchmark_log)
current_dir=str(os.getcwd())
benchmark_csv=find_file(current_dir, "./benchmark_result.csv")
if benchmark_csv is not None and os.stat(benchmark_csv).st_size > 0:
    benchmark_result.writerow(["output_file","codec","file_format","total_time","size"])
try:
    YDL=ydl(params={"download_archive":"./benchmark_files/original/Big_Buck_Bunny_original.webm","prefer_ffmpeg":True,"format":"303"})
    download=YDL.download(["https://youtu.be/aqz-KE-bpKQ"])#https://github.com/ytdl-org/youtube-dl/blob/master/README.md#options
except:
    pass
test_video=find_file(current_dir+"\\benchmark_files\\original",filename="Big_Buck_Bunny_original.webm")
print(test_video.path)
resolutions=[240,360,480,720,1080]
codec_files={"h264":["MP4", "M4V","avi","mkv","flv","MTS","M2TS","ts","asf","3gp","3g2"],
        "hvec":["WEBM","avi","AVCHD","mkv","asf"],
        "mpeg4":["MP4", "M4P", "M4V","WEBM","avi","AVCHD","mkv","MTS","M2TS","ts","asf","3gp","3g2"],}
codecs={"cuda":{
    "h264_nvenc":codec_files["h264"],
        "hvec_nvenc":codec_files["hvec"],
        "mpeg4":codec_files["mpeg4"],
        },
        "OpenCL":{
        "h264":codec_files["h264"],
        "hvec":codec_files["hvec"],
        "mpeg4":codec_files["mpeg4"],
        }
}#https://en.wikipedia.org/wiki/Video_file_format
#for resolution in resolutions:
for hwaccel in codecs.keys():
    for codec in codecs[hwaccel].keys():
        benchmark=converter(codec=codec,output_folder=str(current_dir+"\\benchmark_files"),crf=23,resolution=720,fps=30,hwaccel=hwaccel,resized_log=str(current_dir+"\\resized.log"))
        for file_format in codecs[hwaccel][codec]:
            output_file=str(current_dir+"\\benchmark_files\\benchmark."+codec+"."+file_format.lower())
            initial_time=time.time()
            benchmark.convert_video(test_video,output_name=output_file)
            total_time=time.time()-initial_time
            converted_file=find_file(current_dir+"\\benchmark_files", str("benchmark."+codec+"."+file_format))
            try:
                benchmark_result.writerow([converted_file.path,codec,file_format,total_time,converted_file.stat().st_size])
            except:
                pass
benchmark_log.close()