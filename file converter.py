import ffmpeg
import os
simultaneosconvert=2
fileExtensions=["webm","flv","vob","ogg","ogv","drc","gifv","mng","avi","mov","qt","wmv","yuv","rm","rmvb","asf","amv","mp4","m4v","mp\*","m\?v","svi","3gp","flv","f4v"]
thisdir = os.getcwd()
convertTo={"formato":"mkv","filterParameters":
	{"scale":"hd480",},
		   "outputParameters":{"format":"matroska","vcodec":"libx264","crf":"30","preset":"slow","bitrate":"1000k","fps":"30"}}
arquivosAConverter=[]
flagConversion="convertido"
for r, d, f in os.walk(thisdir):
	for file in f:
		nome=file.split(".")
		for extension in fileExtensions :
			if flagConversion not in nome[len(nome)-2]:
				if extension in nome[len(nome)-1]:
					input=os.path.join(r, file)
					output=""
					for i in range(0,(len(nome)-1)):
						output+=nome[i]+"."
					output+=flagConversion+"."+convertTo["formato"]
					output=os.path.join(r, output)
					arquivosAConverter.append({"input":input,"output":output})
#for arquivos in arquivosAConverter :
#	print("entrada= "+arquivos["input"])
#	print("saida= "+arquivos["output"])
processes=[]
for arquivos in arquivosAConverter :

	processes.append(ffmpeg.input(arquivos["input"],vcodec="h264_cuvid").\
	filter('scale',size=convertTo["filterParameters"]["scale"]).
	output(arquivos["output"]
		   ,crf=convertTo["outputParameters"]["crf"]
		   ,preset=convertTo["outputParameters"]["preset"]
		   #,video_bitrate=convertTo["outputParameters"]["bitrate"]
		   #,acodec="auto"
		   ,format=convertTo["outputParameters"]["format"]
			,vcodec="h264_nvenc"
		   ,)
	)
convertidos=0
running=[]
while convertidos< len(processes):
	print(len(running))
	if len(running) < simultaneosconvert:
		print(arquivosAConverter[convertidos]["output"])
		running.append(processes[convertidos].run_async(pipe_stdout=True, pipe_stderr=True,quiet=False,overwrite_output=True))
		convertidos+=1
	else:
		print(len(running))
		for i in running:
			print(i.communicate())
			if i.poll() == None:
				print(i.poll())
				running.remove(i)


