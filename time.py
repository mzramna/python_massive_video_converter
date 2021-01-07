from allvideoconverter_linux import converter
import datetime
tester=converter()
tester.fill_files_list()
totalTime=0
for File in tester.files:
    try:
        tmp=tester.get_video_time(File)
        if isinstance(subtitle_codec,float):
            totalTime+=tmp
    except:
        tmp=0

        
totalTime=datetime.timedelta(seconds=totalTime)
print(totalTime)
