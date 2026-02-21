# Data Project 2 - Monitoreo de Menores

## Descripción del Proyecto

Este proyecto tiene como objetivo desarrollar un sistema de monitoreo para menores utilizando tecnologías de Google Cloud Platform (GCP). El sistema permitirá a los padres y tutores supervisar la actividad en línea de los menores, detectar comportamientos sospechosos y proporcionar alertas en tiempo real. 

Se implementará utilizando una arquitectura basada en microservicios, con componentes que se encargan de la recopilación de datos, el procesamiento de información y la generación de alertas. Se utilizarán servicios de GCP como Cloud Pub/Sub para la ingesta de datos, Cloud Functions para el procesamiento en tiempo real, y BigQuery para el almacenamiento y análisis de datos. Además, se implementará una interfaz de usuario para que los padres puedan visualizar la información recopilada y configurar las alertas según sus preferencias. 

Se desarrollará siguiendo las mejores prácticas de seguridad y privacidad, asegurando que los datos de los menores estén protegidos en todo momento. Se realizarán pruebas exhaustivas para garantizar la funcionalidad y la fiabilidad del sistema antes de su implementación final. Este proyecto tiene el potencial de proporcionar a los padres una herramienta valiosa para proteger a sus hijos en el entorno digital, promoviendo un uso seguro y responsable de la tecnología.

## Estructura del Proyecto

El proyecto se organiza en las siguientes carpetas y archivos:

- 'Generadores/': Contiene scripts para generar los datos y simular la actividad en línea de los menores, incluyendo la generación de datos sobre las ubicaciones, las zonas restringidas y los datos personales de los menores y sus tutores legales.
- 'api/': Contiene el código para la API que se encargará de recibir los datos generados por los contenedores y procesarlos para su almacenamiento y análisis.