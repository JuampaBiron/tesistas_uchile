import pandas as pd
import shutil
import os
import logging 

# Configuración del logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class BuildWorktray:
    def __init__(self):
        self.process_data_folder = r"process_data"
        #archivos input
        self.template_worktray = r"input\_worktray_template.xlsx"
        self.template_estudiantes = r"input\_estudiantes_postgrado.xlsx"
        self.template_programas = r"input\_programas_postgrado.xlsx"
        self.template_prof = r"input\_profesores.xlsx"
        #archivos process_data
        self.worktray_path = r"process_data\worktray.xlsx"
        self.estudiantes = r"process_data\estudiantes_postgrados.xlsx"
        self.programas = r"process_data\programas_postgrado.xlsx"
        self.profesores = r"process_data\profesores.xlsx"
        self.memory_file = r"out\memory.xlsx"
    
    def run_workflow(self):
        # Delete process_data
        if os.path.exists(self.process_data_folder) and os.path.isdir(self.process_data_folder):
            shutil.rmtree(self.process_data_folder)
            logging.info(f"Carpeta {self.process_data_folder} eliminada correctamente.")
            
        else:
            logging.info(f"La ruta {self.process_data_folder} no existe o no es una carpeta.")
        os.mkdir(self.process_data_folder)
        logging.info(f"Carpeta '{self.process_data_folder}' creada correctamente.")
        #Copying files from input to process data
        shutil.copyfile(src=self.template_worktray, dst=self.worktray_path)
        logging.info(f"Worktray copiado correctamente en process data.")
        shutil.copyfile(src=self.template_programas, dst=self.programas)
        logging.info(f"Programas copiado correctamente en process data.")
        shutil.copyfile(src=self.template_prof, dst=self.profesores)
        logging.info(f"Profesores copiado correctamente en process data.")
        shutil.copyfile(src=self.template_estudiantes, dst=self.estudiantes)
        logging.info(f"estudiantes_postgrado copiado correctamente en process data.")
        """
        # Concat memory into worktray
        df_memory = pd.read_excel(self.memory_file)
        df_worktray = pd.read_excel(self.worktray_path)
        df_merged = pd.concat([df_memory, df_worktray], ignore_index=True)
        df_merged.to_excel(self.worktray_path,sheet_name="base",index=False)"""


if __name__ == "__main__":
    BuildWorktray().run_workflow()
