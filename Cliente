import socket
import json

def consultar_peliculas():
    genero = input("Introduce género: ").strip().lower()
    
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect(('localhost', 5000))
    cliente.send(genero.encode('utf-8'))
    
    data = b""
    while True:
        chunk = cliente.recv(4096)
        if not chunk: break
        data += chunk
    
    resultados = json.loads(data.decode('utf-8'))
    print(json.dumps(resultados, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    consultar_peliculas()
