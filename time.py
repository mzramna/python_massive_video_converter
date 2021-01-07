from allvideoconverter import converter
import datetime

tester = converter()
tester.fill_files_list()
totalTime = 0
for File in tester.files:
    try:
        tmp = tester.get_video_time(File)
        if isinstance(tmp, float):
            print(str(tmp) + " " + str(File.name))
            totalTime += tmp
    except:
        tmp = 0

print(totalTime)
totalTime = datetime.timedelta(seconds=int(totalTime))
print(totalTime)