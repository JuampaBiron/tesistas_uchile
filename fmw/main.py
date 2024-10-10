import logging
import os
import argparse
import pandas as pd
from build_worktray import BuildWorktray
from s1_ucampus_get_tesistas import UcampusTesistas  
from s2_ucampus_get_prof_guia import UcampusGetProfeGuia



# Configuración del logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Robot:
    def __init__(self, start_state, final_state,min_cohorte, max_cohorte):
        self.url = "https://ucampus.uchile.cl"
        self.state = start_state
        self.final_state = final_state
        self.min_cohorte = min_cohorte
        self.max_cohorte = max_cohorte

    def run(self):
        while self.state <= self.final_state:
            if self.state == 0:
                BuildWorktray().run_workflow()
            elif self.state == 1:
                UcampusTesistas(url=self.url,min_year=self.min_cohorte,max_year=self.max_cohorte).run_workflow()
            elif self.state == 2:
                UcampusGetProfeGuia(url=self.url).run_workflow()
            self.state += 1
        logging.info("Proceso completado.")

    
if __name__ == "__main__":    
    robot = Robot(start_state=2, final_state=2, min_cohorte=2018, max_cohorte=2024)
    robot.run()

