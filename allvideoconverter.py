#!/usr/bin/python3
import os
import platform
import re
import shutil
import subprocess


class converter:
    def __init__(self, extension_convert: str = "mkv", resolution: int = 480, codec: str = "h264_omx", fps: int = 24,
                 crf: int = 20, preset: str = "slow", hwaccel="", threads=2, pasta="./", resize_log="./resize.log",
                 resized_log="./resized.log"):
        self.resized_log = resized_log
        self.resize_log = resize_log
        self.pasta = pasta
        self.codec = codec
        self.extension_convert = extension_convert
        self.resolution = resolution
        self.fps = fps
        self.crf = crf
        self.preset = preset
        self.hwaccel = hwaccel
        self.threads = threads
        self.dir_data = self.list_content_folder(self.pasta)
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

    def fill_files_list(self, folders=""):
        if folders == "":
            folders = self.dir_data["dirs"]
            self.files = self.files + self.dir_data["files"]
        for folder in folders:
            dir_data = self.list_content_folder(folder.path)
            self.files = self.files + dir_data["files"]
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
        check_fps = "ffprobe -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate".split(
            " ")
        check_fps.append(arquivo.path)
        dim = subprocess.run(check_fps, stdout=subprocess.PIPE)
        dim = re.compile("(\d+\/\d+)").findall(str(dim.stdout))[0].split("/")
        dim = int(dim[0]) / int(dim[1])
        if dim > fps:
            return True
        return False

    def create_command(self, arquivo, array=False, resize=False, current_dir=False, no_hierarchy=False,
                       force_change_fps=False, debug=False):
        fileExtensions = ["webm", "flv", "vob", "ogg", "ogv", "drc", "gifv", "mng", "avi", "mov", "qt", "wmv", "yuv",
                          "rm", "rmvb", "asf", "amv", "mp4", "m4v", "mp\*", "m\?v", "svi", "3gp", "flv", "f4v", "mkv"]

        file_name_no_extension = os.path.splitext(arquivo.name)[0]
        extension = os.path.splitext(arquivo.name)[1][1:]
        # determina a plataforma
        new_file_name = ""
        relative_dir = self.so_folder_separator.join(
            str(x) for x in arquivo.path.split(self.so_folder_separator)[:-1]) + self.so_folder_separator

        if not current_dir:
            new_file_name = str(str(relative_dir) + str(file_name_no_extension))
        elif not no_hierarchy:
            relative_dir = relative_dir.replace(self.pasta, "")
            new_file_name = str(
                str(os.getcwd()) + self.so_folder_separator + str(relative_dir) + str(file_name_no_extension))
        else:
            relative_dir = relative_dir.replace(self.pasta, "")
            new_file_name = str(os.getcwd()) + self.so_folder_separator + str(file_name_no_extension)

        if (extension == self.extension_convert and not resize) or (
                (extension or self.extension_convert) not in fileExtensions):
            return ""
        elif extension == self.extension_convert:
            new_file_name = new_file_name + ".convert"
            same_extension = True
        else:
            same_extension = False
        if debug:
            new_file_name = str(
                new_file_name + "." + str(self.codec) + "." + str(self.crf) + "." + str(self.preset) + "." + str(
                    self.codec) + "." + str(self.resolution) + "." + str(self.fps))
        new_file_name = new_file_name + "." + self.extension_convert
        command = [self.ffmpeg_executable, "-y"]
        if self.hwaccel != "":
            command.append("-hwaccel")
            command.append(self.hwaccel)

        # if extension == "avi":
        #    command.append("-bsf:v")
        #    command.append("mpeg4_unpack_bframes")
        command = command + ["-hide_banner", "-i", str(arquivo.path), "-acodec", "copy", "-scodec", "copy", "-c:v",
                             self.codec, "-map_metadata", "0", "-map_metadata:s:a", "0:s:a", "-pix_fmt", "yuv420p",
                             "-threads", str(self.threads)]
        if self.hwaccel == "qsv":
            command.append("-load_plugin")
            command.append("hevc_hw")
        resize_command = ["-crf", str(self.crf), "-preset", self.preset]

        change_fps = False

        if resize:
            try:
                log_file = open(self.resized_log)
                converted = False
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

            if not converted or debug:
                small = False
                out_scale = False
                if self.resolution == 240:
                    if self.compare_resolution(arquivo, 426, 240):
                        resize_command.append("-b:v")
                        resize_command.append("500k")
                        resize_command.append("-minrate")
                        resize_command.append("300k")
                        resize_command.append("-maxrate")
                        resize_command.append("700k")
                        resize_command.append("-s")
                        resize_command.append("426x240")  # determina a escala do arquivo para 480p
                    else:
                        small = True
                elif self.resolution == 360:
                    if self.compare_resolution(arquivo, 640, 320):
                        resize_command.append("-b:v")
                        resize_command.append("600k")
                        resize_command.append("-minrate")
                        resize_command.append("400k")
                        resize_command.append("-maxrate")
                        resize_command.append("1000k")
                        resize_command.append("-s")
                        resize_command.append("640x320")  # determina a escala do arquivo para 480p
                    else:
                        small = True
                elif self.resolution == 480:
                    if self.compare_resolution(arquivo, 854, 480):
                        resize_command.append("-b:v")
                        resize_command.append("1000k")
                        resize_command.append("-minrate")
                        resize_command.append("500k")
                        resize_command.append("-maxrate")
                        resize_command.append("2000k")
                        resize_command.append("-s")
                        resize_command.append("854x480")  # determina a escala do arquivo para 480p
                    else:
                        small = True
                elif self.resolution == 720:
                    if self.compare_resolution(arquivo, 1280, 720):
                        resize_command.append("-b:v")
                        resize_command.append("3300k")
                        resize_command.append("-minrate")
                        resize_command.append("1500k")
                        resize_command.append("-maxrate")
                        resize_command.append("6000k")
                        resize_command.append("-s")
                        resize_command.append("1280x720")  # determina a escala do arquivo para 720p
                    else:
                        small = True
                elif self.resolution == 1080:
                    if self.compare_resolution(arquivo, 1920, 1080):
                        resize_command.append("-b:v")
                        resize_command.append("4000k")
                        resize_command.append("-minrate")
                        resize_command.append("3000k")
                        resize_command.append("-maxrate")
                        resize_command.append("9000k")
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
        command.append(new_file_name)
        # print(command)

        if array:
            return command
        else:
            retorno = ""
            for comand in command:
                retorno += comand + " "
            return retorno

    def convert_video(self, arquivo, resize=False, remove=False, process=False, current_dir=False, no_hierarchy=False,
                      force_change_fps=False, debug=False, working_log="./working.log"):

        file_name_no_extension = os.path.splitext(arquivo.name)[0]
        extension = os.path.splitext(arquivo.name)[1][1:]
        relative_dir = str(self.so_folder_separator).join(
            str(x) for x in arquivo.path.split(str(self.so_folder_separator))[:-1]) + str(self.so_folder_separator)
        if not current_dir:
            try:
                os.makedirs(str(os.getcwd()) + self.so_folder_separator + str(relative_dir))
            except:
                pass
            new_file_name = str(str(relative_dir) + str(file_name_no_extension))
        elif not no_hierarchy:
            relative_dir = relative_dir.replace(self.pasta, "")
            try:
                os.makedirs(str(relative_dir))
            except:
                pass
            new_file_name = str(
                str(os.getcwd()) + self.so_folder_separator + str(relative_dir) + str(file_name_no_extension))
        else:
            relative_dir = relative_dir.replace(self.pasta, "")
            new_file_name = str(os.getcwd()) + self.so_folder_separator + str(file_name_no_extension)

        if extension == self.extension_convert:
            new_file_name = new_file_name + ".convert"
            same_extension = True
        else:
            same_extension = False
        new_file_name = new_file_name + "." + self.extension_convert
        try:
            converted = False
            # log_file=open(working_log,"r")
            # for line in log_file.readlines():
            # if line == new_file_name+"\n":
            # log_file.close()
            # print("working")
            # return 0
            # log_file.close()

            log_file = open(self.resized_log)
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
        # finally:
        # log_file=open(working_log,"a")
        # log_file.write(new_file_name+"\n")
        # log_file.close()
        command = self.create_command(arquivo, array=True, resize=resize, current_dir=current_dir, debug=debug,
                                      force_change_fps=force_change_fps)
        if command == "" or (converted and not debug):
            return 0

        if not process:
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
                log_file = open(self.resized_log, "a")
                log_file.write(new_file_name + "\n")
                log_file.close()
                log_file = open(self.resize_log, "a")
                log_file.write(arquivo.path + "\n")
                log_file.close()
            if remove and result.returncode == 0:
                if same_extension:
                    shutil.move(new_file_name,
                                str(relative_dir) + str(file_name_no_extension) + "." + self.extension_convert)
                else:
                    os.remove(str(arquivo.path))
            if result.returncode == 1:
                os.remove(str(new_file_name))
            return result.returncode
        else:
            processo = subprocess.Popen(command)
            retorno = {"process": processo, "new_file_name": new_file_name, "extension": extension,
                       "same_extension": same_extension, "aquivo": arquivo}
            return retorno

    def convert_all_files_sequential(self, resize=False, remove=False, current_dir=False, no_hierarchy=False,
                                     force_change_fps=False, debug=False):
        if self.files != []:
            for file in self.files:
                tmp = self.convert_video(file, resize=resize, remove=remove, process=False, current_dir=current_dir,
                                         no_hierarchy=no_hierarchy, force_change_fps=force_change_fps, debug=debug)
                if tmp not in self.results.keys():
                    self.results[tmp] = []
                self.results[tmp].append(file)
                if tmp != 0:
                    print(self.results[tmp])
                    # input("waiting")
                else:
                    self.files.remove(file)
        else:
            print(self.results)

    def convert_multiple_video(self, multiple=2, resize=False, current_dir=False, no_hierarchy=False, remove=False,
                               force_change_fps=False, working_log="./working.log"):
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
                        log_file = open(self.resized_log, "a")
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
