import json 
import uuid
import random
import requests
from faker import Faker
from datetime import datetime

# Cambia esta URL la api
API_URL = "http://localhost:8000/api/v1/ninos"

Cantidad=5 # Es escalable, es para que no le gaste dinero a Javi. 
ARCHIVO_TEMP = "memoria_ninos.json" 

def generar():
    lista_ninos=[]
    print(f"Generando {Cantidad} perfiles de niños...")

    for _ in range (Cantidad):
        #generamos los IDs vinculados
        id_nino=str(uuid.uuid4())
        id_padres=str(uuid.uuid4())

        #Estructura para la tabla 
        nino={
            "id": id_nino,
            "nombre": fake.first_name(),
            "apellido": fake.last_name() + " " + fake.last_name(),
            "nombre_familia":f"Familia {fake.last_name()}",
            "DNI":fake.unique.bothify(text='########?'), #generamos un DNI único
            "id_adulto": id_padres,
            "fecha_nacimiento": fake.date_of_birth(minimum_age=5, maximum_age=17).strftime("%Y-%m-%d"),
            "domicilio": fake.address().replace("\n", ", "),
            "grado_discapacidad": random.choice(["33%", "55%", "66%", "100%", "Ninguno"]),
            "url_foto":f"https://storage.cloud.google.com/bucket-fotos-menores/{id_nino}.jpg"
        }

        print(f"Creando perfil para {nino['nombre']} {nino['apellido']} con ID: {id_nino}" )

        lista_ninos.append(nino)
#Conexión a la API intentamos enviar a la API
        try:
            #Enviamos el post a la API
            response = requests.post(API_URL, json=nino)
            if response.status_code == 201 or response.status_code == 200:
                print(f"Perfil creado exitosamente para {nino['nombre']} {nino['apellido']}")
            else:
                print(f"Error al crear perfil para {nino['nombre']} {nino['apellido']}: {response.status_code}")
        except Exception as e:
            print(f"Error de conexión,guardamos en local: {e}")
    #Guardamos e archivo para los otros scripts
    with open(ARCHIVO_TEMP, 'w', encoding='utf-8') as f:
        json.dump(lista_ninos, f, indent=4, ensure_ascii=False)
    
    print(f"Datos guardados en {ARCHIVO_TEMP}")


if __name__ == "__main__":
    generar()  
