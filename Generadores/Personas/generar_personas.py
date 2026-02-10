from faker import Faker 
from datetime import datetime
from diffusers import StableDiffusionPipeline
import random
import uuid
import json
import os
import torch
import requests
import io

bucket_fotos = os.getenv("BUCKET_FOTOS")
url_api = os.getenv("URL_API")

device = "cuda" if torch.cuda.is_available() else "cpu"
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5", 
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
).to(device)

ciudades = ["Barcelona", "Valencia", "Madrid"]

fake = Faker('es_ES')

def foto_menor(id_menor, sexo_prompt):
    prompt = f"Professional portrait of a  {sexo_prompt}, realistic, 4k, soft lighting"
    
    imagen = pipe(prompt).images[0]

    img_buffer = io.BytesIO()

    imagen.save(img_buffer, format="PNG")

    img_buffer.seek(0)

    parametros = {"id_menor": id_menor}
    archivos = {"archivo": (f"{id_menor}.png", img_buffer, "image/png")}
    
    try:
        requests.post(f"{url_api}/fotos_menores", params = parametros, files = archivos)

        print(f"Foto generada y subida con exito")
    except Exception as e:
        print(f"Error subiendo foto: {e}")

def generar_adulto():
    sexo = random.choice(['m', 'f'])
    nombre = fake.first_name_male() if sexo == 'm' else fake.first_name_female()
    apellido_paterno = fake.last_name()
    apellido_materno = fake.last_name()

    return {
        "id": str(uuid.uuid4()),
        "nombre": nombre,
        "apellidos": f"{apellido_paterno} {apellido_materno}",
        "telefono": fake.phone_number(),
        "email": fake.email()
    }

def generar_menor(id_adulto, apellidos):
    sexo = random.choice(['masculino', 'femenino'])
    id_menor = str(uuid.uuid4())
    
    if sexo == 'masculino':
        nombre = fake.first_name_male()
        sexo_prompt = "boy"
    else:
        nombre = fake.first_name_female()
        sexo_prompt = "girl"

    menor = {
        "id": id_menor,
        "id_adulto": id_adulto,
        "nombre": nombre,
        "apellidos": apellidos,
        "dni": fake.nif(),
        "fecha_nacimiento": fake.date_of_birth(minimum_age=10, maximum_age=17).strftime("%Y-%m-%d"),
        "direccion": f"{random.choice(ciudades)}, Spain",
        "url_foto": f"https://storage.googleapis.com/{bucket_fotos}/{id_menor}.png",
        "discapacidad": random.choice([True, False])
    }
    
    return menor, sexo_prompt

if __name__ == "__main__":
    adultos = 3
    menores = 5
    lista_adultos = []

    for _ in range(adultos):
        adulto = generar_adulto()
        try:
            res = requests.post(f"{url_api}/adultos", json=adulto)
            if res.status_code == 201:
                lista_adultos.append(adulto)
                print(f"Adulto registrado: {adulto['nombre']} {adulto['apellidos']}")
        except Exception as e:
            print(f"Error: {e}")

    for _ in range(menores):
        tutor = random.choice(lista_adultos)
        
        datos_menor, sexo_prompt = generar_menor(tutor["id"], tutor["apellidos"])
        
        foto_menor(datos_menor["id"], sexo_prompt)
        
        try:
            res = requests.post(f"{url_api}/menores", json=datos_menor)
            if res.status_code == 201:
                print(f"Menor {datos_menor['nombre']} asignado a {tutor['nombre']}")
        except Exception as e:
            print(f"Error: {e}")


