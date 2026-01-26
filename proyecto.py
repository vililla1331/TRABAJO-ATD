import requests
import time
from collections import defaultdict
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.parse import quote

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
            if ". " in elem.text:
                try:
                    lista_limpia.append(elem.text.split('. ', 1)[1])
                except: continue
            if len(lista_limpia) == cantidad: break
    except: pass
    finally: driver.quit()
    return lista_limpia


#PAGINA 2: FILMAFFINITY: buscar la nota de cada pelicula

def obtener_nota(lista_titulos):
    driver = uc.Chrome(options=uc.ChromeOptions())
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
    
#PAGINA 3: JUSTWATCH: buscar las plataformas de cada película
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
    
#PAGINA 4: WIKIPEDIA: Sinopsis de la películay recomendación de 5 películas de los 3 principales actores

def sinopsis_recom(dic_actores, pausa=1.0):
    BASE = "https://es.wikipedia.org"
    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
    }
    dic_sinopsis = {}
    dic_pelis_por_actor = {}
    for titulo, actores in dic_actores.items():
        try:
            r = requests.get(
                f"{BASE}/w/index.php?search={quote(titulo)}",
                headers=HEADERS, timeout=15
            )
            soup = BeautifulSoup(r.text, "html.parser")
            sinopsis = "Sinopsis no encontrada"
            h = soup.find(
                lambda tag: tag.name in ["h2", "h3"]
                and any(x in tag.get_text() for x in ["Argumento", "Trama", "Sinopsis"])
            )
            if h:
                p = h.find_next("p")
                if p:
                    sinopsis = p.get_text(" ", strip=True)
            dic_sinopsis[titulo] = sinopsis
        except:
            dic_sinopsis[titulo] = "Sinopsis no encontrada"
        time.sleep(pausa)
        dic_pelis_por_actor[titulo] = {}
        for actor in actores[:3]:
            try:
                r = requests.get(
                    f"{BASE}/w/index.php?search={quote(actor)}",
                    headers=HEADERS, timeout=15
                )
                soup = BeautifulSoup(r.text, "html.parser")
                pelis = []
                # primero tablas
                for table in soup.select("table.wikitable"):
                    for tr in table.select("tr")[1:]:
                        tds = tr.find_all("td")
                        if len(tds) < 2:
                            continue
                        year = tds[0].get_text(strip=True)
                        if not (year.isdigit() and len(year) == 4):
                            continue
                        a = tds[1].select_one("a[href^='/wiki/']")
                        if not a:
                            continue
                        peli = f"{a.get_text(strip=True)} ({year})"
                        if peli not in pelis:
                            pelis.append(peli)
                        if len(pelis) == 5:
                            break
                    if len(pelis) == 5:
                        break
                # fallback por si falla
                if not pelis:
                    for li in soup.select("div#mw-content-text li"):
                        txt = li.get_text(" ", strip=True)
                        if "(" in txt and ")" in txt:
                            year = txt[txt.find("(")+1:txt.find(")")]
                            if year.isdigit() and len(year) == 4:
                                a = li.select_one("a[href^='/wiki/']")
                                if a:
                                    peli = f"{a.get_text(strip=True)} ({year})"
                                    if peli not in pelis:
                                        pelis.append(peli)
                        if len(pelis) == 5:
                            break
                dic_pelis_por_actor[titulo][actor] = pelis if pelis else ["No encontrado"]
            except:
                dic_pelis_por_actor[titulo][actor] = ["No encontrado"]
            time.sleep(pausa)
    return dic_sinopsis, dic_pelis_por_actor
