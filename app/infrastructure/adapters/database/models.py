# flake8: noqa
import geoalchemy2 as ga  # For geometry types
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    Numeric,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Vehiculos(Base):
    __tablename__ = "vehiculos"
    idvehiculo = Column(String, primary_key=True)
    estado = Column(String)  # 'Y' or 'N'
    tipo_modem = Column(String)
    velocidad = Column(Float)
    direccion = Column(String)
    latitud = Column(String)
    longitud = Column(String)
    municipio = Column(String)
    departamento = Column(String)
    ultperiodo = Column(BigInteger)
    enc_apa = Column(String)
    idconductor = Column(BigInteger)
    idconductor_actual = Column(BigInteger)
    ultimaactualizacion = Column(DateTime)
    ultimoevento = Column(Integer)
    rumbo = Column(Integer)
    rumbo_linea_tiempo = Column(Integer)
    indexgeoc = Column(Integer)
    estadosenal = Column(String)
    encendido = Column(Boolean)
    indexevento = Column(BigInteger)
    contratista = Column(String)
    recurso = Column(String)


class Eventos(Base):
    __tablename__ = "eventos"
    idevento = Column(BigInteger, primary_key=True, autoincrement=True)
    idvehiculo = Column(String(25))
    evento = Column(String(5))  # event code stored as text in DB
    fecha = Column(DateTime)
    velocidad = Column(String(10))
    direccion = Column(String(100))
    latitud = Column(String(50))
    longitud = Column(String(50))
    xpos = Column(Numeric(16, 8))
    ypos = Column(Numeric(16, 8))
    municipio = Column(String)
    departamento = Column(String)
    idevento_ini = Column(BigInteger)
    idgeocerca = Column(BigInteger)
    idpunto = Column(BigInteger)
    indicegeocerca = Column(Integer, server_default=text("0"))
    fecha_insercion = Column(DateTime, server_default=text("now()"))
    idconductor = Column(BigInteger)
    idprogramacion = Column(BigInteger)
    rumbo = Column(BigInteger)


class EventosDesc(Base):
    __tablename__ = "eventosdesc"
    evento = Column(String, primary_key=True)  # event_code as string
    estatico = Column(String)  # 'S' or 'N'


class Procesos(Base):
    __tablename__ = "procesos"
    proceso = Column(String, primary_key=True)
    contratistas = Column(String)  # Regex string
    toleranciatiempo = Column(Integer)


class EjesViales(Base):
    __tablename__ = "EjesViales"  # Note the mixed case from SP, adjust if needed
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    direccion = Column(String)
    municipio = Column(String)
    latitud = Column(Float)
    longitud = Column(Float)
    dirnoform = Column(String)
    the_geom = Column(ga.Geometry("POINT", srid=4326))
    flat_geom = Column(
        ga.Geometry("POINT", srid=21892)
    )  # Assumed SRID 21892 for ST_Transform from SP
    xpos = Column(Float)
    ypos = Column(Float)


class PeriodosActivo(Base):
    __tablename__ = "periodosactivo"
    idperiodo = Column(BigInteger, primary_key=True, autoincrement=True)
    idvehiculo = Column(String)
    fechadesde = Column(DateTime)
    fechahasta = Column(DateTime)
    idconductor = Column(BigInteger)


class PeriodosConductores(Base):
    __tablename__ = "periodosconductores"
    idperiodo = Column(
        BigInteger, primary_key=True, autoincrement=True
    )  # Assuming a primary key
    idvehiculo = Column(String)
    idconductor = Column(BigInteger)
    fechadesde = Column(DateTime)
    fechahasta = Column(DateTime)


class ProgramacionVehicularModel(
    Base
):  # To check active programs (for idconductor_actual reset)
    __tablename__ = "progvehiculos"
    idprogramacion = Column(BigInteger, primary_key=True)
    idvehiculo = Column(String)
    activa = Column(String)  # 'S' or 'N'


class Odométros(Base):
    __tablename__ = "odometros"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    idvehiculo = Column(String)
    valor = Column(Float)
    fecha = Column(DateTime)


class Recursos(Base):
    __tablename__ = "Recursos"  # Note the mixed case, adjust if needed
    id = Column(
        BigInteger, primary_key=True, autoincrement=True
    )  # Assuming primary key
    recurso = Column(String)
    contratista = Column(String)
    fechagps = Column(DateTime)
    estadogps = Column(String)  # 'OK' or 'NOTOK'


class EventosResumen(Base):
    __tablename__ = "eventos_resumen"
    idvehiculo = Column(String, primary_key=True)
    idevento = Column(SmallInteger, primary_key=True)
    valor = Column(BigInteger)
    fecha = Column(Date, primary_key=True)
    hora = Column(SmallInteger, primary_key=True)


# Special Transport Tables
class ProgEspecialesVehiculos(Base):
    __tablename__ = "prog_especiales_vehiculos"
    idprogramacion = Column(BigInteger, primary_key=True)
    idvehiculo = Column(String)
    fechasalida = Column(DateTime)
    finalizado = Column(String)  # 'N' or 'S'
    cancelada = Column(String)  # 'N' or 'S'
    activa = Column(String)  # 'S' or 'N'
    idruta = Column(Integer)


class RutasEspecialesDetalles(Base):
    __tablename__ = "rutas_especiales_detalles"
    id = Column(
        BigInteger, primary_key=True, autoincrement=True
    )  # Assuming primary key
    idruta = Column(Integer)
    idpunto = Column(BigInteger)
    orden = Column(Integer)
    tiempoglobal = Column(Float)


class PuntosControl(Base):  # Not `PuntosControlEspeciales`
    __tablename__ = "puntoscontrol"
    idpunto = Column(BigInteger, primary_key=True)
    latitud = Column(Float)
    longitud = Column(Float)
    radio = Column(Float)  # In meters


class RutasEspecialesControl(Base):
    __tablename__ = "rutas_especiales_control"
    id = Column(
        BigInteger, primary_key=True, autoincrement=True
    )  # Assuming primary key
    idprogramacion = Column(BigInteger)
    idpunto = Column(BigInteger)
    fecha = Column(DateTime)
    tiempoint = Column(Float)
    tiempoglobal = Column(Float)
    diferenciaint = Column(Float)
    diferenciaglobal = Column(Float)
    orden = Column(Integer)
