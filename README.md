# SafeChild: Sistema de Monitoreo Infantil en Tiempo Real 📍

## Descripción del Proyecto

Este proyecto implementa una solución de streaming de datos para la seguridad infantil. Utiliza sensores de ubicación para detectar si un menor entra en zonas restringidas por sus padres, los notifica y guarda un histórico en la nube. Los datos se transmiten en tiempo real, y se almacenan en una base de datos SQL, asi como tambien en BigQuery para un análisis posterior.

El sistema también incluye una app para que los padres puedan monitorear la ubicación de sus hijos y recibir alertas instantáneas. De esta manera, se busca proporcionar una herramienta efectiva para la protección de los menores, permitiendo a los padres estar tranquilos sabiendo que pueden actuar rápidamente en caso de cualquier situación de riesgo. Otras características que incluye es la capacidad de configurar zonas seguras y restringidas, así como la integración con servicios de mensajería para enviar alertas a los padres. Este proyecto es una demostración de cómo la tecnología puede ser utilizada para mejorar la seguridad y el bienestar de los niños en un mundo cada vez más conectado.

Por otra parte, se almacenan los datos en la nube utilizando una base de datos NoSQL, lo que permite una gestión eficiente de grandes volúmenes de información y una rápida recuperación de datos. Esto es crucial para el sistema, ya que se generan múltiples eventos y alertas en tiempo real. Estos resumenes de los eventos ocurridos se muestran en un dashboard para que los padres puedan revisar el historial de ubicaciones y alertas de sus hijos.

El almacenamiento de datos en la nube permite un acceso fácil y seguro a la información, garantizando que los padres puedan revisar el historial de ubicaciones y alertas en cualquier momento. Además, el sistema está diseñado para ser escalable, permitiendo la incorporación de más usuarios o funcionalidades en el futuro sin comprometer el rendimiento. 

## Arquitectura

![Diagrama de Arquitectura](.img/arquitectura.png)

## Simulación de Datos (Generadores Synthetic)

Para validar la robustez del sistema en tiempo real, hemos desarrollado una suite de **Generadores de Datos Sintéticos**. Estos scripts simulan el comportamiento de los dispositivos GPS y la actividad de la base de datos sin necesidad de hardware físico.

### 1. Generadores de Entidades Estáticas

* **Generador de Adultos**: Crea perfiles de tutores con nombres, teléfonos y correos electrónicos realistas utilizando la librería `Faker`.
* **Generador de Menores**: Crea los perfiles infantiles y los vincula aleatoriamente a los adultos existentes, asignándoles metadatos como DNI y necesidad de asistencia especial.

### 2. Generador de Zonas (Geofencing)

Este script automatiza la creación de áreas de seguridad en Cloud SQL. Define un punto central (lat/lon) y establece dos radios concéntricos:

* **Radio de Advertencia**: Alerta preventiva.
* **Radio de Peligro**: Alerta crítica.

### 3. Generador de Ubicaciones GPS (Streaming)

Es el motor principal de telemetría. Simula el movimiento de un menor enviando mensajes JSON a **GCP Pub/Sub** cada pocos segundos:

* **Latencia simulada**: Emula la frecuencia de actualización de un dispositivo real.
* **Inyección de Peligro**: Programado para generar trayectorias que crucen intencionadamente las zonas restringidas para validar la respuesta del pipeline.

## API de Gestión (FastAPI)

El sistema dispone de una API REST robusta construida con **FastAPI**, que actúa como capa de orquestación entre los generadores, la base de datos y los servicios de almacenamiento de Google Cloud.

### Características principales:

* **Validación de Datos**: Uso de `Pydantic` para garantizar la integridad de los esquemas.
* **Inyección de Dependencias**: Gestión eficiente de conexiones a la base de datos.
* **Escalabilidad**: Diseño asíncrono para manejar múltiples peticiones simultáneas.

### Seguridad de la API

Para proteger los endpoints de accesos no autorizados, se ha implementado un sistema de **API Key Header**:

* **Middleware de Seguridad**: Todas las peticiones deben incluir una cabecera `X-API-Key`.
* **Validación**: La API verifica la clave contra una variable de entorno segura antes de procesar cualquier operación, devolviendo un error `403 Forbidden` si la clave es incorrecta.

### Endpoints Principales

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `POST` | `/menores` | Registra un nuevo menor en el sistema. |
| `POST` | `/fotos_menores` | Sube la imagen del menor a un Bucket de GCS. |
| `POST` | `/ubicaciones` | Publica telemetría GPS directamente en **Pub/Sub**. |
| `POST` | `/zonas_restringidas` | Configura geocercas para el monitoreo. |
| `GET` | `/menores/id_direccion` | Obtiene datos básicos para la simulación. |

### Integración Cloud Nativa

La API no solo guarda datos en SQL, sino que dispara eventos en la nube:

* **Google Cloud Storage**: El endpoint `/fotos_menores` procesa archivos binarios y los almacena en un bucket, devolviendo la URL pública del objeto.
* **Google Cloud Pub/Sub**: El endpoint `/ubicaciones` serializa los datos en JSON y los publica en el tópico correspondiente, activando el flujo de streaming en Dataflow de forma inmediata.

### Inicialización Automática

La API está configurada para preparar el entorno en el arranque:

* **Evento `startup`**: Al iniciar el servidor, la API verifica la existencia de las tablas (`adultos`, `menores`, `zonas`, `historico`) y las crea si es necesario.
* **Extensiones SQL**: Activa automáticamente la extensión `uuid-ossp` en PostgreSQL para el manejo de identificadores únicos universales.
  
## Modelo de Datos Relacional (PostgreSQL)

La persistencia de la configuración y el estado maestro del sistema se gestiona en **Cloud SQL**. Se ha diseñado un esquema relacional que garantiza la integridad de los datos y facilita el enriquecimiento de los mensajes en el pipeline.

![Diagrama de Base de Datos](.img/relacion_tablas.png)

### 1. Gestión de Usuarios (Tabla `adultos`)

Representa a los tutores legales en el sistema. Es la entidad raíz para la gestión de permisos en la aplicación.

* **Campos clave**: `id` (PK), `telefono`, `email` y `nombre`.
  
### 2. Entidad Menores (Tabla `menores`)

Contiene los perfiles de los niños protegidos. 

* **Relación**: Posee una clave foránea (`id_adulto`) que vincula a cada menor con su tutor responsable.
* **Multimedia**: Almacena la `url_foto` que referencia a los archivos en **GCS**.

### 3. Zonas Restringidas (Tabla `zonas_restringidas`)

Define los parámetros espaciales para el motor de reglas de Dataflow.

* **Atributos**: `id_menor`, `latitud`, `longitud`, `radio_peligro` (m) y `radio_advertencia` (m).
* **Uso**: El pipeline realiza un JOIN dinámico con esta tabla para evaluar la seguridad de cada coordenada recibida.

### 4. Histórico de Notificaciones (Tabla `historico_notificaciones`)

Almacena el resultado de cada procesamiento crítico realizado por el pipeline.

* **Campos**: `id_menor`, `nombre_menor`, `estado` y `fecha`.
* **Propósito**: Alimentar la vista de "Alertas" de la aplicación web de forma rápida.

## Replicación de Datos (Change Data Capture)

Para mantener el Data Warehouse actualizado sin penalizar el rendimiento de la base de datos transaccional, se implementó **Google Cloud Datastream**. Este servicio realiza una captura de datos modificados (CDC) en tiempo real, replicando automáticamente las tablas de Cloud SQL (PostgreSQL) hacia **BigQuery**. Esto permite que el Dashboard analítico consulte el histórico de forma eficiente y desacoplada de la operativa principal.
  
## Tecnologías utilizadas

* **Google Cloud Platform (GCP)**: Hosting de toda la infraestructura.

* **Terraform**: Infraestructura como código.
  
* **Apache Beam & Dataflow**: Procesamiento de datos en streaming.
  
* **Pub/Sub**: Ingesta de mensajes de ubicación.
  
* **Cloud SQL (PostgreSQL)**: Gestión de zonas y usuarios.
  
* **BigQuery**: Data Warehouse para análisis histórico.
  
* **Firestore**: Alertas en tiempo real.

* **Streamlit**: Despliegue de la App

* **Plotly**: Genera el Dashboard

## Prerrequisitos

* Python 3.9 o superior.
  
* Google Cloud SDK instalado y configurado.
  
* Una cuenta de servicio en GCP con permisos de Editor.
  
* Docker Desktop (para ejecución de contenedores locales).

## Despliegue de la Infraestructura

Este proyecto utiliza **Terraform** para gestionar la infraestructura como código (IaC), permitiendo que todo el entorno de Google Cloud se despliegue de forma automática y consistente.

### Pasos para el despliegue inicial:

1. **Inicializar el entorno**: Prepara los proveedores y el backend.
   ```bash
   terraform init
   ```

2. **Planificar el despliegue**: Revisa los cambios que se aplicarán a la infraestructura.
   ```bash
   terraform plan
   ```

3. **Ejecutar el despliegue**: Aplica los cambios para crear los recursos en Google Cloud.
   ```bash
   terraform apply
   ```

## Procesamiento de Datos (Dataflow Pipeline)

El pipeline de procesamiento está desarrollado en **Apache Beam** y se ejecuta de forma escalable en **Google Cloud Dataflow**. Su función principal es el enriquecimiento de datos en tiempo real.

### Lógica de Procesamiento:

1. **Ingesta y Windowing**: Consumo de eventos desde Pub/Sub en streaming aplicando ventanas de tiempo fijas (*Fixed Windows* de 10 segundos). Esto permite deduplicar señales GPS ruidosas y conservar únicamente la lectura más reciente por menor (`Latest.PerKey()`), optimizando el procesamiento.
2. **Enriquecimiento Optimizado (Caché local)**: Las zonas restringidas se extraen de Cloud SQL y se mantienen en memoria del *worker*, refrescándose cada 5 minutos. Esto minimiza la latencia y evita la saturación de la base de datos por consultas continuas.
3. **Cálculo Geoespacial**: Uso de la librería `geopy` para determinar la distancia geodésica exacta entre la posición del menor y los radios de las zonas.
4. **Ramificación y Micro-batching**: El flujo de datos se divide para alimentar distintos sumideros simultáneamente:
   * **BigQuery**: Inserción en streaming para el registro histórico y analítico.
   * **Firestore**: Coleccion de ubicaciones, con el punto en el que se encuentra el menor, reflejandose actualizado en el mapa de la app y colección de notificacion en donde se hace actualización del estado para reflejar alertas de peligro y advertencia inmediatas en la App de los padres.
   * **PostgreSQL**: Inserción del estado de peligro y advertencia, evitando el estado OK. 

## Clasificación de Estados

El motor de reglas evalúa la distancia geodésica y clasifica el evento según la configuración de la base de datos:

| Estado | Acción del Sistema |
| :--- | :--- |
| **OK** | Registro silencioso en BigQuery. |
| **ADVERTENCIA** | Notificación preventiva en la App. |
| **PELIGRO** | Alerta crítica y guardado en histórico de seguridad. |

## Interfaz de Monitoreo (Streamlit App)

La plataforma incluye una aplicación web desarrollada con **Streamlit**, diseñada para que los padres y tutores puedan interactuar con el sistema de seguridad de forma intuitiva. 

La aplicación se conecta directamente a **Cloud SQL** mediante el conector de Google Cloud y recupera archivos multimedia desde **Google Cloud Storage**.

### Control de Acceso y Registro

La seguridad de la App incluye:

* **Sistema de Login/Registro**: Validación de credenciales contra la tabla de `adultos` en PostgreSQL.
* **Sesiones Seguras**: Uso de `st.session_state` para mantener la persistencia del usuario y limitar los intentos de acceso fallidos (máximo 3 intentos).
* **Gestión de Perfiles**: Los padres pueden registrarse y acceder únicamente a la información de los menores vinculados a su ID de usuario.

### Gestión de Menores y Multimedia

Una vez iniciada la sesión, la app permite:

* **Exploración de Perfiles**: Visualización de tarjetas personalizadas para cada hijo.
* **Integración con GCS**: Las fotografías de los menores se recuperan dinámicamente desde un **Bucket de Google Cloud Storage** mediante el cliente oficial de Python.
* **Fichas de Datos**: Visualización de información sensible (DNI, fecha de nacimiento, dirección, discapacidad) recuperada de forma segura desde Cloud SQL.

### Visualización Geoespacial (Mapas)

El corazón de la aplicación es su mapa interactivo, construido con la librería **Folium**:

* **Capas Personalizables**: El usuario puede alternar entre vista de Callejero (OpenStreetMap), Satélite (Esri World Imagery) y Modo Oscuro (CartoDB).
* **Representación de Zonas**: Las zonas restringidas se dibujan dinámicamente sobre el mapa:
    * 🟡 **Círculos Amarillos**: Radios de advertencia.
    * 🔴 **Círculos Rojos**: Radios de peligro inminente.
* **Centrado Inteligente**: El mapa se geolocaliza automáticamente en la ciudad de residencia del menor.

### Configuración Técnica de la App

La aplicación utiliza variables de entorno para una configuración segura y flexible:

* `PROYECTO_REGION_INSTANCIA`: Conexión al socket de Cloud SQL.
* `USUARIO_DB` / `CONTR_DB`: Credenciales de acceso a PostgreSQL.
* `BUCKET_FOTOS`: Nombre del bucket de GCS para los activos multimedia.
* **IP Privada**: El conector utiliza `IPTypes.PRIVATE` para garantizar que el tráfico de datos no salga a la internet pública.

## Seguridad y Privacidad

* **IAM**: Uso de Cuentas de Servicio con el principio de mínimo privilegio.

* **Redes**: Conexión entre App y DB mediante IP Privada y VPC Peering para evitar exposición a internet.

Integrantes:
   * Celia Sarrió
   * Gemma Balaguer
   * Javier Plaza
   * Marina López
