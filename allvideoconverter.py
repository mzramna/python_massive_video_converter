#!/usr/bin/python3
import os
import platform
import re
import shutil
import subprocess
import fnmatch


class converter:
    def __init__(self, extension_convert: str = "mkv", resolution: int = 480, codec: str = "h264_omx", fps: int = 24,
                 crf: int = 20, preset: str = "slow", hwaccel="", threads=2, log_level=32, input_folder="./",
                 output_folder="./convert/", resize_log="./resize.log", resized_log="./resized.log",sort_size=False):
        """
        class to convert huge amount of video files to same size,codec and other parameters specified below

        :param extension_convert: extension used in output file
        :param resolution: output resolution
        :param codec:output codec,default will be h264,works in raspberry pi as default
        :param fps:output fps,only tested with values below input file fps,not recomended use fps bigger than input file
        :param crf: Constant Rate Factor,defined in some codecs of ffmpeg, as said in:https://trac.ffmpeg.org/wiki/Encode/H.264
        :param preset: preset for ffmpeg to use with some codecs,as specified in: https://trac.ffmpeg.org/wiki/Encode/H.264
        :param hwaccel: hardware acceleration,as defined in: https://trac.ffmpeg.org/wiki/HWAccelIntro
        :param threads: number of threads used in ffmpeg when in cpu mode
        :param log_level: log level of ffmpeg as specified in: https://ffmpeg.org/ffmpeg.html#Generic-options
        :param input_folder: folder where will gather the video files
        :param output_folder: folder where the output files will be saved
        :param resize_log: the log file that informs all the converted files that ends correctly,if deleted or moved from the informed dir,it will restart all the conversion process
        :param resized_log: the redundant log file that informs all the converted files that ends correctly,if deleted or moved from the informed dir,it will restart all the conversion process
        """
        self.resized_log = resized_log
        self.resize_log = resize_log
        self.input_folder = input_folder
        self.output_folder = output_folder
        if not os.path.isdir(self.output_folder):
            os.mkdir(self.output_folder)
        self.codec = codec
        self.extension_convert = str(extension_convert).lower()
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
        if sort_size:
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
        # obligate de folder address ends with the so separator
        if str(self.input_folder[-1]) != self.so_folder_separator:
            self.input_folder = self.input_folder + self.so_folder_separator

        if str(self.output_folder[-1]) != self.so_folder_separator:
            self.output_folder = self.output_folder + self.so_folder_separator

    @staticmethod
    def treat_console_out(console_popen: subprocess.Popen):
        """
            this treat the console output to show better output
        :param console_popen: subprocess.popen process where the console log will be get
        :return: return in case of error,the error code from ffmpeg
        """
        number_of_frames = 0
        error = 0
        line_nun = 0
        for line in iter(console_popen.stdout.readline, b''):
            if "frame" in line and "fps" in line and "q" in line and "size" in line and "time" in line and "bitrate" in line and "speed" in line:
                '''frame= 2246 fps=748 q=15.0 size=   23365kB time=00:01:33.97 bitrate=2036.9kbits/s speed=31.3x'''
                # print(number_of_frames)
                search = None
                try:
                    search = re.search(
                        r'frame=\D*(\d*)\D*fps=\D*(\d*)\D*q=\D*([\d.]*)\D*size=\D*(\d*)\D*time=\D*(.*?)bitrate=\D*([\d.kmg]*)*bits/s\D*speed=\D*([\d.]*)\D*',
                        line)
                    try:
                        frame = int(search.group(1))
                    except:
                        frame = int(re.search(r'frame=\D*(\d+)\D*=', line).group(1))
                    try:
                        fps = int(search.group(2))
                    except:
                        fps = int(re.search(r'fps=\D*(\d+)\D*=', line).group(1))
                    try:
                        quality = float(search.group(3))
                    except:
                        quality = float(re.search(r'q=\D*([\d.]+)\D*=', line).group(1))
                    try:
                        size = int(search.group(4))
                    except:
                        size = int(re.search(r'size=\D*(\d+)\D*=', line).group(1))
                    try:
                        time = search.group(5)
                    except:
                        time = re.search(r'time=\D*(.*?)bitrate', line).group(1)
                    try:
                        bitrate = search.group(6)
                    except:
                        bitrate = re.search(r'bitrate=\D*([\d.kmg]+)*bits/s\D*=', line).group(1)
                    try:
                        speed = float(search.group(7))
                    except:
                        speed = float(re.search(r'speed=\D*([\d.]*)\D*', line).group(1))
                    conclusion = int((number_of_frames * int(frame)) / 100)
                    try:
                        eta = int((number_of_frames - int(frame)) / int(fps))
                    except:
                        eta = "nan"
                    out = str(str(line_nun) + str(conclusion) + "    eta=" + str(eta) + "s  quality=" + str(
                        quality) + "  speed=" + str(speed))
                    print(out, end="\r")
                except:
                    print(str(search), end="\r")
            elif "NUMBER_OF_FRAMES" in line:
                # print(str(line_nun)+str(line.rstrip()))
                frames = re.search(r'NUMBER_OF_FRAMES\D*(\d+).*', line)
                try:
                    number_of_frames = int(frames.group(1))
                except:
                    pass
            elif "Error" in line:
                error += 1
                print(str(error) + line)
            elif "Conversion failed" in line:
                console_popen.kill()
                return 1
            elif len(line) > 0 and line[-1] != "\r":
                if line[-1] == "\n":
                    print(str(line[:-1]))
                else:
                    print(str(line))
                pass
            # line_nun+=1

    def fill_files_list(self, folders=""):
        """
            search the media files in folder ,used also to update if any change happend
        :param folders: folder where will be searched,works with more than just the input folder
        """
        fileExtensions = ["webm", "flv", "vob", "ogg", "ogv", "drc", "gifv", "mng", "avi", "mov", "qt", "wmv", "yuv",
                          "rm", "rmvb", "asf", "amv", "mp4", "m4v", "mp\*", "m\?v", "svi", "3gp", "flv", "f4v", "mkv",
                          "divx"]
        if folders == "":
            folders = self.dir_data["dirs"]
            for file in self.dir_data["files"]:
                if str(os.path.splitext(file.name)[1][1:]).lower() in fileExtensions:
                    self.files.append(file)
        for folder in folders:
            dir_data = self.list_content_folder(folder.path)
            for file in dir_data["files"]:
                if os.path.splitext(file.name)[1][1:] in fileExtensions:
                    self.files.append(file)
            self.fill_files_list(folders=dir_data["dirs"])

    @staticmethod
    def list_content_folder(path):
        """
            get the folders and files in some path as an dict
        :param path: folder where the data will be gether
        :return: dict with the dirs and files
        """
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

    @staticmethod
    def get_video_time(File: os.DirEntry):
        """
            get the time in seconds from the select file
        :param File: media file that will be analyzed
        :return: time in seconds,return a float value,so it is very precize
        """
        check_dim = "ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1".split(
            " ")
        check_dim.append(File.path)
        dim = subprocess.run(check_dim, stdout=subprocess.PIPE)
        if dim.returncode != 0:
            return "error", int(dim.returncode)
        dim = re.compile("\'(.*)\\\\").findall(str(dim.stdout))[0]
        # print(dim)
        return float(dim)

    @staticmethod
    def get_video_codec(File: os.DirEntry, stream: int = 0):
        """
            get the video codec from the media file
        :param File: media file that will be analyzed
        :param stream: stream wich will be extracted
        :return: the codec from the video selected
        """
        check_dim = str(
            "ffprobe -v quiet -select_streams v:" + str(
                stream) + " -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1").split(
            " ")
        check_dim.append(File.path)
        dim = subprocess.run(check_dim, stdout=subprocess.PIPE)
        if dim.returncode != 0:
            return "error", int(dim.returncode)
        dim = re.compile("\'(.*)\\\\").findall(str(dim.stdout))[0]
        # print(dim)
        return str(dim)

    @staticmethod
    def get_audio_codec(File: os.DirEntry, stream: int = 0):
        """
            get the audio codec from selected stream in file
        :param File:media file that will be analyzed
        :param stream: stream wich will be extracted
        :return: the codec from the video selected
        """
        check_dim = str("ffprobe -v quiet -select_streams a:" + str(
            stream) + " -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1").split(
            " ")
        check_dim.append(File.path)
        dim = subprocess.run(check_dim, stdout=subprocess.PIPE)
        if dim.returncode != 0:
            return "error", int(dim.returncode)
        dim = re.compile("\'(.*)\\\\").findall(str(dim.stdout))[0]
        # print(dim)
        return str(dim)

    @staticmethod
    def get_subtitle_codec(File: os.DirEntry, stream: int = 0):
        """
            get the subtitle codec from selected stream in file
        :param File:media file that will be analyzed
        :param stream: stream wich will be extracted
        :return: the codec from the subtitle selected
        """
        check_dim = str("ffprobe -v quiet -select_streams s:" + str(
            stream) + " -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1").split(" ")
        check_dim.append(File.path)
        dim = subprocess.run(check_dim, stdout=subprocess.PIPE)
        if dim.returncode != 0:
            return "error", int(dim.returncode)
        dim = re.compile("\'(.*)\\\\").findall(str(dim.stdout))[0]
        # print(dim)
        return str(dim)

    @staticmethod
    def get_resolution(File: os.DirEntry, stream: int = 0):
        """
            get the resolution from selected stream in file
        :param File:media file that will be analyzed
        :param stream: stream wich will be extracted
        :return: the resolution from the subtitle selected in an dict {x:,y:}
        """
        check_dim = str(
            "ffprobe -v quiet -select_streams v:" + str(
                stream) + " -show_entries stream=width,height -of csv=p=0").split(
            " ")
        check_dim.append(File.path)
        dim = subprocess.run(check_dim, stdout=subprocess.PIPE)
        if dim.returncode != 0:
            return "error", int(dim.returncode)
        dim = re.compile("(\d+,\d+)").findall(str(dim.stdout))[0].split(",")
        # print(dim)
        dim = {"x": dim[0], "y": dim[1]}
        return dim

    @staticmethod
    def get_fps(File: os.DirEntry, stream: int = 0):
        """
            get the resolution from selected stream in file
        :param File:media file that will be analyzed
        :param stream: stream wich will be extracted
        :return: the resolution from the subtitle selected in an dict {x:,y:}
        """
        check_fps = str(
            "ffprobe -v quiet -select_streams v:" + str(
                stream) + " -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate").split(
            " ")
        check_fps.append(File.path)
        dim = subprocess.run(check_fps, stdout=subprocess.PIPE)
        if dim.returncode != 0:
            return "error", int(dim.returncode)
        dim = re.compile("(\d+/\d+)").findall(str(dim.stdout))[0].split("/")
        dim = int(dim[0]) / int(dim[1])
        return dim

    @staticmethod
    def command_to_array(command, aditional_data: [] = [], previous_array: [] = []):
        """
            convert the string to an array of words to use in a subprocess call
        :param command: string wich will be turned into array
        :param aditional_data: array with posterior parameters in array form to sum them to the result array,will be inserted after the string
        :param previous_array: array with previous parameters in array form to sum them to the result array,will be inserted before the string
        :return:
        """
        result = previous_array
        for command in command.split(" "):
            result.append(command)
        for aditional in aditional_data:
            result.append(aditional)
        return result

    @staticmethod
    def compare_resolution(File: os.DirEntry, width: int, height: int, stream: int = 0):
        """
            verify if the file resolution is smaller than the parsed values
        :param File:
        :param width:
        :param height:
        :return:
        """
        check_dim = str(
            "ffprobe -v quiet -select_streams v:" + str(
                stream) + " -show_entries stream=width,height -of csv=p=0").split(
            " ")
        check_dim.append(File.path)
        dim = subprocess.run(check_dim, stdout=subprocess.PIPE)
        if dim.returncode != 0:
            return "error", int(dim.returncode)
        dim = re.compile("(\d+,\d+)").findall(str(dim.stdout))[0].split(",")
        # print(dim)
        if int(dim[0]) > width or int(dim[1]) > height:
            return True
        else:
            return False

    @staticmethod
    def compare_fps(File: os.DirEntry, fps, stream: int = 0):
        """

        :param File:
        :param fps:
        :return:
        """
        check_fps = str(
            "ffprobe -v quiet -select_streams v:" + str(
                stream) + " -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate").split(
            " ")
        check_fps.append(File.path)
        dim = subprocess.run(check_fps, stdout=subprocess.PIPE)
        if dim.returncode != 0:
            return "error", int(dim.returncode)
        dim = re.compile("(\d+/\d+)").findall(str(dim.stdout))[0].split("/")
        dim = int(dim[0]) / int(dim[1])
        if dim > fps:
            return True
        return False

    def find_files(self, pattern,folder=""):
        """
            used to find specific files with text pattern in defined folder,if none folder is defined uses input folder
        :param pattern: regex pattern used to search files
        :param folder: folder where the files will be searched
        :return: an array of files that match the pattern
        """
        '''Return list of files matching pattern in base folder.'''
        if folder=="":
            folder=self.input_folder
        return [n for n in fnmatch.filter(os.listdir(folder), pattern) if
                os.path.isfile(os.path.join(folder, n))]

    def treat_file_name(self, File: os.DirEntry, current_dir=False, no_hierarchy=False, remove=False, debug=False):
        """

        :param File:
        :param current_dir:
        :param no_hierarchy:
        :param remove:
        :param debug:
        :return:
        """
        fileExtensions = ["webm", "flv", "vob", "ogg", "ogv", "drc", "gifv", "mng", "avi", "mov", "qt", "wmv", "yuv",
                          "rm", "rmvb", "asf", "amv", "mp4", "m4v", "mp\*", "m\?v", "svi", "3gp", "flv", "f4v", "mkv",
                          "divx"]

        file_name_no_extension = os.path.splitext(File.name)[0]
        extension = str(os.path.splitext(File.name)[1][1:])
        new_file_name = None
        folder_to_create = None
        log_file_name = None
        if (extension.lower() or self.extension_convert.lower()) in fileExtensions:
            convertable = True
            ##create relative dir
            relative_dir = ""
            if len(File.path.split(self.so_folder_separator)) > 1:
                for x in File.path.split(self.so_folder_separator)[:-1]:
                    relative_dir = str(relative_dir + str(x) + self.so_folder_separator)
            else:
                relative_dir = str(relative_dir + str(".") + self.so_folder_separator)

            if relative_dir[-1] != self.so_folder_separator:
                relative_dir = relative_dir + self.so_folder_separator
            relative_dir = relative_dir.replace(self.input_folder, "")

            if relative_dir != "":

                if relative_dir[0] == self.so_folder_separator:
                    relative_dir = relative_dir[1:]
            # print("relative_dir")
            ##make the specificities from combination of parameters of current_dir and no_hierarchy
            if not current_dir and not no_hierarchy:
                ## this works when will not save into current dir and will respect the folder hierarchy from imput folder
                # print("no current dir and hierarchy")

                new_file_name = str(str(self.output_folder) + str(relative_dir) + str(file_name_no_extension))
                folder_to_create = str(self.output_folder) + str(relative_dir)
                if self.resized_log[:2] == "./":
                    log_file_name = str(self.output_folder) + self.resized_log[2:]
            elif not current_dir and no_hierarchy:
                ## this works when will not save into current dir and will not respect the folder hierarchy from imput folder
                # print("no current dir and no hierarchy")

                new_file_name = str(str(self.output_folder) + str(file_name_no_extension))
                folder_to_create = str(self.output_folder)
                if self.resized_log[:2] == "./":
                    log_file_name = str(self.output_folder) + self.resized_log[2:]
            elif current_dir and not no_hierarchy:
                ## this works when will save into current dir and will respect the folder hierarchy from imput folder
                # print("current dir and hierarchy")
                # relative_dir = relative_dir.replace(self.input_folder, "")
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
                # relative_dir = relative_dir.replace(self.input_folder, "")
                new_file_name = str(os.getcwd()) + str(file_name_no_extension)
                folder_to_create = ""
                log_file_name = self.resized_log
            # print(folder_to_create)
            if extension == self.extension_convert  :
                same_extension = True
            else:
                same_extension = False
            if same_extension and not remove and (self.input_folder == self.output_folder or (os.getcwd() == self.input_folder and current_dir )):
                new_file_name = new_file_name + ".convert"
            if debug:
                new_file_name = str(
                    new_file_name + "." + str(self.codec) + "." + str(self.crf) + "." + str(self.preset) + "." + str(
                        self.codec) + "." + str(self.resolution) + "." + str(self.fps))
            new_file_name = new_file_name + "." + self.extension_convert
            try:
                log_file = open(log_file_name)
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
                    if File.path in line:
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
            os.remove(File)
        return {"file_name_no_extension": file_name_no_extension, "extension": extension, "convertable": convertable,
                "relative_dir": relative_dir, "new_file_name": new_file_name, "same_extension": same_extension,
                "folder_to_create": folder_to_create, "converted": converted, "log_file_name": log_file_name}

    def log_error_files(self, error_log_file="./error.log"):
        """

        :param error_log_file:
        :return:
        """
        file = open(error_log_file, "a")
        for key in self.results.keys():
            if key != 0:
                for error in self.results[key]:
                    file.write(str(key) + ";" + str(error.path) + "\n")
        file.close()

    def create_command(self, File: os.DirEntry, array=False, resize=False, current_dir=False, no_hierarchy=False,
                       force_change_fps=False, debug=False,output_name=""):
        """

        :param File:
        :param array:
        :param resize:
        :param current_dir:
        :param no_hierarchy:
        :param force_change_fps:
        :param debug:
        :return:
        """
        subtitle_srt = ["srt", "ass", "ssa"]
        subtitle_bitmap = ["dvdsub", "dvd_subtitle", "pgssub", "hdmv_pgs_subtitle"]
        name_data = self.treat_file_name(File, current_dir=current_dir, no_hierarchy=no_hierarchy, debug=debug)
        # print(name_data)
        converted=False
        if not name_data["convertable"] or (name_data["converted"] and not debug) or (
                name_data["extension"] == self.extension_convert and not resize):
            return ""
        # if os.path.isfile(name_data["new_file_name"]) and current_dir==True or os.path.isfile(str(name_data["relative_dir"]) + str(
        #                            name_data["file_name_no_extension"]) + "." + self.extension_convert) and current_dir==False :
        #  return ""
        if output_name!="":
            try:
                log_file = open(self.resized_log,"r+")
                for line in log_file.readlines():
                    if output_name in line:
                        converted = True
                        break
                log_file.close()
            except:
                pass
        if converted:
            return ""
        command = [self.ffmpeg_executable, "-y"]
        if self.hwaccel != "":
            command.append("-hwaccel")
            command.append(self.hwaccel)
        command = command + ["-hide_banner", "-loglevel", self.log_level, "-i", str(File.path)]
        # subtitles_avaliable=self.find_files(name_data["file_name_no_extension"]+"*.srt")
        # if len(subtitles_avaliable)>0:
        #    for i in subtitles_avaliable:
        #        command.append("-i")
        #        command.append(str(self.input_folder)+self.so_folder_separator+str(i))
        command = command + ["-acodec", "aac", "-c:v",
                             self.codec, "-map_metadata", "0", "-pix_fmt", "yuv420p",
                             "-threads", str(self.threads), "-copy_unknown"]
        try:
            subtitle_codec = self.get_subtitle_codec(File, 0)
            if isinstance(subtitle_codec, int):
                return ""
            elif subtitle_codec in subtitle_srt:
                command.append("-c:s")
                command.append("srt")
        except:
            pass

        if self.hwaccel == "qsv":
            command.append("-load_plugin")
            command.append("hevc_hw")
        resize_command = []
        # if used crf the resize parameters of bitrate are not necessary
        # but accord to official youtube data the bitrate used in resize parameters are
        # the best for any situation
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
                    compared_res = self.compare_resolution(File, 426, 240)
                    if not isinstance(compared_res, int) and compared_res:
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
                    compared_res = self.compare_resolution(File, 640, 320)
                    if not isinstance(compared_res, int) and compared_res:
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
                    compared_res = self.compare_resolution(File, 854, 480)
                    if not isinstance(compared_res, int) and compared_res:
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
                    compared_res = self.compare_resolution(File, 1280, 720)
                    if not isinstance(compared_res, int) and compared_res:
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
                    compared_res = self.compare_resolution(File, 1920, 1080)
                    if not isinstance(compared_res, int) and compared_res:
                        resize_command.append("-s")
                        resize_command.append("1920x1080")  # determina a escala do arquivo para 1080p
                    else:
                        small = True
                else:
                    out_scale = True
                if not small and not out_scale:
                    if self.compare_fps(File, self.fps):
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
        compared_codec = self.get_video_codec(File)
        if isinstance(compared_codec, int):
            return ""
        elif compared_codec == "mpeg4" and "h26" in self.codec:
            command.append("-bsf:v")
            command.append("mpeg4_unpack_bframes")
        # command.append(str(name_data["new_file_name"])+".tmp")
        # if len(subtitles_avaliable)>0:
        #    command.append("-c:s")
        #    command.append("mov_text")
        #    for i in range(0,len(subtitles_avaliable)+1):
        #        command.append("-map")
        #        command.append(i)
        if output_name=="":
            command.append(str(name_data["new_file_name"]))
        else:
            command.append(str(output_name))
        # print(command)

        if array:
            return command
        else:
            retorno = ""
            for comand in command:
                retorno += comand + " "
            return retorno

    def convert_video(self, File: os.DirEntry, resize=False, remove=False, process=False, current_dir=False,
                      no_hierarchy=False,
                      force_change_fps=False, debug=False, working_log="./working.log",output_name=""):
        """

        :param File:
        :param resize:
        :param remove:
        :param process:
        :param current_dir:
        :param no_hierarchy:
        :param force_change_fps:
        :param debug:
        :param working_log:
        :return:
        """
        name_data = self.treat_file_name(File, current_dir=current_dir, no_hierarchy=no_hierarchy, remove=remove,
                                         debug=debug)
        if not name_data["convertable"] or (name_data["converted"] and not debug) or (
                name_data["extension"] == self.extension_convert and not resize):
            return 0

        try:
            os.makedirs(name_data["folder_to_create"])
        except:
            pass
        command = self.create_command(File, array=True, resize=resize, current_dir=current_dir, debug=debug,
                                      force_change_fps=force_change_fps, no_hierarchy=no_hierarchy,output_name=output_name)
        if command == "" or (name_data["converted"] and not debug):
            return 0

        if not process:
            if debug:
                print(command)
            os.chdir(self.output_folder)
            result = subprocess.run(command, stdout=subprocess.PIPE)
            if result.returncode == 0 and output_name != "":
                log_file = open(self.resized_log, "a")
                log_file.write(output_name + "\n")
                log_file.close()
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
                # os.rename(name_data["new_file_name"]+".tmp",name_data["new_file_name"])
                log_file = open(name_data["log_file_name"], "a")
                log_file.write(name_data["new_file_name"] + "\n")
                log_file.close()
            if remove and result.returncode == 0:
                if name_data["same_extension"]:
                    # shutil.move(name_data["new_file_name"]+".tmp",
                    #            str(name_data["relative_dir"]) + str(
                    #                name_data["file_name_no_extension"]) + "." + self.extension_convert)
                    try:
                        shutil.move(name_data["new_file_name"],
                                    str(name_data["relative_dir"]) + str(
                                        name_data["file_name_no_extension"]) + "." + self.extension_convert)
                    except:
                        if "cannot overwrite original" not in self.results.keys():
                            self.results["cannot overwrite original"] = []
                        self.results["cannot overwrite original"].append(File.path)
                else:
                    try:
                        os.remove(str(File.path))
                    except:
                        if "cannot delete original" not in self.results.keys():
                            self.results["cannot delete original"] = []
                        self.results["cannot delete original"].append(File.path)
            elif result.returncode == 1 and name_data["new_file_name"] != "":
                try:
                    os.remove(str(name_data["new_file_name"] + ".tmp"))
                except:
                    if "cannot delete tmp" not in self.results.keys():
                            self.results["cannot delete tmp"] = []
                    self.results["cannot delete tmp"].append(str(name_data["new_file_name"] + ".tmp"))
                return result.returncode
        else:
            processo = subprocess.Popen(command)
            retorno = {"process": processo, "aquivo": File}
            return retorno

    def convert_all_files_sequential(self, resize=False, remove=False, current_dir=False, no_hierarchy=False,
                                     force_change_fps=False, debug=False):
        """

        :param resize:
        :param remove:
        :param current_dir:
        :param no_hierarchy:
        :param force_change_fps:
        :param debug:
        :return:
        """
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

class converter_identifier(converter):
    """
    until second order this just works with movies
    """
    import tmdbsimple as tmdb
    import shlex
    from imdbpie import Imdb
    from json import JSONDecoder
    import urllib
    def __init__(self, imdb_api_key, extension_convert: str = "mkv", resolution: int = 480, codec: str = "h264_omx",
                 fps: int = 24, crf: int = 20, preset: str = "slow", hwaccel="", threads=2, log_level=32,
                 input_folder="./", output_folder="./convert/", resize_log="./resize.log", resized_log="./resized.log"):
        """

        :param imdb_api_key:
        :param extension_convert:
        :param resolution:
        :param codec:
        :param fps:
        :param crf:
        :param preset:
        :param hwaccel:
        :param threads:
        :param log_level:
        :param input_folder:
        :param output_folder:
        :param resize_log:
        :param resized_log:
        """
        super().__init__(extension_convert, resolution, codec, fps,
                         crf, preset, hwaccel, threads, log_level, input_folder,
                         output_folder, resize_log, resized_log)
        self.tmdb.API_KEY = imdb_api_key

    def collect_stream_metadata(self, File: os.DirEntry):
        """
        Returns a list of streams' metadata present in the media file passed as
        the argument (filename)
        :param File:
        :return:
        """
        command = 'ffprobe -i "{}" -show_streams -of json'.format(File)
        args = self.shlex.split(command)
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             universal_newlines=True)
        out, err = p.communicate()

        json_data = self.JSONDecoder().decode(out)

        return json_data

    def create_command(self, File: os.DirEntry, array=False, resize=False, current_dir=False, no_hierarchy=False,
                       force_change_fps=False, debug=False,output_name=""):
        """

        :param File:
        :param array:
        :param resize:
        :param current_dir:
        :param no_hierarchy:
        :param force_change_fps:
        :param debug:
        :return:
        """
        avaliable_metadatas = {
            "mp4": ["title", "author", "album_artist", "album", "grouping", "composer", "year", "track", "comment",
                    "copyright", "show", "episode_id", "network", "lyrics"],
            "m4v": ["title", "author", "album_artist", "album", "grouping", "composer", "year",
                    "track", "comment", "copyright", "show", "episode_id", "network",
                    "lyrics"],
            "mov": ["title", "author", "album_artist", "album", "grouping", "composer", "year",
                    "track", "comment", "copyright", "show", "episode_id", "network",
                    "lyrics"],
            "mkv": ["title", "author", "album_artist", "album", "grouping", "composer", "year",
                    "track", "comment", "copyright", "show", "episode_id", "network",
                    "lyrics"]}
        title = os.path.splitext(File.name)[0]
        command = super().create_command(File, True, resize, current_dir, no_hierarchy, force_change_fps, debug)
        output_file = command[-1]
        command = command[:-1]
        stream_md = self.collect_stream_metadata(File)
        streams_to_process = []

        print('\nSearching IMDb for "{}"'.format(title))

        imdb = self.Imdb()
        movie_results = []
        while not movie_results and len(title) > 1:
            results = imdb.search_for_title(title)
            for result in results:
                if result['type'] == "feature":
                    movie_results.append(result)
            if not movie_results:
                title = title[:-1]

        if not movie_results:
            while not movie_results:
                title = input('\nNo results for "' + title +
                              '" Enter alternate/correct movie title >> ')

                results = imdb.search_for_title(title)
                for result in results:
                    if result['type'] == "feature":
                        movie_results.append(result)

        # The most prominent result is the first one
        # mpr - Most Prominent Result
        mpr = movie_results[0]
        print('\nFetching data for {} ({})'.format(mpr['title'],
                                                   mpr['year']))
        imdb_movie = imdb.get_title(mpr['imdb_id'])

        imdb_movie_title = imdb_movie['base']['title']
        imdb_movie_id = mpr['imdb_id']
        imdb_movie_year = mpr['year']
        try:
            imdb_movie_rating = imdb_movie['ratings']['rating']
        except:
            imdb_movie_rating = 0
        if not 'outline' in imdb_movie['plot']:
            imdb_movie_plot_outline = (imdb_movie['plot']['summaries'][0]
            ['text'])
            print("\nPlot outline does not exist. Fetching plot summary "
                  "instead.\n\n")
        else:
            imdb_movie_plot_outline = imdb_movie['plot']['outline']['text']

        # Composing a string to have the rating and the plot of the
        # movie which will go into the 'comment' metadata of the
        # mp4 file.
        imdb_rating_and_plot = str('IMDb rating ['
                                   + str(float(imdb_movie_rating))
                                   + '/10] - '
                                   + imdb_movie_plot_outline)

        imdb_movie_genres = imdb.get_title_genres(imdb_movie_id)['genres']

        # Composing the 'genre' string of the movie.
        # I use ';' as a delimeter to searate the multiple genre values
        genre = ';'.join(imdb_movie_genres)
        print(avaliable_metadatas[self.extension_convert])
        for metadata in imdb_movie['base']:
            print(metadata)
            if metadata in avaliable_metadatas[self.extension_convert]:
                command.append("-metadata")
                command.append(metadata + "=" + str(imdb_movie['base'][metadata]))
        command.append("-metadata")
        command.append("description=" + str(imdb_rating_and_plot))
        command.append("-metadata")
        command.append("genre=" + str(genre))
        command.append("-metadata")
        command.append("rating=" + str(imdb_movie_rating / 2))
        command.append("-metadata")
        command.append("imdb=" + str(imdb_movie_id))
        newfilename = (imdb_movie_title
                       + ' ('
                       + str(imdb_movie_year)
                       + ').' + self.extension_convert)
        newfilename = (newfilename
                       .replace(':', ' -')
                       .replace('/', ' ')
                       .replace('?', ''))
        for f in streams_to_process:
            command.append("-map 0:{}".format(f))

        try:
            poster_filename = title + ".jpg"
            if not os.path.isfile(poster_filename):
                print('\nFetching the movie poster...')
                tmdb_find = self.tmdb.Find(imdb_movie_id)
                tmdb_find.info(external_source='imdb_id')

                path = tmdb_find.movie_results[0]['poster_path']
                complete_path = r'https://image.tmdb.org/t/p/w780' + path

                uo = self.urllib.request.urlopen(complete_path)
                with open(poster_filename, "wb") as poster_file:
                    poster_file.write(uo.read())
                    poster_file.close()
            command.append("-attach")
            command.append(poster_filename)
            command.append("-metadata:s:t:0")
            command.append("mimetype=image/jpg")
        except:
            pass

        if output_name == "":
            command.append(str(output_file))
        else:
            command.append(str(output_name))
        if array:
            return command
        else:
            retorno = ""
            for comand in command:
                retorno += comand + " "
            return retorno

    def convert_video(self, File: os.DirEntry, resize=False, remove=False, process=False, current_dir=False,
                      no_hierarchy=False,
                      force_change_fps=False, debug=False, working_log="./working.log",output_name=""):
        """

        :param File:
        :param resize:
        :param remove:
        :param process:
        :param current_dir:
        :param no_hierarchy:
        :param force_change_fps:
        :param debug:
        :param working_log:
        :return:
        """
        name_data = self.treat_file_name(File, current_dir=current_dir, no_hierarchy=no_hierarchy, remove=remove,
                                         debug=debug)
        if not name_data["convertable"] or (name_data["converted"] and not debug) or (
                name_data["extension"] == self.extension_convert and not resize):
            return 0

        try:
            os.makedirs(name_data["folder_to_create"])
        except:
            pass
        command = self.create_command(File, array=True, resize=resize, current_dir=current_dir, debug=debug,
                                      force_change_fps=force_change_fps, no_hierarchy=no_hierarchy,output_name=output_name)
        if command == "" or (name_data["converted"] and not debug):
            return 0
        print(command)
        if not process:
            # print(command)
            # os.chdir(self.output_folder)
            result = subprocess.run(command, stdout=subprocess.PIPE)
            # result = subprocess.Popen(command, stdout = subprocess.PIPE,stderr = subprocess.STDOUT,universal_newlines=True)
            # line_nun=0

            try:
                os.remove(os.path.splitext(File.name)[0] + ".jpg")
            except:
                pass
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
                # os.rename(name_data["new_file_name"]+".tmp",name_data["new_file_name"])
                log_file = open(name_data["log_file_name"], "a")
                log_file.write(name_data["new_file_name"] + "\n")
                log_file.close()
            if remove and result.returncode == 0:
                if name_data["same_extension"]:
                    # shutil.move(name_data["new_file_name"]+".tmp",
                    #            str(name_data["relative_dir"]) + str(
                    #                name_data["file_name_no_extension"]) + "." + self.extension_convert)
                    shutil.move(name_data["new_file_name"],
                                str(name_data["relative_dir"]) + str(
                                    name_data["file_name_no_extension"]) + "." + self.extension_convert)
                else:
                    os.remove(str(File.path))
            if result.returncode == 1 and name_data["new_file_name"] != "":
                try:
                    os.remove(str(name_data["new_file_name"] + ".tmp"))
                except:
                    pass
            return result.returncode
        else:
            processo = subprocess.Popen(command)
            retorno = {"process": processo, "aquivo": File}
            return retorno

    def convert_all_files_sequential(self, resize=False, remove=False, current_dir=False, no_hierarchy=False,
                                     force_change_fps=False, debug=False):
        """

        :param resize:
        :param remove:
        :param current_dir:
        :param no_hierarchy:
        :param force_change_fps:
        :param debug:
        :return:
        """
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
