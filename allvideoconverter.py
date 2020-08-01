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


def create_command(arquivo,extension_convert:str="mkv",resolution:int=480,codec:str="h264_omx",fps:int=24,crf:int=20,preset:str="slow",array=False,resize=False,resize_log="./resize.log",resized_log="./resize.log"):
    fileExtensions=["webm","flv","vob","ogg","ogv","drc","gifv","mng","avi","mov","qt","wmv","yuv","rm","rmvb","asf","amv","mp4","m4v","mp\*","m\?v","svi","3gp","flv","f4v","mkv"]

    file_name_no_extension=os.path.splitext(arquivo.name)[0]
    extension=os.path.splitext(arquivo.name)[1][1:]
    relative_dir="/".join(str(x) for x in arquivo.path.split("/")[:-1])+"/"
    new_file_name=str(relative_dir)+str(file_name_no_extension)

    if ( extension == extension_convert and not resize ) or ( ( extension or extension_convert ) not in fileExtensions ):
        return ""
    elif extension == extension_convert:
        new_file_name=new_file_name+".convert"
        same_extension=True
    else:
        same_extension=False
        
    new_file_name=new_file_name+"."+extension_convert
    command=["ffmpeg","-y","-hide_banner","-i",str(arquivo.path), "-acodec", "copy","-scodec","copy" ]
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
                if line == new_file_name+"\n":
                    converted=True
                    break
            log_file.close()
            log_file = open(resized_log)
            converted=False
            for line in log_file.readlines():
                if line == arquivo.path+"\n":
                    converted=True
                    break
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

def convert_video(arquivo,extension_convert:str="mkv",resolution:int=480,codec:str="h264_omx",fps:int=24,crf:int=20,preset:str="slow",resize=False,remove=False,process=False,resize_log='./resize.log',resized_log="./resized.log",working_log="./working.log"):
    file_name_no_extension=os.path.splitext(arquivo.name)[0]
    extension=os.path.splitext(arquivo.name)[1][1:]
    relative_dir="/".join(str(x) for x in arquivo.path.split("/")[:-1])+"/"
    new_file_name=str(relative_dir)+str(file_name_no_extension)

    if extension == extension_convert:
        new_file_name=new_file_name+".convert"
        same_extension=True
    else:
        same_extension=False
    new_file_name=new_file_name+"."+extension_convert
    try:
        log_file=open(working_log,"r")
        for line in log_file.readlines():
            if line == new_file_name+"\n":
                log_file.close()
                print("working")
                return 0
        log_file.close()
        
        log_file=open(resize_log,"r")
        for line in log_file.readlines():
            if line == new_file_name+"\n":
                log_file.close()
                print("resize")
                return 0
        log_file.close()
        
        log_file=open(resized_log,"r")
        for line in log_file.readlines():
            if line == arquivo.path+"\n":
                log_file.close()
                print("resized")
                return 0
        log_file.close()
    except:
        pass
    finally:
        log_file=open(working_log,"a")
        log_file.write(new_file_name+"\n")
        log_file.close()
            
    command= create_command(arquivo,extension_convert=extension_convert,resize=resize,resolution=resolution,codec=codec,fps=fps,crf=crf,preset=preset,array=True,resize_log=resize_log,resized_log=resized_log)
    if command == "":
        return 0
    
    if not process:
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
            log_file=open(resized_log,"a")
            log_file.write(arquivo.path+"\n")
            log_file.close()
        if remove:
            if same_extension:
                shutil.move(new_file_name,str(relative_dir)+str(file_name_no_extension)+"."+extension_convert)
            else:
                os.remove(str(arquivo.path))
    else:
        processo= subprocess.Popen(command)
        retorno={"process":processo,"new_file_name":new_file_name,"extension":extension,"same_extension":same_extension}
        return retorno


def convert_multiple_video(files:[] ,multiple=2,extension_convert:str="mkv", resize=False, resolution:int=480, remove=False, codec:str="h264_omx", fps:int=24, crf:int=20, preset:str="slow", resize_log='./resize.log', working_log="./working.log"):
    processes=[]
    file_index=0
    while True:
        while len(processes) <  multiple:
            element_data=convert_video(files[file_index],extension_convert=extension_convert,resolution=resolution,codec=codec,fps=fps,crf=crf,preset=preset,resize=resize,remove=remove,process=True,resize_log=resize_log,working_log=working_log)
            print(element_data)
            if type(element_data) == type({}) :
                element_data["arquivo"]=files[file_index]
                print(element_data)
                processes.append(element_data)
            else:
                #print(create_command(files[file_index],extension_convert=extension_convert,resolution=resolution,codec=codec,fps=fps,crf=crf,preset=preset,resize=resize,resize_log=resize_log))
                print(files[file_index])
                if file_index<len(files):
                    file_index+=1
                else:
                    break
            
        for process in processes:
            if process["process"].poll() != None:
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
                    log_file=open(resized_log,"a")
                    log_file.write(arquivo.path+"\n")
                    log_file.close()
                if remove:
                    if process["same_extension"]:
                        shutil.move(process["new_file_name"],str("/".join(str(x) for x in process["arquivo"].path.split("/")[:-1])+"/")+str(os.path.splitext(process["arquivo"].name)[0])+"."+extension_convert)
                    else:
                        os.remove(str(arquivo.path))
                processes.remove(process)
                
        if len(processes) == 0:
            return 1

pasta_teste="./test"
dir_data=list_content(pasta_teste)
#print(dir_data)
#print(os.listdir(pasta_teste))
#print([f for f in os.listdir(pasta_teste) if os.path.isfile(f)])
#for file in dir_data["files"]:
    #print(create_command(file,resize=True))
#for arquivo in dir_data["files"]:
    #print(arquivo)
    #convert_video(arquivo,"mkv",resize=True)

convert_multiple_video(dir_data["files"],resize=True)
