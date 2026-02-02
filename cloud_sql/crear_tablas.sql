CREATE TABLE IF NOT EXISTS menores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100),
    dni VARCHAR(20) UNIQUE,
    fecha_nacimiento DATE,
    direccion VARCHAR(100),
    url_foto VARCHAR(255), 
    discapacidad INTEGER
);

CREATE TABLE IF NOT EXISTS padres (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100),
    telefono VARCHAR(20), 
    id_menor INTEGER REFERENCES menores(id) 
);

CREATE TABLE IF NOT EXISTS historico_ubicaciones (
    id SERIAL PRIMARY KEY,
    id_menor INTEGER REFERENCES menores(id),
    latitud DOUBLE PRECISION NOT NULL,
    longitud DOUBLE PRECISION NOT NULL,
    radio INTEGER,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    duracion INTEGER
);

CREATE TABLE IF NOT EXISTS zonas_restringidas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100),
    latitud DOUBLE PRECISION NOT NULL,
    longitud DOUBLE PRECISION NOT NULL,
    radio_peligro INTEGER,
    radio_advertencia INTEGER
);