import allvideoconverter

conversor = allvideoconverter.converter(resolution=480, codec="h264_qsv", fps=24, pasta=".\\test", preset="slow",
                      hwaccel="qsv", threads=3)

conversor.convert_all_files_sequential(resize=True, current_dir=True)
conversor.codec = "hevc_qsv"
conversor.convert_all_files_sequential(resize=True, current_dir=True)
conversor.codec = "h264"
conversor.convert_all_files_sequential(resize=True, current_dir=True)
conversor.codec = "copy"
conversor.convert_all_files_sequential(resize=True, current_dir=True)
# convert_multiple_video(dir_data["files"],resize=True,current_dir=True)

