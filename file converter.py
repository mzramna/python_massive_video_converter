import ffmpeg
import os
simultaneosconvert=3
fileExtensions=["webm","flv","vob","ogg","ogv","drc","gifv","mng","avi","mov","qt","wmv","yuv","rm","rmvb","asf","amv","mp4","m4v","mp\*","m\?v","svi","3gp","flv","f4v"]
#thisdir = os.path.normpath(input("diretorio de execucao"))
thisdir=os.getcwd()
convertTo={"formato":"mkv","filterParameters":
	{"scale":"hd480","fps":24},
		   "outputParameters":{"vcodec":"h264_omx","crf":20,"preset":"slow","acodec":"copy"}}
arquivosAConverter=[]
for r, d, f in os.walk(thisdir):
	for file in f:
		nome=file.split(".")
		for extension in fileExtensions :
			if (extension) in nome[len(nome)-1]:
				input=os.path.join(r, file)
				output=""
				for i in range(0,(len(nome)-1)):
					output+=nome[i]+"."
				output+="convertido."+convertTo["formato"]
				output=os.path.join(r, output)
				arquivosAConverter.append({"input":input,"output":output})
#for arquivos in arquivosAConverter :
#	print("entrada= "+arquivos["input"])
#	print("saida= "+arquivos["output"])
processes=[]
for arquivos in arquivosAConverter :
	#if len(processes)<=simultaneosconvert:
	audio=ffmpeg.input(arquivos["input"]).audio
	video=ffmpeg.input(arquivos["input"]).filter('scale',size=convertTo["filterParameters"]["scale"]).filter('fps', fps=convertTo["filterParameters"]["fps"], round='up')
	output=ffmpeg.output(video,audio,arquivos["output"]
		   ,acodec=convertTo["outputParameters"]["acodec"]
		   ,vcodec=convertTo["outputParameters"]["vcodec"]
		   ,crf=convertTo["outputParameters"]["crf"]
		   ,preset=convertTo["outputParameters"]["preset"]
		   )
	
	processes.append(output)
	#else:
for process in processes :
	process.run(overwrite_output=True,capture_stdout=True)
