#!/usr/bin/python3
import os,subprocess,re

def list_content(path):
	retorno={}
	retorno["starting_path"]=path
	retorno["dirs"]=[]
	retorno["files"]=[]
	for entry in os.scandir(path):
		if entry.is_file():
			retorno["files"].append(entry)
		if entry.is_dir():
			retorno["dirs"].append(entry)
	return retorno

def command_to_array(command,aditional_data=[],previous_aray=[]):
    result=previous_array
    for command in command.split(" "):
        result.append(command)
    for aditional in aditional_data:
        result.append(aditional)
    return result

def compare_resolution(arquivo,width:int,height:int):
	check_dim="ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0".split(" ")
	check_dim.append(arquivo.path)
	dim = subprocess.run(check_dim, stdout=subprocess.PIPE) 
	dim=re.compile("(\d+\,\d+)").findall(str(dim.stdout))[0].split(",")
	#print(dim)
	if int(dim[0]) > width or int(dim[1])> height:
		return True
	else:
		return False

def convert_video(arquivo,extension_convert:str="mkv",resize=False,resolution:int=480,remove=False,codec:str="h264_omx",fps:int=24,crf:int=20,preset:str="slow",resize_log='./resize.log',working_log="./working.log"):
    fileExtensions=["webm","flv","vob","ogg","ogv","drc","gifv","mng","avi","mov","qt","wmv","yuv","rm","rmvb","asf","amv","mp4","m4v","mp\*","m\?v","svi","3gp","flv","f4v"]
    
	file_name_no_extension=os.path.splitext(arquivo.name)[0]
	extension=os.path.splitext(arquivo.name)[1]
	
	relative_dir="/".join(str(x) for x in arquivo.path.split("/")[:-1])+"/"
	new_file_name=str(relative_dir)+str(file_name_no_extension)+"."+extension_convert
	if ( extension =="."+extension_convert and not resize ) or ( extension not in fileExtensions ):
		return 0
    else:
        log_file=open(working_log,"a")
		log_file.write(new_file_name+"\n")
		log_file.close()
	
	command=["ffmpeg","-i",str(arquivo.path), "-acodec", "copy" ]
	copy_command=["-vcodec","copy"]
	resize_command=["-filter:v","fps=fps="+str(fps),"-c:v",codec,"-crf",str(crf),"-preset",preset,"-s"]
	if not resize :
		#print(" not resize")
		for i in copy_command:
			command.append(i)
	elif resize :
		#print("resize")
		try:
			log_file = open(resize_log)
			converted=False
			#print(log_file.readlines())
			for line in log_file.readlines():
				print(line)
				if line == new_file_name+"\n":
					converted=True
			log_file.close()
		except:
			converted=False
		if not converted:
			#print("not resized")
			if resolution == 480:
				if compare_resolution(arquivo,640,480):
					#print("resize to 480p")
					resize_command.append("hd480")	#determina a escala do arquivo para 480p
				else:
					#print("menor que o pedido")
					return 0
			elif resolution == 720:
				if compare_resolution(arquivo,1280,720):
					#print("resize to 720p")
					resize_command.append("hd720") #determina a escala do arquivo para 720p
				else:
					#print("menor que o pedido")
					return 0
			else:
				return 0
			print("criado comando")
			for i in resize_command:
				command.append(i)
		else:
			print("already resized")
			return 0
	command.append(new_file_name)
	#print(command)
	result = subprocess.run(command, stdout=subprocess.PIPE)
	if resize:
        log_file=open(working_log,"a")
        tmp_log_file=open(str(working_log)+".tmp","a")
        for line in log_file:
            if line == new_file_name+"\n":
                pass
            else:
                tmp_log_file.write(line)
        log_file.close()
        tmp_log_file.close()
        os.remove(working_log)
        os.rename(str(working_log)+".tmp",working_log)
		log_file=open(resize_log,"a")
		log_file.write(new_file_name+"\n")
		log_file.close()
	if remove:
		os.remove(str(arquivo.path))


pasta_teste="./test"
dir_data=list_content(pasta_teste)
print(dir_data)
#print(os.listdir(pasta_teste))
#print([f for f in os.listdir(pasta_teste) if os.path.isfile(f)])

for arquivo in dir_data["files"]:
	convert_video(arquivo,resize=True)
