from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
import os
import time
import pandas as pd

# Configuración del logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class UcampusGetProfeGuia:
    def __init__(self, url, keep_web_alive=True):
        self.url = url
        self.keep_web_alive = keep_web_alive
        self.logger = logging.getLogger(self.__class__.__name__)
        self.user = os.environ.get("UCAMPUS_USER")
        self.password = os.environ.get("UCAMPUS_PASSWORD")
        self.driver = self._setup_driver()
        self.wait_1 = WebDriverWait(self.driver, 1)
        self.wait_2 = WebDriverWait(self.driver, 2)
        self.wait_10 = WebDriverWait(self.driver, 10)
        self.wait_20 = WebDriverWait(self.driver, 20)
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
    
    def navigate_bia(self):
        df_estudiantes = pd.read_excel(self.estudiantes)

        btn_boletines = (By.XPATH, "//a[contains(@href, 'https://ucampus.uchile.cl/m/fcfm_bia/') and contains(text(), 'Boletines')]")
        self.wait_10.until(EC.element_to_be_clickable(btn_boletines))
        self.driver.find_element(*btn_boletines).click()

        for index, row in df_estudiantes.iterrows():
            boolExtracted = row["Extracted"]
            if row["Tesista"] != True:
                rut = row['Rut']
                programa = row['Programa']
                cohorte = row["Cohorte"]
                total_rows_to_process = df_estudiantes[df_estudiantes['Extracted'] == "TRUE"].shape[0]
                total_rows = df_estudiantes.shape[0]

                try:
                    logging.info(f"Processing {total_rows_to_process}/{total_rows}")
                    logging.info(f"-- {rut} - {cohorte} - {programa} --")
                    text_field = (By.XPATH,"//input[@type='text' and @class='autofocus' and @placeholder='Persona']")
                    self.wait_2.until(EC.element_to_be_clickable(text_field))
                    self.driver.find_element(*text_field).send_keys(rut)
                    btn_buscar = (By.XPATH, "//input[@type='submit' and contains(@value, 'Buscar')]")
                    self.driver.find_element(*btn_buscar).click()
                    seccion_tesis = None
                    
                    try:
                        seccion_inscripcion_tesis = (By.XPATH,"//h2[contains(text(), 'Exámenes de Grado y/o Título')]")
                        self.wait_1.until(EC.element_to_be_clickable(seccion_inscripcion_tesis))
                        seccion_tesis = self.driver.find_element(*seccion_inscripcion_tesis).text
                        logging.info(f"Tiene {seccion_tesis}")
                    except:
                        logging.info("No existe sección de tesis")

                    if seccion_tesis:
                        target_table = self.driver.find_element("xpath", "//h2[contains(text(), 'Exámenes de Grado y/o Título')]/following::table[.//th[contains(text(), 'Examen / Título')]]")
                        rows = target_table.find_elements("xpath", ".//tbody/tr")

                        professor = None  # Initialize professor variable
                        for tesis_row in rows:
                            if programa in tesis_row.text:
                                professor = tesis_row.find_element("xpath", "./td[contains(@class, 'privado')]").text
                                logging.info(professor)

                        if professor and isinstance(professor, str):
                            df_estudiantes.at[index, "Profesor guia"] = professor
                            df_estudiantes.at[index, "Tesista"] = "TRUE"
                            logging.info(f"Profesor encontrado en sección tesis: {professor}")
                        else:
                            try:
                                posible = (By.XPATH, f"//tr[td/h1[contains(text(),'Inscripción del Tema de Tesis')] \
                                and td[contains(text(),'{programa}')] \
                                and td[contains(text(),'Aceptado')]]")
                                tesista = self.driver.find_element(*posible).text
                                logging.info(f"Tesista sin profe asociado")
                                df_estudiantes.at[index, "Tesista"] = "TRUE"

                            except:
                                logging.info(f"No se encontró tesista")
                                df_estudiantes.at[index, "Tesista"] = "FALSE"
                                logging.info(f"Sección tesis encontrada pero no se encontró profesor")

                    else:
                        # Si no hay sección de tesis, marcar como 'FALSE'
                        df_estudiantes.at[index, "Tesista"] = "FALSE"
                        logging.info(f"No se encontró sección tesis para {rut}")

                    df_estudiantes.at[index, "Extracted"] = "TRUE"

                except Exception as e:
                    df_estudiantes.at[index, "Extracted"] = "FALSE"
                    logging.error("No se pudo procesar el estudiante: %s", e)

                # Attempt to save the DataFrame to Excel
                try:
                    df_estudiantes.to_excel(self.estudiantes, index=False, sheet_name="base")
                except Exception as e:
                    logging.error("Error al guardar el archivo de Excel: %s", e)


    def run_workflow(self):
        logging.info(f"************ Inicio del workflow {self.__class__.__name__} ************")
        self.log_in()
        try:
            self.navigate_bia()
        except Exception as e:
            logging.error(f"Error en {self.__class__.__name__} durante la navegación: %s", e)
        finally:
            self.close()  # Ensure the driver is closed
            logging.info(f"************ Termino del workflow {self.__class__.__name__} ************")

if __name__ == "__main__":
    url = "https://ucampus.uchile.cl"
    proceso = UcampusGetProfeGuia(url=url)
    proceso.run_workflow()
