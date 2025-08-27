from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text # Importar text para ejecutar SQL raw

from app.core.domain.services import GeolocationService
from app.core.domain.entities import GeolocationInfo

class PostgresGeolocationAdapter(GeolocationService):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_address_from_coords(self, latitude: float, longitude: float) -> Optional[GeolocationInfo]:
        """
        Realiza la geocodificación inversa llamando a la función PL/pgSQL getdireccion.
        """
        try:
            # Ejecutar la función getdireccion en PostgreSQL
            # La función getdireccion devuelve un tipo compuesto (composite type) o un RECORD.
            # Necesitamos mapear eso a nuestros campos.
            # Asumiendo que getdireccion retorna una tupla o un record con campos like (direccion, municipio, departamento)
            # El nombre de la función en el SP es getdireccion.
            query = text("SELECT * FROM getdireccion(:lat, :lon)")
            
            # Ejecutar la consulta y obtener el resultado
            result = await self.session.execute(query, {"lat": latitude, "lon": longitude})
            row = result.fetchone()

            if row:
                # Acceder a los campos por índice o por nombre si es posible
                # Asumo que la función getdireccion devuelve 3 columnas en este orden
                # (direccion TEXT, municipio TEXT, departamento TEXT)
                address = row[0] if len(row) > 0 else None
                city = row[1] if len(row) > 1 else None
                department = row[2] if len(row) > 2 else None
                if address and address.lower() == 'no disponible':
                    address = None
                if city and city.lower() == 'no disponible':
                    city = None
                if department and department.lower() == 'no disponible':
                    department = None

                return GeolocationInfo(address=address, city=city, department=department)
            
            return GeolocationInfo(address='No Disponible', city='No Disponible', department='No Disponible') # Default if no row

        except Exception as e:
            print(f"Error calling getdireccion in PostgreSQL: {e}")
            # En caso de error, retorna un objeto con info 'No Disponible'
            return GeolocationInfo(address='No Disponible', city='No Disponible', department='No Disponible')