import requests
import time
from collections import defaultdict
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By

# PAGINA 1: IMDB: BUSCAR PELÍCULAS POR GÉNERO
VALID_GENRES = ["action", "adventure", "animation", "biography", "comedy", "crime", "documentary", "drama", "family", "fantasy", "film-noir", "history", "horror", "music", "musical", "mystery", "romance", "sci-fi", "short", "sport", "thriller", "war", "western"]
def obtener_titulos_imdb(genero, cantidad=5):
    driver = webdriver.Chrome()
    lista_limpia = []
    try:
        driver.get(f"https://www.imdb.com/search/title/?genres={genero}&sort=moviemeter,asc")
        time.sleep(3)
        elementos = driver.find_elements(By.CLASS_NAME, "ipc-title__text")
        for elem in elementos:
            if ". " in elem.text: # si forma parte de una trilogia o saga
                try:
                    lista_limpia.append(elem.text.split('. ', 1)[1])
                except: continue
            if len(lista_limpia) == cantidad: break
    except: pass
    finally: driver.quit()
    return lista_limpia


#PAGINA 2: FILMAFFINITY: buscar la nota de cada pelicula

def obtener_nota(lista_titulos):
    driver = uc.Chrome(options=uc.ChromeOptions()) # para solucionar lo verificación humana
    dic_nota = {}
    dic_actores = defaultdict(list)
    url = 'https://www.filmaffinity.com/es/main.html'
    
    for titulo in lista_titulos:
        try:
            driver.get(url)
            time.sleep(2)
            try:
                driver.find_element(By.ID, 'accept-btn').click()
            except: pass # porque a la segunda vez no sale
            
            try: buscador = driver.find_element(By.ID, 'top-search-input-2')
            except: buscador = driver.find_element(By.ID, 'top-search-input')
            
            buscador.clear()
            buscador.send_keys(titulo)
            buscador.submit()
            time.sleep(3)
            
            try:
                dic_nota[titulo] = driver.find_element(By.ID, "movie-rat-avg").get_attribute("content")
                elementos_actores = driver.find_elements(By.CSS_SELECTOR, "div.name[itemprop='name']")
                if len(elementos_actores) != 0:
                    for i in elementos_actores[:3]:
                        dic_actores[titulo].append(i.text)
            except:
                try:
                    link = driver.find_element(By.XPATH, f"//a[contains(text(), '{titulo}')]")
                    driver.execute_script("arguments[0].click();", link)
                    time.sleep(3)
                    dic_nota[titulo] = driver.find_element(By.ID, "movie-rat-avg").get_attribute("content")
                    elementos_actores = driver.find_elements(By.CSS_SELECTOR, "div.name[itemprop='name']")
                    if len(elementos_actores) != 0:
                        for i in elementos_actores[:3]:
                            dic_actores[titulo].append(i.text)
                except:
                    dic_nota[titulo] = "No encontrado"
        except:
            dic_nota[titulo] = "Error"
            
    try: driver.quit()
    except: pass
    return dic_nota,dic_actores
    
#PAGINA 3: JUSTWACH: buscar las plataformas de cada película
def buscar_plataformas(dic_nota):
    driver = webdriver.Chrome()
    dic_resultados = {}
    print(f"Iniciando una búsqueda para {len(dic_nota)} películas en JustWatch...")
    #Aceptar las cookies si aparecen
    driver.get("https://www.justwatch.com/es")
    time.sleep(3)
    try:
        botones = driver.find_elements(By.TAG_NAME, "button")
        for boton in botones:
            if "Aceptar" in boton.text or "Accept" in boton.text:
                boton.click()
                print("Cookies aceptadas.")
                break
    except:
        print("No se pudieron aceptar las cookies o no aparecieron.")
    #Búsqueda de plataforma para cada película
    for pelicula in dic_nota.keys():
        print(f"Buscando: {pelicula}...")
        url_busqueda = f"https://www.justwatch.com/es/buscar?q={pelicula.replace(' ', '%20')}"
        driver.get(url_busqueda)
        time.sleep(3)
        try:
            #Buscamos el primer elemento de la rejilla de resultados al buscar la pelicula que contiene "title-list-grid__item"
            primer_resultado = driver.find_element(By.CSS_SELECTOR, "div.title-list-grid__item a")
            primer_resultado.click()

            time.sleep(3)
            
            #Las plataformas están dentro de una caja llamada "buybox-row__offers" como imágenes
            imagenes_plataformas = driver.find_elements(By.CSS_SELECTOR, "div.buybox-row__offers img")
            plataformas= []
            for imagen in imagenes_plataformas:
                nombre_plataforma = imagen.get_attribute("alt")
                if nombre_plataforma not in plataformas:
                    plataformas.append(nombre_plataforma)
            #Guardamos en el diccionario el resultado:
            dic_resultados[pelicula] = plataformas
            print(f"Película encontrada en: {plataformas}")
        except Exception as e:
            # Si falla (no hay plataformas encontradas), guardamos una lista vacía
            print(f"No se encontraron plataformas para la película o hubo un error: {e}")
            dic_resultados[pelicula] = ["No disponible, error"]
            continue

    driver.quit()
    
    return dic_resultados
