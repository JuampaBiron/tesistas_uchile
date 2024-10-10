from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
import os
import time
import pandas as pd
import re

# Configuración del logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class GetAllProfessors:
    def __init__(self, url, keep_web_alive=True):
        self.url = url
        self.keep_web_alive = keep_web_alive
        self.logger = logging.getLogger(self.__class__.__name__)
        self.user = os.environ.get("UCAMPUS_USER")
        self.password = os.environ.get("UCAMPUS_PASSWORD")
        self.driver = self._setup_driver()
        self.wait_1 = WebDriverWait(self.driver, 1)
        self.wait_5 = WebDriverWait(self.driver, 5)
        self.wait_10 = WebDriverWait(self.driver, 10)
        self.wait_20 = WebDriverWait(self.driver, 20)
        self.profesores = "framework\input\profesores manual.xlsx"
        self.estudiantes = "framework\input\estudiantes_postgrado.xlsx"

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
    
    def click_btn(self, xpath:str):
        btn_to_be_clicked = (By.XPATH, xpath)
        self.wait_10.until(EC.element_to_be_clickable(btn_to_be_clicked))
        self.driver.find_element(*btn_to_be_clicked).click()
    
    def navigate_catalogo_cursos(self):
        df_profesores = pd.read_excel(self.profesores)
        self.click_btn(xpath='//a[@href="https://ucampus.uchile.cl/m/fcfm_catalogo/" and text()="Catálogo de Cursos"]')
        elementos_profes = (By.XPATH,'//div[@id="body"]//h1[img[@class="photo foto chica"]]')
        self.click_btn(xpath='//div[@id="depto_chosen"]')
        ul = (By.XPATH, '//ul[@class="chosen-results"]')
        time.sleep(3)
        #self.wait_10.until(EC.element_to_be_clickable(ul))
        ul_element = self.driver.find_element(*ul)
        # Encuentra todos los elementos <li> dentro del <ul> utilizando XPath
        lista_departamentos = ul_element.find_elements(By.XPATH, '//li[contains(@class, "active-result")]')
        for semestre in range(1,2):
            for n in range(1,len(lista_departamentos)):
                logging.info(f"N {n}")
                url = f"https://ucampus.uchile.cl/m/fcfm_catalogo/?semestre=2024{semestre}&depto={n}"
                self.driver.get(url)
                logging.info(f"Url {url}")
                elementos_profes = (By.XPATH,'//div[@id="body"]//h1[img[@class="photo foto chica"]]')
                self.wait_10.until(EC.visibility_of_element_located(elementos_profes))
                lista_nombres_profes = self.driver.find_elements(*elementos_profes)
                logging.info(f"Lista con: {len(lista_nombres_profes)} profes")
                for elemento in lista_nombres_profes:
                    nombre_ucampus = elemento.text
                    nueva_fila = pd.DataFrame({
                    "Nombre ucampus": [nombre_ucampus],
                    "Nombre portafolio": [""]  # Puedes dejar esto vacío o asignar un valor específico
                    })

                    # Usar pd.concat para agregar la nueva fila
                    df_profesores = pd.concat([df_profesores, nueva_fila], ignore_index=True)
                        #Agregar el nombre a una fila nueva
                logging.info(f"Datos agregados al df")
            
        df_profesores.drop_duplicates(inplace=True)
        df_profesores.to_excel(self.profesores,index=False,sheet_name="base")
    
    def get_portafolio_name(self):
        df_profesores = pd.read_excel(self.profesores)
        self.driver.get("https://uchile.cl/portafolio-academico/")
        buscador = (By.XPATH, "//input[@placeholder='Buscar...' and @type='text']")
        self.wait_10.until(EC.visibility_of_element_located(buscador))
        btn_buscar = (By.XPATH,'//button[.//strong[text()="BUSCAR"]]')
        academic_card = (By.XPATH,"//div[contains(@class, 'AcademicCard_nombre__MQcFY')]//label[contains(@class, 'Celeste Pointer')]")
        for nombre_ucampus in df_profesores["Nombre ucampus"].to_list():
            self.driver.find_element(*buscador).send_keys(nombre_ucampus)
            self.driver.find_element(*btn_buscar).click()

            try:
                self.wait_5.until(EC.visibility_of_element_located(academic_card))
                cards = self.driver.find_elements(*academic_card)
                if len(cards) == 1:
                    enlace_elemento = self.driver.find_element(By.XPATH, '//div[@class="AcademicCard_nombre__MQcFY"]/a')
                    href = enlace_elemento.get_attribute('href')
                    nombre = cards[0].text.split(", ")[1] +" "+ cards[0].text.split(", ")[0]
                    df_profesores.loc[df_profesores["Nombre ucampus"] == nombre_ucampus, "Nombre portafolio"] = nombre
                    df_profesores.loc[df_profesores["Nombre ucampus"] == nombre_ucampus, "URL portafolio"] = href
                    df_profesores.loc[df_profesores["Nombre ucampus"] == nombre_ucampus, "Pagina encontrada"] = "TRUE"
                    print(f"Profe encontrado: {href}")

                    
            except:
                df_profesores.loc[df_profesores["Nombre ucampus"] == nombre_ucampus, "Pagina encontrada"] = "FALSE"
                print("No se encontró resultado")

            self.driver.find_element(*buscador).clear()
        df_profesores.to_excel(self.profesores, index=False, sheet_name="base", engine='openpyxl')  
        df_profesores.drop_duplicates(inplace=True)
            #lista = self.driver.find_elements(*sugerencias)
            #print(lista)
    def scrape_portafolio(self):
        df_profesores = pd.read_excel(self.profesores)
        for index, row in df_profesores.iterrows():
            url = row['URL portafolio']
            nombre_ucampus = row['Nombre ucampus']
            if isinstance(url, str) and url:
                self.driver.get(url=url)
                descripcion = (By.XPATH,'//div[@class="AcademicProfile_nombramientoContPri__lU4f_"]')
                self.wait_10.until(EC.visibility_of_element_located(descripcion))
                texto_descripcion = self.driver.find_element(*descripcion).text
                logging.info(f"Scraping {nombre_ucampus} data")
                jornada_pattern = r"Jornada.*?(\d+)"
                jerarquia_pattern = r"Prof.*?([aA-zZ]+)"
                try:
                    jornada = re.search(jornada_pattern, texto_descripcion).group(1)  
                except:
                    jornada = self.driver.find_element(By.XPATH,'//div[@class="AcademicProfile_nombramientoContPri__lU4f_"]//div[@class="AcademicProfile_nombramientoDetail__sTZwO"][last()]')
                try:
                    jerarquia = re.search(jerarquia_pattern, texto_descripcion).group(1) 
                except:
                    jerarquia = self.driver.find_element(By.XPATH,'//div[@class="AcademicProfile_nombramientoContPri__lU4f_"]//div[@class="AcademicProfile_nombramientoDetail__sTZwO"][1]')

                df_profesores.loc[df_profesores["Nombre ucampus"] == nombre_ucampus, "Jornada"] = jerarquia
                df_profesores.loc[df_profesores["Nombre ucampus"] == nombre_ucampus, "Jerarquia"] = jornada
                logging.info(jornada)
                logging.info(jerarquia)
               
            else:
                logging.info(f"No existe url para {row['Nombre ucampus']}")
        df_profesores.to_excel(self.profesores, index=False, sheet_name="base", engine='openpyxl')  
        df_profesores.drop_duplicates(inplace=True)


        
    
    def run_workflow(self):
        logging.info(f"************ Inicio del workflow {self.__class__.__name__} ************")
        try:
            #self.log_in()
            logging.info("starting navigate_catalogo_cursos")
            #self.navigate_catalogo_cursos()
            logging.info("starting get_portafolio_names")
            #self.get_portafolio_name()
            logging.info("starting scrape_portafolio")
            self.scrape_portafolio()
            
        except Exception as e:
            logging.error(f"Error inesperado en {self.__class__.__name__}: {str(e)}", exc_info=True)
        finally:
            self.close()
            logging.info(f"************ Termino del workflow {self.__class__.__name__} ************")




if __name__ == "__main__":
    url = "https://ucampus.uchile.cl"
    proceso = GetAllProfessors(url=url)
    proceso.run_workflow()