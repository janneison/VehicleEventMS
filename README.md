# VehicleEventMS
Microservicio para registrar eventos de vehiculos

## Configuración

El servicio utiliza la variable de entorno `DATABASE_URL` para conectarse a la base de datos.
Al ejecutar con `docker-compose` se usará automáticamente una base de datos local a menos que
se proporcione un valor diferente. Para entornos de producción define esta variable de forma
externa (por ejemplo en un archivo `.env`) y evita commitear credenciales al repositorio.
