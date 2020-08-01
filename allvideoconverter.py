#!/usr/bin/python3
import os,subprocess,re,shutil

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


def create_command(arquivo,extension_convert:str="mkv",resize=False,resolution:int=480,codec:str="h264_omx",fps:int=24,crf:int=20,preset:str="slow",array=False,resize_log="./resize.log"):
    fileExtensions=["webm","flv","vob","ogg","ogv","drc","gifv","mng","avi","mov","qt","wmv","yuv","rm","rmvb","asf","amv","mp4","m4v","mp\*","m\?v","svi","3gp","flv","f4v","mkv"]
    
    file_name_no_extension=os.path.splitext(arquivo.name)[0]
    extension=os.path.splitext(arquivo.name)[1][1:]
    print(extension)
    relative_dir="/".join(str(x) for x in arquivo.path.split("/")[:-1])+"/"
    new_file_name=str(relative_dir)+str(file_name_no_extension)

    if ( extension == extension_convert and not resize ) or ( ( extension or extension_convert ) not in fileExtensions ):
        print("already resized")
        return ""
    elif extension == extension_convert:
        new_file_name=new_file_name+".convert"
        same_extension=True
    else:
        same_extension=False
    new_file_name=new_file_name+"."+extension_convert
    command=["ffmpeg","-y","-i",str(arquivo.path), "-acodec", "copy" ]
    copy_command=["-vcodec","copy"]
    resize_command=["-filter:v","fps=fps="+str(fps),"-c:v",codec,"-crf",str(crf),"-preset",preset]
    if not resize :
        for i in copy_command:
            command.append(i)
    else:
        try:
            log_file = open(resize_log)
            converted=False
            for line in log_file.readlines():
                print(line)
                if line == new_file_name+"\n":
                    converted=True
            log_file.close()
        except:
            converted=False
        if not converted:
            if resolution == 480:
                if compare_resolution(arquivo,640,480):
                    resize_command.append("-s")
                    resize_command.append("hd480") #determina a escala do arquivo para 480p
                else:
                    pass
            elif resolution == 720:
                if compare_resolution(arquivo,1280,720):
                    resize_command.append("-s")
                    resize_command.append("hd720") #determina a escala do arquivo para 720p
                else:
                    pass
            else:
                pass
            for i in resize_command:
                command.append(i)
        else:
            print("already resized")
            return ""
    command.append(new_file_name)
    #print(command)
    
    if array:
        return command
    else:
        retorno=""
        for comand in command:
            retorno+=comand+" "
        return retorno

def convert_video(arquivo,extension_convert:str="mkv",resize=False,resolution:int=480,remove=False,codec:str="h264_omx",fps:int=24,crf:int=20,preset:str="slow",resize_log='./resize.log',working_log="./working.log"):
    file_name_no_extension=os.path.splitext(arquivo.name)[0]
    extension=os.path.splitext(arquivo.name)[1][1:]
    print(extension)
    relative_dir="/".join(str(x) for x in arquivo.path.split("/")[:-1])+"/"
    new_file_name=str(relative_dir)+str(file_name_no_extension)

    if extension == extension_convert:
        new_file_name=new_file_name+".convert"
        same_extension=True
    else:
        same_extension=False
        try:
            log_file=open(working_log,"r")
            for line in log_file.readlines():
                if line == new_file_name+"\n":
                    log_file.close()
                    return 0
        except:
            pass
        finally:
            log_file=open(working_log,"a")
            log_file.write(new_file_name+"\n")
            log_file.close()
            
    command= create_command(arquivo,extension_convert=extension_convert,resize=resize,resolution=resolution,codec=codec,fps=fps,crf=crf,preset=preset,array=True)
    #print(command)
    if command == "":
        return 0
    
    new_file_name=new_file_name+"."+extension_convert
    result = subprocess.run(command, stdout=subprocess.PIPE)
    if resize:
        log_file=open(working_log,"a")
        tmp_log_file=open(str(working_log)+".tmp","a")
        for line in log_file.readlines():
            if line == new_file_name+"\n":
                pass
            else:
                tmp_log_file.write(line)
        log_file.close()
        tmp_log_file.close()
        shutil.move(str(working_log)+".tmp",working_log)
        log_file=open(resize_log,"a")
        log_file.write(new_file_name+"\n")
        log_file.close()
    if remove:
        if same_extension:
            shutil.move(new_file_name,str(relative_dir)+str(file_name_no_extension)+"."+extension_convert)
        else:
            os.remove(str(arquivo.path))


pasta_teste="./test"
dir_data=list_content(pasta_teste)
print(dir_data)
#print(os.listdir(pasta_teste))
#print([f for f in os.listdir(pasta_teste) if os.path.isfile(f)])

for arquivo in dir_data["files"]:
    print(arquivo)
    convert_video(arquivo,"mkv",resize=True)
