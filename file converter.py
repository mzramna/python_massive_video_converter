import ffmpeg
import os
fileExtensions=["webm","flv","vob","ogg","ogv","drc","gifv","mng","avi","mov","qt","wmv","yuv","rm","rmvb","asf","amv","mp4","m4v","mp\*","m\?v","svi","3gp","flv","f4v"]
thisdir = os.getcwd()
convertTo={"formato":"mkv","filterParameters":
	{"scale":"hd480",},
		   "outputParameters":{"vcodec":"libx264","crf":"18","preset":"veryfast"}}
for r, d, f in os.walk(thisdir):
	for file in f:
		nome=file.split(".")
		for extension in fileExtensions :
			if (extension) in nome[len(nome)-1]:
				print(os.path.join(r, file))
				input=os.path.join(r, file)
				output=""
				for i in range(0,(len(nome)-1)):
					output+=nome[i]+"."
				output+="convertido."+convertTo["formato"]
				print(output)
				output=os.path.join(r, output)
				ffmpeg.input(input).\
					filter('scale',size=convertTo["filterParameters"]["scale"]). \
					output(output,vcodec=convertTo["outputParameters"]["vcodec"]
						   ,crf=convertTo["outputParameters"]["crf"]
						   ,preset=convertTo["outputParameters"]["preset"]
						   ,).run()
