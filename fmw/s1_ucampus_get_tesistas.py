from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import logging
import os
import time
import pandas as pd

# Configuración del logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class UcampusTesistas:
    def __init__(self, url, min_year:int, max_year:int, keep_web_alive=True):
        self.url = url
        self.min_year = min_year
        self.max_year = max_year
        self.keep_web_alive = keep_web_alive
        self.logger = logging.getLogger(self.__class__.__name__)
        self.user = os.environ.get("UCAMPUS_USER")
        self.password = os.environ.get("UCAMPUS_PASSWORD")
        self.driver = self._setup_driver()
        self.wait_1 = WebDriverWait(self.driver, 1)
        self.wait_2 = WebDriverWait(self.driver, 2)
        self.wait_10 = WebDriverWait(self.driver, 10)
        self.wait_20 = WebDriverWait(self.driver, 20)
        #archivos process_data
        self.estudiantes = r"process_data\estudiantes_postgrados.xlsx"
        self.listado_programas = r"process_data\programas_postgrado.xlsx"


    def _setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--disable-gpu')
        chrome_prefs = {
            "download.default_directory": os.path.curdir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "safebrowsing.enabled": True,
            "safebrowsing.disable_download_protection": True,
        }
        chrome_options.add_experimental_option("prefs", chrome_prefs)
        return webdriver.Chrome(options=chrome_options, keep_alive=self.keep_web_alive)
    
    def close(self):
        if self.driver:
            self.driver.quit()
    
    def log_in(self):
        self.driver.get(self.url)
        self.driver.maximize_window()
        logging.info(f"Página cargada: {self.url}")
        input_text_field = (By.XPATH,'//input[@name="username"]')
        input_password = (By.XPATH,'//input[@name="password"]')
        btn_ingresar = (By.XPATH, '//input[@type="submit" and @value="Ingresar"]')
        self.wait_10.until(EC.element_to_be_clickable(input_text_field))
        self.driver.find_element(*input_text_field).send_keys(self.user)
        self.driver.find_element(*input_password).send_keys(self.password)
        self.driver.find_element(*btn_ingresar).click()
    
    def navigate_indicadores(self):
        df_programas = pd.read_excel(self.listado_programas)
        df_estudiantes = pd.read_excel(self.estudiantes)
        try:
            btn_indicadores_autoevaluacion = (By.XPATH, '//li[@id="fcfm_acreditacion"]//a[text()="Indicadores Autoevaluación"]')
            self.wait_10.until(EC.element_to_be_clickable(btn_indicadores_autoevaluacion))
            self.driver.find_element(*btn_indicadores_autoevaluacion).click()
        except Exception as e:
            logging.error(f"No se pudo navegar hasta indicadores académicos: {e}")
            raise

        for programa in df_programas["Nombre Programa"].to_list():
            try:
                btn_programa = (By.XPATH, f'//a[text()="{programa}"]')
                self.wait_2.until(EC.element_to_be_clickable(btn_programa))
                self.driver.find_element(*btn_programa).click()

            except Exception as e:
                logging.error(f"Error inesperado al hacer click en {programa}: ", exc_info=False)
                raise

            for cohorte in range(self.min_year, self.max_year + 1):
                logging.info(f"Cohorte {cohorte}")
                btn_regulares = (By.XPATH, f"//a[@href=\"javascript:ls('regular',{cohorte})\"]")

                try:
                    self.wait_1.until(EC.element_to_be_clickable(btn_regulares))
                    self.driver.find_element(*btn_regulares).click()
                    regulares = (By.XPATH, '//li[@class="objetoflex"]')
                    self.wait_2.until(EC.element_to_be_clickable(regulares))
                    lista_regulares = self.driver.find_elements(*regulares)

                    for est in lista_regulares:
                        estudiante = est.text
                        nombre_completo, rut = estudiante.split("\n")
                        nombre_apellido = nombre_completo.split(", ")[1] + " " + nombre_completo.split(", ")[0]

                        nueva_fila = pd.DataFrame({
                            "Nombre estudiante": [nombre_apellido],
                            "Rut": [rut],
                            "Cohorte": [cohorte],
                            "Programa": [programa]
                        })

                        df_estudiantes = pd.concat([df_estudiantes, nueva_fila], ignore_index=True)
                    
                    df_estudiantes.to_excel(self.estudiantes, index=False, sheet_name="base")

                except Exception as e:
                    logging.error(f"No se encontró la cohorte {cohorte}: ", exc_info=False)
                    

                finally:
                    try:
                        btn_cerrar = (By.XPATH, '//a[@rel="modal:close" and text()="Close"]')
                        self.wait_2.until(EC.element_to_be_clickable(btn_cerrar))
                        self.driver.find_element(*btn_cerrar).click()
                        logging.info("Cerrando popup")
                    except Exception as e:
                        logging.error(f"No se encontró Popup: {e}", exc_info=False)
                        
    
            time.sleep(0.5)
            self.driver.find_element(*btn_indicadores_autoevaluacion).click()
            df_programas.loc[df_programas["Nombre Programa"]==programa, "Encontrado"] = "TRUE"
            logging.info(f"Se encnotró link de {programa}")    

        df_programas = df_programas.drop_duplicates()
        df_programas.to_excel(self.listado_programas, sheet_name="base", index=False)
        time.sleep(2)
    
    def run_workflow(self):
        logging.info(f"************ Inicio del workflow {self.__class__.__name__} ************")
        try:
            if not self.user or not self.password:
                logging.error("Credenciales no encontradas en las variables de entorno. Finalizando el proceso.")
                return
            logging.info("Starting Ucampus Login")
            self.log_in()
            logging.info("Finishing Ucampus Login")
            self.navigate_indicadores()
            logging.info("Closing apps")
            self.close()
            
        except Exception as e:
            logging.error(f"Error en workflow: {self.__class__.__name__}: {e}", exc_info=True)
        finally:
            self.close()
            logging.info(f"************ Termino del workflow {self.__class__.__name__} ************")




if __name__ == "__main__":
    url = "https://ucampus.uchile.cl"
    proceso = UcampusTesistas(url=url,min_year=2018, max_year=2024)
    proceso.run_workflow()