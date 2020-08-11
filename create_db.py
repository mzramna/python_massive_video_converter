import os
import platform
import re
import sqlite3
import subprocess


class controller:
    def __init__(self, start_folder="./", db_locate="./database.db"):
        self.start_folder=start_folder
        self.conn = sqlite3.connect(db_locate)
        self.create_db()
        if platform.system() == 'Windows':
            self.so_folder_separator="\\"
        elif platform.system() == 'Linux':
            self.so_folder_separator = "/"

    def list_content_folder(self, path):
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

    def compare_resolution(self,arquivo):
        check_dim="ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0".split(" ")
        check_dim.append(arquivo.path)
        dim = subprocess.run(check_dim, stdout=subprocess.PIPE)
        dim=re.compile("(\d+\,\d+)").findall(str(dim.stdout))[0].split(",")
        #print(dim)
        return dim

    def compare_fps(self,arquivo):
        check_fps="ffprobe -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate".split(" ")
        check_fps.append(arquivo.path)
        dim = subprocess.run(check_fps, stdout=subprocess.PIPE)
        dim=re.compile("(\d+\/\d+)").findall(str(dim.stdout))[0].split("/")
        dim=int(dim[0])/int(dim[1])#x,y
        return dim

    def create_db(self):
        self.cursor = self.conn.cursor()
        self.cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='diretorio' ''')

        if self.cursor.fetchall()[0][0] == 1:
            pass
        else:
            print("not exist dir")
            self.cursor.execute('''
                        CREATE TABLE IF NOT EXISTS `diretorio` (
                          `id_diretorio` INTEGER PRIMARY KEY AUTOINCREMENT,
                          `id_diretorio_pai` INTEGER REFERENCES diretorio(id_diretorio),
                          `nome` text NOT NULL);''')

            self.conn.commit()
            self.cursor.execute("""
                                INSERT INTO diretorio ( nome,id_diretorio_pai)
                                VALUES (?,?)
                            """, ("root", 0))  # resize=0,não iniciado]
            self.conn.commit()

        self.cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='arquivo' ''')
        if self.cursor.fetchall()[0][0]==1:
            pass
        else:
            print("not exist arquivo")
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS `arquivo` (
                  `id_arquivo` INTEGER PRIMARY KEY AUTOINCREMENT,
                  `id_diretorio` INTEGER REFERENCES diretorio(id_diretorio),
                  `nome` text NOT NULL,
                  `path` text NOT NULL,
                  `extensao` text NOT NULL,
                  `resolucao_x` int(6) NOT NULL,
                  `resolucao_y` int(6) NOT NULL,
                  `resize` int(1) NOT NULL,
                  `delete` int(1) NOT NULL,
                  `fps` int(3) NOT NULL,
                  `estado_convertido` int(1) NOT NULL);''')
            self.conn.commit()
        self.cursor.close()

    def recreate_path_file(self, file):
        arquivo=self.search_arquivo(path=file.path)
        tmp=self.search_diretorio(id_diretorio=arquivo["id_diretorio"])
        diretorios=[]
        while tmp["id_diretorio_pai"]!= 0:
            diretorios.append(tmp)
            tmp = self.search_diretorio(id_diretorio=tmp["id_diretorio_pai"])
        tmp=self.start_folder
        for i in reversed(diretorios):
            tmp+=i+self.so_folder_separator
            os.mkdir(tmp)

    def add_file(self,file,diretorio,resize,delete):
        fps=self.compare_fps(file)
        dim=self.compare_resolution(file)
        extensao=os.path.splitext(file.name)[1][1:]
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            INSERT INTO arquivo (id_diretorio, nome,path, extensao, resolucao_x, resolucao_y, resize, delete, fps,estado_convertido)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, ( diretorio,file.name,file.path, extensao, dim[0], dim[1], resize, delete, fps,0))#resize=0,não iniciado
        self.conn.commit()
        self.cursor.close()

    def add_dir(self,diretorio,diretorio_pai:int=0):
        self.cursor = self.conn.cursor()
        # self.cursor.execute(''' SELECT id_diretorio FROM diretorio WHERE id_diretorio_pai=? ''',(diretorio_pai))
        # diretorio_pai=self.cursor.fetchall()[0]
        self.cursor.execute("""
                    INSERT INTO diretorio ( nome,id_diretorio_pai)
                    VALUES (?,?)
                """, (diretorio.name,diretorio_pai))  # resize=0,não iniciado]
        self.conn.commit()
        self.cursor.close()

    def search_diretorio(self, id_diretorio: int = -1, id_diretorio_pai: int = -1, nome: str = ""):
        command = "SELECT * FROM arquivo WHERE "
        added=0
        if id_diretorio == -1 and id_diretorio_pai == -1 and nome == "":
            return None
        if id_diretorio != -1:
            command += "id_diretorio=" + str(id_diretorio) + " "
            added+=1
        if id_diretorio_pai != -1:
            if added>0:
                command+="AND "
            command += "id_diretorio_pai=" + str(id_diretorio_pai) + " "
            added+=1
        if nome != -1:
            if added>0:
                command+="AND "
            command += "nome=" + str(nome) + " "
        self.cursor = self.conn.cursor()

        self.cursor.execute(command)
        ret = self.cursor.fetchall()
        self.cursor.close()
        retorno=[]
        for dir in ret:
            retorno.append(self.diretorio_element_query_to_dict(dir))
        return retorno

    def diretorio_element_query_to_dict(self, ret):
        retorno = {}
        retorno["id_diretorio"] = int(ret[0])
        retorno["id_diretorio_pai"] = int(ret[1])
        retorno["nome"] = str(ret[2])
        return retorno

    def search_arquivo(self, id_arquivo: int = -1, id_diretorio: int = -1, nome: str = "",path:str="",extensao:str="",resolucao_x:int=-1,resolucao_y:int=-1,resize:int=-1,delete:int=-1,fps:int=-1,estado_convertido:int=-1):
        command = "SELECT * FROM arquivo WHERE "
        added=0
        if id_diretorio == -1 and id_diretorio == -1 and nome == "" and path == "" and extensao != -1 and resolucao_x!=-1 and resolucao_y!=-1 and resize!=-1 and delete!=-1 and fps!=-1 and estado_convertido!=-1:
            return None
        if id_arquivo != -1:
            command += "id_arquivo=" + str(id_arquivo) + " "
            added+=1
        if id_diretorio != -1:
            if added>0:
                command+="AND "
            command += "id_diretorio=" + str(id_diretorio) + " "
            added+=1
        if nome != -1:
            if added>0:
                command+="AND "
            command += "nome=" + str(nome) + " "
            added+=1
        if path != -1:
            if added>0:
                command+="AND "
            command += "path=" + str(path) + " "
            added+=1
        if extensao != -1:
            if added>0:
                command+="AND "
            command += "extensao=" + str(extensao) + " "
            added += 1
        if resolucao_x!=-1:
            if added>0:
                command+="AND "
            command+= "resolucao_x="+str(resolucao_x)+" "
            added += 1
        if resolucao_y!=-1:
            if added>0:
                command+="AND "
            command+= "resolucao_y="+str(resolucao_y)+" "
            added += 1
        if resize!=-1:
            if added>0:
                command+="AND "
            command+= "resize="+str(resize)+" "
            added += 1
        if delete!=-1:
            if added>0:
                command+="AND "
            command+= "delete="+str(delete)+" "
            added += 1
        if fps!=-1:
            if added>0:
                command+="AND "
            command+= "fps="+str(fps)+" "
            added += 1
        if estado_convertido!=-1:
            if added>0:
                command+="AND "
            command+= "estado_convertido="+str(estado_convertido)+" "
            added += 1
        self.cursor = self.conn.cursor()
        self.cursor.execute(command)
        ret = self.cursor.fetchall()
        self.cursor.close()
        retorno=[]
        for file in ret:
            retorno.append(self.arquivo_element_query_to_dict(file))
        return retorno

    def arquivo_element_query_to_dict(self, ret):
        retorno = {}
        retorno["id_arquivo"] = int(ret[0])
        retorno["id_diretorio"] = int(ret[1])
        retorno["nome"] = str(ret[2])
        retorno["path"] = str(ret[3])
        retorno["extensao"] = str(ret[4])
        retorno["resolucao_x"] = int(ret[5])
        retorno["resolucao_y"] = int(ret[6])
        retorno["resize"] = int(ret[7])
        retorno["delete"] = int(ret[8])
        retorno["fps"] = int(ret[9])
        retorno["estado_convertido"] = int(ret[10])
        return retorno


    def rebuild_path_diretorio(self,id_diretorio):
        tmp=self.search_diretorio(id_diretorio=id_diretorio)
        retorno=""
        while tmp["id_diretorio_pai"]!=0:
            retorno=tmp["nome"]+self.so_folder_separator+retorno
            tmp = self.search_diretorio(id_diretorio=tmp["id_diretorio_pai"])
        return self.start_folder+self.so_folder_separator+retorno

    def fill_db(self,current_dir=1):
        if current_dir==1:
            content = self.list_content(self.start_folder)
            for folder in content["dirs"]:
                self.add_dir(diretorio_pai=0,diretorio=folder.name)
            for folder in content["dirs"]:
                tmp=self.search_diretorio(nome=folder.name)
                self.fill_db(current_dir=tmp["id_diretorio"])
        else:
            path=self.rebuild_path_diretorio(current_dir)
