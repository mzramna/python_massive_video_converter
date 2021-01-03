#!/usr/bin/python3
import os
import platform
import re
import shutil
import subprocess
import fnmatch



class converter:
    def __init__(self, extension_convert: str = "mkv", resolution: int = 480, codec: str ="h264_omx", fps: int = 24,crf: int = 20, preset: str = "slow", hwaccel="", threads=2, log_level=32, input_folder="./",output_folder="./convert/",resize_log="./resize.log",resized_log="./resized.log"):
        self.resized_log = resized_log
        self.resize_log = resize_log
        self.input_folder = input_folder
        self.output_folder=output_folder
        if not os.path.isdir(self.output_folder):
            os.mkdir(self.output_folder)
        self.codec = codec
        self.extension_convert = extension_convert
        self.resolution = resolution
        self.fps = fps
        self.crf = crf
        self.preset = preset
        self.hwaccel = hwaccel
        self.threads = threads
        self.log_level = str(log_level)
        self.dir_data = self.list_content_folder(self.input_folder)
        self.files = []
        self.fill_files_list()
        self.files.sort(key=lambda x: x.stat().st_size, reverse=False)
        self.results = {}
        if platform.system() == 'Windows':
            self.so_folder_separator = "\\"
            self.ffmpeg_executable = "ffmpeg.exe"
            if codec == "h264_omx":
                self.codec = "h264"
        elif platform.system() == 'Linux':
            self.so_folder_separator = "/"
            self.ffmpeg_executable = "ffmpeg"
            if "arm" not in str(platform.machine()) and codec == "h264_omx":
                self.codec = "h264"
        #obligate de folder address ends with the so separator
        if str(self.input_folder[-1]) != self.so_folder_separator:
                self.input_folder=self.input_folder+self.so_folder_separator
                
        if str(self.output_folder[-1]) != self.so_folder_separator:
                self.output_folder=self.output_folder+self.so_folder_separator

    def fill_files_list(self, folders=""):
        fileExtensions = ["webm", "flv", "vob", "ogg", "ogv", "drc", "gifv", "mng", "avi", "mov", "qt", "wmv", "yuv",
                          "rm", "rmvb", "asf", "amv", "mp4", "m4v", "mp\*", "m\?v", "svi", "3gp", "flv", "f4v", "mkv","divx"]
        if folders == "":
            folders = self.dir_data["dirs"]
            for file in self.dir_data["files"]:
                if os.path.splitext(file.name)[1][1:] in fileExtensions:
                    self.files.append(file)
        for folder in folders:
            dir_data = self.list_content_folder(folder.path)
            for file in dir_data["files"]:
                if os.path.splitext(file.name)[1][1:] in fileExtensions:
                    self.files.append(file)
            self.fill_files_list(folders=dir_data["dirs"])

    def list_content_folder(self, path):
        retorno = {}
        retorno["starting_path"] = path
        retorno["dirs"] = []
        retorno["files"] = []
        for entry in os.scandir(path):
            if entry.is_file():
                retorno["files"].append(entry)
            if entry.is_dir():
                retorno["dirs"].append(entry)
        return retorno

    def command_to_array(self, command, aditional_data=[], previous_array=[]):
        result = previous_array
        for command in command.split(" "):
            result.append(command)
        for aditional in aditional_data:
            result.append(aditional)
        return result

    def compare_video_codec(self, arquivo):
        check_dim = "ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1".split(
            " ")
        check_dim.append(arquivo.path)
        dim = subprocess.run(check_dim, stdout=subprocess.PIPE)
        dim = re.compile("\'(.*)\\\\").findall(str(dim.stdout))[0]
        #print(dim)
        return str(dim)
        
    def compare_audio_codec(self, arquivo,stream):
        check_dim = str("ffprobe -v error -select_streams a:"+str(stream)+" -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1").split(
            " ")
        check_dim.append(arquivo.path)
        dim = subprocess.run(check_dim, stdout=subprocess.PIPE)
        dim = re.compile("\'(.*)\\\\").findall(str(dim.stdout))[0]
        # print(dim)
        return str(dim)
    
    def compare_subtitle_codec(self, arquivo,stream):
        check_dim = str("ffprobe -v error -select_streams s:"+str(stream)+" -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1").split(" ")
        check_dim.append(arquivo.path)
        dim = subprocess.run(check_dim, stdout=subprocess.PIPE)
        dim = re.compile("\'(.*)\\\\").findall(str(dim.stdout))[0]
        # print(dim)
        return str(dim)

    def compare_resolution(self, arquivo, width: int, height: int):
        check_dim = "ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0".split(" ")
        check_dim.append(arquivo.path)
        dim = subprocess.run(check_dim, stdout=subprocess.PIPE)
        dim = re.compile("(\d+\,\d+)").findall(str(dim.stdout))[0].split(",")
        # print(dim)
        if int(dim[0]) > width or int(dim[1]) > height:
            return True
        else:
            return False

    def compare_fps(self, arquivo, fps):
        check_fps = "ffprobe -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate".split(" ")
        check_fps.append(arquivo.path)
        dim = subprocess.run(check_fps, stdout=subprocess.PIPE)
        dim = re.compile("(\d+\/\d+)").findall(str(dim.stdout))[0].split("/")
        dim = int(dim[0]) / int(dim[1])
        if dim > fps:
            return True
        return False
    
    def find_files(self,pattern):
        '''Return list of files matching pattern in base folder.'''
        return [n for n in fnmatch.filter(os.listdir(self.input_folder), pattern) if
        os.path.isfile(os.path.join(self.input_folder, n))]
    
    def treat_file_name(self, arquivo, current_dir=False, no_hierarchy=False, remove=False, debug=False):
        fileExtensions = ["webm", "flv", "vob", "ogg", "ogv", "drc", "gifv", "mng", "avi", "mov", "qt", "wmv", "yuv","rm", "rmvb", "asf", "amv", "mp4", "m4v", "mp\*", "m\?v", "svi", "3gp", "flv", "f4v", "mkv","divx"]

        file_name_no_extension = os.path.splitext(arquivo.name)[0]
        extension = os.path.splitext(arquivo.name)[1][1:]

        if (extension or self.extension_convert) in fileExtensions:
            convertable = True
            ##create relative dir
            relative_dir = ""
            for x in arquivo.path.split(self.so_folder_separator)[:-1]:
                relative_dir=str(relative_dir+str(x)+self.so_folder_separator)
            if relative_dir[-1] != self.so_folder_separator:
                relative_dir=relative_dir+self.so_folder_separator
            relative_dir = relative_dir.replace(self.input_folder, "")
            if relative_dir!="":
                if relative_dir[0] == self.so_folder_separator:
                    relative_dir=relative_dir[1:]
            #print("relative_dir")
            ##make the specificities from combination of parameters of current_dir and no_hierarchy
            if not current_dir and not no_hierarchy:
                ## this works when will not save into current dir and will respect the folder hierarchy from imput folder
                #print("no current dir and hierarchy")
                
            
                new_file_name = str(str(self.output_folder) + str(relative_dir) + str(file_name_no_extension))
                folder_to_create = str(self.output_folder) + str(relative_dir)
                if self.resized_log[:2]=="./":
                    log_file_name = str(self.output_folder) +self.resized_log[2:]
            elif not current_dir and no_hierarchy:
                ## this works when will not save into current dir and will not respect the folder hierarchy from imput folder
                #print("no current dir and no hierarchy")
                
                new_file_name = str(str(self.output_folder) + str(file_name_no_extension))
                folder_to_create = str(self.output_folder) 
                if self.resized_log[:2]=="./":
                    log_file_name = str(self.output_folder) +self.resized_log[2:]
            elif current_dir and not no_hierarchy:
                ## this works when will save into current dir and will respect the folder hierarchy from imput folder
                #print("current dir and hierarchy")
                #relative_dir = relative_dir.replace(self.input_folder, "")
                if str(os.getcwd()[-1]) != self.so_folder_separator:
                    new_file_name = str(
                      str(os.getcwd()) + self.so_folder_separator + str(relative_dir) + str(file_name_no_extension))
                else:
                    new_file_name = str(
                      str(os.getcwd()) + str(relative_dir) + str(file_name_no_extension))
                folder_to_create = str(relative_dir)
                log_file_name = self.resized_log
            elif current_dir and no_hierarchy:
                ## this works when will save into current dir and will not respect the folder hierarchy from imput folder
                print("current dir and no hierarchy")
                #relative_dir = relative_dir.replace(self.input_folder, "")
                new_file_name = str(os.getcwd()) + str(file_name_no_extension)
                folder_to_create = ""
                log_file_name = self.resized_log
            #print(folder_to_create)
            if extension == self.extension_convert:
                new_file_name = new_file_name + ".convert"
                same_extension = True
            else:
                same_extension = False
            if debug:
                new_file_name = str(
                    new_file_name + "." + str(self.codec) + "." + str(self.crf) + "." + str(self.preset) + "." + str(
                        self.codec) + "." + str(self.resolution) + "." + str(self.fps))
            new_file_name = new_file_name + "." + self.extension_convert
            try:
                log_file=open(log_file_name)
                converted = False
                # log_file=open(working_log,"r")
                # for line in log_file.readlines():
                # if line == new_file_name+"\n":
                # log_file.close()
                # print("working")
                # return 0
                # log_file.close()

                
                for line in log_file.readlines():
                    if new_file_name in line:
                        converted = True
                        break
                log_file.close()
                log_file = open(self.resize_log)
                for line in log_file.readlines():
                    if arquivo.path in line:
                        converted = True
                        break
                log_file.close()
            except:
                converted = False
        else:
            convertable = False
            new_file_name = ""
            folder_to_create = ""
            same_extension = False
            converted = False
            relative_dir = ""
        if converted and remove:
            os.remove(arquivo)
        return {"file_name_no_extension": file_name_no_extension, "extension": extension, "convertable": convertable,"relative_dir": relative_dir, "new_file_name": new_file_name, "same_extension": same_extension,"folder_to_create": folder_to_create, "converted": converted,"log_file_name":log_file_name}

    def log_error_files(self, error_log_file="./error.log"):
        file = open(error_log_file, "a")
        for key in self.results.keys():
            if key != 0:
                for error in self.results[key]:
                    file.write(str(key) + ";" + str(error.path) + "\n")
        file.close()

    def create_command(self, arquivo, array=False, resize=False, current_dir=False, no_hierarchy=False,force_change_fps=False, debug=False):
        subtitle_srt=["srt","ass","ssa"]
        subtitle_bitmap=["hdmv_pgs_subtitle","mov_text"]
        name_data = self.treat_file_name(arquivo, current_dir=current_dir, no_hierarchy=no_hierarchy, debug=debug)
        #print(name_data)
        if not name_data["convertable"] or (name_data["converted"] and not debug) or (
                name_data["extension"] == self.extension_convert and not resize):
            return ""
        #if os.path.isfile(name_data["new_file_name"]) and current_dir==True or os.path.isfile(str(name_data["relative_dir"]) + str(
        #                            name_data["file_name_no_extension"]) + "." + self.extension_convert) and current_dir==False :
        #  return ""
        command = [self.ffmpeg_executable, "-y"]
        try:
            print(self.compare_subtitle_codec(arquivo,0))
            print(compare_subtitle_codec(arquivo,0))
        except:
            pass
        if self.hwaccel != "":
            command.append("-hwaccel")
            command.append(self.hwaccel)
        command = command + ["-hide_banner", "-loglevel", self.log_level, "-i", str(arquivo.path)]
        #subtitles_avaliable=self.find_files(name_data["file_name_no_extension"]+"*.srt")
        #if len(subtitles_avaliable)>0:
        #    for i in subtitles_avaliable:
        #        command.append("-i")
        #        command.append(str(self.input_folder)+self.so_folder_separator+str(i))
        command = command +["-acodec", "aac",  "-c:v",
                             self.codec, "-map_metadata", "0", "-pix_fmt", "yuv420p",
                             "-threads", str(self.threads),"-copy_unknown"]
        try:
            if self.compare_subtitle_codec(arquivo,0) in subtitle_srt:
                command.append("-c:s")
                command.append("srt")
        except:
            pass
            
        if self.hwaccel == "qsv":
            command.append("-load_plugin")
            command.append("hevc_hw")
        resize_command = []
        #if used crf the resize parameters of bitrate are not necessary
        #but accord to official youtube data the bitrate used in resize parameters are 
        #the best for any situation
        change_fps = False
        if not resize:
            resize_command.append("-crf")
            resize_command.append(str(self.crf))
            resize_command.append("-preset")
            resize_command.append(self.preset)
        else:
            if not name_data["converted"] or debug:
                small = False
                out_scale = False
                if self.resolution == 240:
                    resize_command.append("-b:v")
                    resize_command.append("500k")
                    resize_command.append("-minrate")
                    resize_command.append("300k")
                    resize_command.append("-maxrate")
                    resize_command.append("700k")
                    if self.compare_resolution(arquivo, 426, 240):
                        resize_command.append("-s")
                        resize_command.append("426x240")  # determina a escala do arquivo para 480p
                    else:
                        small = True
                elif self.resolution == 360:
                    resize_command.append("-b:v")
                    resize_command.append("600k")
                    resize_command.append("-minrate")
                    resize_command.append("400k")
                    resize_command.append("-maxrate")
                    resize_command.append("1000k")
                    if self.compare_resolution(arquivo, 640, 320):
                        resize_command.append("-s")
                        resize_command.append("640x320")  # determina a escala do arquivo para 480p
                    else:
                        small = True
                elif self.resolution == 480:
                    resize_command.append("-b:v")
                    resize_command.append("1000k")
                    resize_command.append("-minrate")
                    resize_command.append("500k")
                    resize_command.append("-maxrate")
                    resize_command.append("2000k")
                    if self.compare_resolution(arquivo, 854, 480):
                        resize_command.append("-s")
                        resize_command.append("854x480")  # determina a escala do arquivo para 480p
                    else:
                        small = True
                elif self.resolution == 720:
                    resize_command.append("-b:v")
                    resize_command.append("3300k")
                    resize_command.append("-minrate")
                    resize_command.append("1500k")
                    resize_command.append("-maxrate")
                    resize_command.append("6000k")
                    if self.compare_resolution(arquivo, 1280, 720):
                        resize_command.append("-s")
                        resize_command.append("1280x720")  # determina a escala do arquivo para 720p
                    else:
                        small = True
                elif self.resolution == 1080:
                    resize_command.append("-b:v")
                    resize_command.append("4000k")
                    resize_command.append("-minrate")
                    resize_command.append("3000k")
                    resize_command.append("-maxrate")
                    resize_command.append("9000k")
                    if self.compare_resolution(arquivo, 1920, 1080):
                        resize_command.append("-s")
                        resize_command.append("1920x1080")  # determina a escala do arquivo para 1080p
                    else:
                        small = True
                else:
                    out_scale = True
                if not small and not out_scale:
                    if self.compare_fps(arquivo, self.fps):
                        command.append("-filter:v")
                        command.append("fps=fps=" + str(self.fps))
                        change_fps = True
                    for i in resize_command:
                        command.append(i)
                elif out_scale:
                    return ""
            else:
                return ""
        if force_change_fps and not change_fps:
            command.append("-filter:v")
            command.append("fps=fps=" + str(self.fps))
        if self.compare_video_codec(arquivo) == "mpeg4" and "h26" in self.codec :
            command.append("-bsf:v")
            command.append("mpeg4_unpack_bframes")
        #command.append(str(name_data["new_file_name"])+".tmp")
        #if len(subtitles_avaliable)>0:
        #    command.append("-c:s")
        #    command.append("mov_text")
        #    for i in range(0,len(subtitles_avaliable)+1):
        #        command.append("-map")
        #        command.append(i)
        command.append(str(name_data["new_file_name"]))
        # print(command)

        if array:
            return command
        else:
            retorno = ""
            for comand in command:
                retorno += comand + " "
            return retorno

    def convert_video(self, arquivo, resize=False, remove=False, process=False, current_dir=False, no_hierarchy=False,force_change_fps=False, debug=False, working_log="./working.log"):
        name_data = self.treat_file_name(arquivo, current_dir=current_dir, no_hierarchy=no_hierarchy,remove=remove, debug=debug)
        if not name_data["convertable"] or (name_data["converted"] and not debug) or (
                name_data["extension"] == self.extension_convert and not resize):
            return 0

        try:
            os.makedirs(name_data["folder_to_create"])
        except:
            pass
        command = self.create_command(arquivo, array=True, resize=resize, current_dir=current_dir, debug=debug,force_change_fps=force_change_fps, no_hierarchy=no_hierarchy)
        if command == "" or (name_data["converted"] and not debug):
            return 0

        if not process:
            #print(command)
            os.chdir(self.output_folder)
            result = subprocess.run(command, stdout=subprocess.PIPE)
            if resize and result.returncode == 0:
                # log_file=open(working_log,"a")
                # tmp_log_file=open(str(working_log)+".tmp","a")
                # for line in log_file.readlines():
                # if line == new_file_name+"\n":
                # pass
                # else:
                # tmp_log_file.write(line)
                # log_file.close()
                # tmp_log_file.close()
                # shutil.move(str(working_log)+".tmp",working_log)
                #os.rename(name_data["new_file_name"]+".tmp",name_data["new_file_name"])
                log_file = open(name_data["log_file_name"], "a")
                log_file.write(name_data["new_file_name"] + "\n")
                log_file.close()
            if remove and result.returncode == 0:
                if name_data["same_extension"]:
                    #shutil.move(name_data["new_file_name"]+".tmp",
                    #            str(name_data["relative_dir"]) + str(
                    #                name_data["file_name_no_extension"]) + "." + self.extension_convert)
                    shutil.move(name_data["new_file_name"],
                                str(name_data["relative_dir"]) + str(
                                    name_data["file_name_no_extension"]) + "." + self.extension_convert)
                else:
                    os.remove(str(arquivo.path))
            if result.returncode == 1 and name_data["new_file_name"] != "":
                try:
                    os.remove(str(name_data["new_file_name"]+".tmp"))
                except:
                    pass
            return result.returncode
        else:
            processo = subprocess.Popen(command)
            retorno = {"process": processo, "aquivo": arquivo}
            return retorno

    def convert_all_files_sequential(self, resize=False, remove=False, current_dir=False, no_hierarchy=False,force_change_fps=False, debug=False):
        if self.files != []:
            for file in self.files:
                tmp = self.convert_video(file, resize=resize, remove=remove, process=False, current_dir=current_dir,
                                         no_hierarchy=no_hierarchy, force_change_fps=force_change_fps, debug=debug)
                if tmp not in self.results.keys():
                    self.results[tmp] = []
                self.results[tmp].append(file)
                if tmp != 0:
                    pass
                    # print(self.results[tmp])
                    # input("waiting")
                else:
                    self.files.remove(file)
        else:
            print(self.results)

    def convert_multiple_video(self, multiple=2, resize=False, current_dir=False, no_hierarchy=False, remove=False,force_change_fps=False, debug=False, working_log="./working.log"):
        processes = []
        file_index = 0
        while True:
            while len(processes) < multiple:
                element_data = self.convert_video(self.files[file_index], resize=resize, remove=remove,
                                                  process=True, current_dir=current_dir, no_hierarchy=no_hierarchy,
                                                  force_change_fps=force_change_fps, working_log=working_log)
                print(element_data)
                if type(element_data) == type({}):
                    element_data["arquivo"] = self.files[file_index]
                    print(element_data)
                    processes.append(element_data)
                else:
                    # print(create_command(files[file_index],extension_convert=extension_convert,resolution=resolution,codec=codec,fps=fps,crf=crf,preset=preset,resize=resize,resize_log=resize_log))
                    print(self.files[file_index])
                    if file_index < len(self.files):
                        file_index += 1
                    else:
                        break

            for process in processes:
                if process["process"].poll() != None:
                    name_data = self.treat_file_name(process["arquivo"], current_dir=current_dir,
                                                     no_hierarchy=no_hierarchy, debug=debug)
                    if resize:
                        # log_file=open(working_log,"a")
                        # tmp_log_file=open(str(working_log)+".tmp","a")
                        # for line in log_file.readlines():
                        # if line == new_file_name+"\n":
                        # pass
                        # else:
                        # tmp_log_file.write(line)
                        # log_file.close()
                        # tmp_log_file.close()
                        # shutil.move(str(working_log)+".tmp",working_log)
                        log_file = open(name_data["log_file_name"], "a")
                        log_file.write(process["new_file_name"] + "\n")
                        log_file.close()
                        log_file = open(self.resize_log, "a")
                        log_file.write(process["arquivo"].path + "\n")
                        log_file.close()
                    if remove:
                        if process["same_extension"]:
                            shutil.move(process["new_file_name"], str(str(self.so_folder_separator).join(str(x) for x in
                                                                                                         process[
                                                                                                             "arquivo"].path.split(
                                                                                                             str(
                                                                                                                 self.so_folder_separator))[
                                                                                                         :-1]) + str(
                                self.so_folder_separator)) + str(
                                os.path.splitext(process["arquivo"].name)[0]) + "." + self.extension_convert)
                        else:
                            os.remove(str(process["arquivo"].path))
                    processes.remove(process)

            if len(processes) == 0:
                return 1

conversor=converter(resolution=720,codec="hevc_nvenc",fps=24,input_folder=".\\" ,output_folder=".\\convert",preset="slow",hwaccel="cuda",threads=4)

conversor.convert_all_files_sequential(resize=True,current_dir=True,no_hierarchy=True)
conversor.log_error_files()
