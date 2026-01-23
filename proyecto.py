import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

# PATGINA 1: IMDB: BUSCAR PELÍCULAS POR GÉNERO

def obtener_titulos_imdb(genero, cantidad=10):
    driver = webdriver.Chrome()
    lista_limpia = []
    try:
        url = f"https://www.imdb.com/search/title/?genres={genero}&sort=moviemeter,asc"
        driver.get(url)
        time.sleep(3) # para que de tiempo a cargar la página
        # Buscamos todos los títulos por su clase
        elementos = driver.find_elements(By.CLASS_NAME, "ipc-title__text")
        for elem in elementos:
            texto = elem.text
            # si la peli es parte de una trilogia o saga
            if ". " in texto:
                #limpiamos el numero inicial
                titulo = texto.split('. ', 1)[1]
                lista_limpia.append(titulo)
            
            if len(lista_limpia) == cantidad:
                break     
        driver.quit()
    except Exception as e:
        print(f"Error: {e}")
        driver.quit()
        
    return lista_limpia
generos= [
    "action",
    "adventure",
    "animation",
    "biography",
    "comedy",
    "crime",
    "documentary",
    "drama",
    "family",
    "fantasy",
    "film-noir",
    "history",
    "horror",
    "music",
    "musical",
    "mystery",
    "romance",
    "sci-fi",
    "short",
    "sport",
    "thriller",
    "war",
    "western"
]

#PAGINA 2: FILMAFFINITY: buscar la nota de cada pelicula
