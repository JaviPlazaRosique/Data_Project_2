CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS menores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_adulto UUID REFERENCES adultos(id),
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100),
    dni VARCHAR(20) UNIQUE,
    fecha_nacimiento DATE,
    direccion VARCHAR(100),
    url_foto VARCHAR(255), 
    discapacidad BOOLEAN
);

CREATE TABLE IF NOT EXISTS adultos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100),
    telefono VARCHAR(20), 
    email VARCHAR(100),
    ciudad VARCHAR(100),
    clave VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS historico_ubicaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_menor UUID REFERENCES menores(id),
    latitud DOUBLE PRECISION NOT NULL,
    longitud DOUBLE PRECISION NOT NULL,
    radio INTEGER,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    duracion INTEGER,
    estado VARCHAR(20)
    zona_involucrada VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS zonas_restringidas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_menor UUID REFERENCES menores(id),
    nombre VARCHAR(100),
    latitud DOUBLE PRECISION NOT NULL,
    longitud DOUBLE PRECISION NOT NULL,
    radio_peligro INTEGER,
    radio_advertencia INTEGER
);