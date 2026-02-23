# Levantar contenedores únicos.

Para levantar uno de los contenedores del `compose.yaml`, se debe de ejecutar el siguiente comando:

````sh
docker compose up <nombre del contenedor>
````

En el `compose.yaml` se encuentran los siguientes contenedores:

- **personas**: Este contenedor contiene la generación tanto de menores, como de los tutores legales que se encuentran a su cargo. (Recomendación: Ejecutarlo solo una vez)
- **ubicaciones**: Este contenedor contiene la generación de la ubicación de cada menor en tiempo real.
- **zonas_restringidas**: Este contenedor contiene la generación de las zonas que cada menor tiene restringidas. (Recomendación: Ejecutarlo solo una vez) 