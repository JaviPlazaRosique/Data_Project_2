# Creación de la imagen de la API en Artifact Registry.

Para poder crear la imagen de la API, debes de estar en el directorio `Data_Project_2/api/`. Una vez estando en el directorio, se debe de ejecutar el siguiente comando en la terminal:

````sh
gcloud builds submit \
    --tag <Region en la que estes trabajando>-docker.pkg.dev/<ID del proyecto>/<Repositorio de Artifact>/<Nombre de la imagen>:latest .
````