from allvideoconverter import converter,converter_identifier


tmdb_API_KEY = 'b888b64c9155c26ade5659ea4dd60e64'

conversor=converter_identifier(imdb_api_key=tmdb_API_KEY,resolution=720,codec="hevc_nvenc",fps=24,input_folder=".\\" ,output_folder=".\\convert",preset="slow",hwaccel="cuda",threads=4)

conversor.convert_all_files_sequential(resize=True,current_dir=False,no_hierarchy=True)
conversor.log_error_files()

conversor=converter(resolution=720,codec="hevc_nvenc",fps=24,input_folder="./",output_folder="./convert",preset="slow",hwaccel="cuda",threads=4)

conversor.convert_all_files_sequential(resize=True,current_dir=False,no_hierarchy=True,remove=True)
conversor.log_error_files()
