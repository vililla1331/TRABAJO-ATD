import json
import requests
import time
from collections import defaultdict
from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.parse import quote
import socket

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

def obtener_nota(lista_titulos):
    driver = uc.Chrome(options=uc.ChromeOptions(), version_main=144)#para que no de error si se vuelve a actualizar Chrome
    dic_nota = {}
    dic_actores = defaultdict(list)
    url = 'https://www.filmaffinity.com/es/main.html'
    
    for titulo in lista_titulos:
        try:
            driver.get(url)
            time.sleep(2)
            
            # Gestión de Cookies
            try: driver.find_element(By.ID, 'accept-btn').click()
            except: pass 
            
            # Buscador
            try: buscador = driver.find_element(By.ID, 'top-search-input-2')
            except: buscador = driver.find_element(By.ID, 'top-search-input')
            
            buscador.clear()
            buscador.send_keys(titulo)
            buscador.submit()
            time.sleep(4) 
         
            try:
                dic_nota[titulo] = driver.find_element(By.ID, "movie-rat-avg").get_attribute("content")
                elementos_actores = driver.find_elements(By.CSS_SELECTOR, "div.name[itemprop='name']")
                dic_actores[titulo] = [i.text for i in elementos_actores[:3]]
                
            except:
                
                try:
                    resultados = driver.find_elements(By.CSS_SELECTOR, "div.mc-title a")
                    encontrado = False
                    for res in resultados:
                        if titulo.lower() in res.text.lower():
                            driver.execute_script("arguments[0].click();", res)
                            encontrado = True
                            break 
                    if encontrado:
                        time.sleep(3)
                        dic_nota[titulo] = driver.find_element(By.ID, "movie-rat-avg").get_attribute("content")
                        
                        elementos_actores = driver.find_elements(By.CSS_SELECTOR, "div.name[itemprop='name']")
                        dic_actores[titulo] = [i.text for i in elementos_actores[:3]]
                    else:
                         dic_nota[titulo] = "No encontrado en lista"

                except Exception as e:
                    
                    print(f"Error buscando enlace para {titulo}: {e}")
                    dic_nota[titulo] = "No encontrado"
                    
        except Exception as e:
            print(f"Error general con {titulo}: {e}")
            dic_nota[titulo] = "Error"
            
    try: driver.quit()
    except: pass
    return dic_nota, dic_actores

def buscar_plataformas(lista_titulos):
    driver = uc.Chrome(version_main=144)
    dic_resultados = {}
    url = 'https://www.justwatch.com/es'
    
    print("Iniciando búsqueda en JustWatch...")

    for titulo in lista_titulos:
        try:
            driver.get(url)
            time.sleep(2)
            
            try:
                for btn in driver.find_elements(By.TAG_NAME, "button"):
                    if "Accept" in btn.text or "Aceptar" in btn.text:
                        btn.click(); break
            except: pass 

            try: buscador = driver.find_element(By.CSS_SELECTOR, 'input[name="q"]')
            except: buscador = driver.find_element(By.ID, 'searchbar-input')
            
            buscador.clear(); buscador.send_keys(titulo); buscador.submit()
            print(f"Buscando plataformas para: {titulo}")
            time.sleep(3)
            
            elementos = driver.find_elements(By.CLASS_NAME, "header-title")
            if elementos:
                driver.execute_script("arguments[0].click();", elementos[0])
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, 250);")
                time.sleep(3)
                filas = driver.find_elements(By.CLASS_NAME, "buybox-row")
                plataformas = []
                encontrado = False

                for fila in filas:
                    txt = fila.text.lower()
                    if "stream" in txt or "fijo" in txt or "suscripción" in txt:
                        for img in fila.find_elements(By.TAG_NAME, "img"):
                            nombre = img.get_attribute("alt")
                            if nombre and nombre not in plataformas:
                                plataformas.append(nombre)
                        encontrado = True
                        break 
                
                if encontrado and plataformas:
                    dic_resultados[titulo] = plataformas
                else:
                    dic_resultados[titulo] = 'No esta disponible'
                    print(f" -> No disponible en streaming")
            else:
                dic_resultados[titulo] = 'No esta disponible'

        except:
            dic_resultados[titulo] = "Error"
    
    driver.quit()
    return dic_resultados
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
            api = "https://es.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": titulo,
                "srlimit": 1,
                "format": "json"
            }
            r = requests.get(api, params=params, headers=HEADERS, timeout=15)
            data = r.json()
            resultados = data.get("query", {}).get("search", [])
            titulo_real = resultados[0]["title"] if resultados else None
            sinopsis = "Sinopsis no encontrada"
            if titulo_real:
                r2 = requests.get(
                    f"https://es.wikipedia.org/wiki/{quote(titulo_real)}",
                    headers=HEADERS, timeout=15
                )
                soup2 = BeautifulSoup(r2.text, "html.parser")
                h = soup2.find(
                    lambda tag: tag.name in ["h2", "h3"]
                    and any(x in tag.get_text() for x in ["Argumento", "Trama", "Sinopsis", "Resumen", "Historia"])
                )
                if not h:
                    h = soup2.find(
                        lambda tag: tag.name in ["h2", "h3"]
                        and "Plot" in tag.get_text()
                    )
                if h:
                    p = h.find_next("p")
                    if p and len(p.get_text(strip=True)) > 80:
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

def filtrado(mis_pelis, notas, sinopsis):
    validacion = {}
    for titulo in mis_pelis:
        errores = []
        nota = notas.get(titulo)
        try:
            float(nota)
        except:
            errores.append("nota_no_valida")
        sinop = sinopsis.get(titulo, "")
        if not sinop or sinop == "Sinopsis no encontrada":
            errores.append("sinopsis_no_valida")
        validacion[titulo] = {
            "valida": len(errores) == 0,
            "errores": errores
        }
    return validacion

#USO DE SERVIDOR SOCKET
def ejecutar_servidor():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 5001))
    server_socket.listen(1)
    print("Servidor listo y escuchando en el puerto 5000. Esperando para recibir un género.")

    while True:
        conn, addr = server_socket.accept()
        print(f"Conexión recibida de: {addr}")
        
        try:
            genero = conn.recv(1024).decode('utf-8')
            if not genero: continue
            print(f"Procesando género: {genero}")

            mis_pelis = obtener_titulos_imdb(genero)
            notas, actores = obtener_nota(mis_pelis)
            plataformas = buscar_plataformas(mis_pelis)
            sinopsis, pelis_por_actor = sinopsis_recom(actores)
            
            datos_filtrados=filtrado(mis_pelis, notas, sinopsis)

            resultados = {
                "peliculas": mis_pelis,
                "notas": notas,
                "actores": actores,
                "plataformas": plataformas,
                "sinopsis": sinopsis,
                "recomendaciones_por_actor": pelis_por_actor,
                "datos filtrados": datos_filtrados
            }

            respuesta = json.dumps(resultados, ensure_ascii=False)
            conn.sendall(respuesta.encode('utf-8'))
            
        except Exception as e:
            print(f"Error en el servidor: {e}")
            # ENVIAR ERROR AL CLIENTE EN LUGAR DE CERRAR EN SILENCIO
            error_msg = json.dumps({"error": str(e)}, ensure_ascii=False)
            conn.sendall(error_msg.encode('utf-8'))
        finally:
            conn.close()

if __name__ == "__main__":
    ejecutar_servidor()
