## Taskboard Swarm Practice
Proyecto práctico para demostrar el uso real de Docker Swarm como orquestador, implementando un stack completo con servicios reales, routing dinámico, secrets, persistencia, escalado, self-healing y rolling updates.

## Objetivo
Demostrar cómo desplegar y operar una arquitectura backend completa utilizando Docker Swarm, enfocándose en aspectos de orquestación y operación más que en funcionalidades de negocio.

## Arquitectura
Componentes:
-Traefik - Reverse proxy y Load balancer (entrypoint HTTP)
-FastAPI - Backend API (servicio replicado)
-PostgreSQL - Base de datos con volumen persistente
-Docker Swarm - Orquestador

Flujo simplificado:

Cliente (curl/browser) -> Traefik -> FastAPI -> PostgreSQL

## Stack técnico
-Docker swarm (single node -- docker-desktop)
-Traefik v2
-FastAPI + Uvicorn 
-PostgreSQL 16
-Docker Secrets
-Docker Volumes 
-Overlay Network

## Funcionalidades demostradas
1|Orquestación con Docker Swarm
-Inicialización de cluster local 
-Deploy mediante docker stack deploy
-Gestión de servicios, tasks y réplicas

2|Arquitectura multi-servicio real
-Servicios desacoplados
-Comunicación interna mediante overlay network
-Separación de responsabilidades (proxy/app/DB)

3|Routing dinámico con Traefik
-Descubrimiento automático de servicios vía labels
-Routing HTTP con PathPrefix(/api)
-Middleware stripPrefix para desacoplar rutas externas de rutas internas

Ejemplo: /api/tasks -> /tasks (backend)

4|Load balancing
-Distribución automática de tráfico entre múltiples réplicas del backend

5|Escalado horizontal
-Escalado manual del servicio API(se cambió de 2->5 réplicas)
-Redistribución automática de tasks

6|Self-healing
-Detección automática de contenedores fallidos
-Recreación de tasks para mantener el estado deseado

7|Rolling updates sin downtime
-Actualización de imagen del backend (1.0 -> 1.1)
-Estrategia start-first
-Validación con requests continuos durante el update

8|Gestión de secrets (Swarm only)
-Uso de docker secret
-Inyección como archivos (*_FILE)
-Separación entre configuración y credenciales

9|Persistencia de datos
-Uso de volumen nombrado (pgdata)
-Datos sobreviven a: redeploy del stack, eliminación de servicios, salida del swarm

10| Inicialización automática (seed)
-Creación automática de esquema
-Inserción de datos iniciales si la tabla está vacía
-Deploy reproducible sin pasos manuales

## Validaciones operativas realizadas
-Escalado del backend de 2 a 5 réplicas
-Verificación de balanceo de carga
-Prueba de self-healing forzando la muerte de contenedores
-Rolling update de imagen sin downtime
-Verificación de persistencia de datos tras redeploy

## Decisiones de diseño relevantes
Uso de /api + stripPrefix, se utilizó Traefik como API gateway para:
-Mantener el backend desacoplado del proxy
-Permitir versionado futuro (/api/v1, /api/v2)
-Facilitar múltiples servicios bajo un mismo dominio

## Qué no busca este proyecto
-No es un entorno productivo completo
-No incluye TLS / certificados
-No incluye CI/CD
-No incluye autenticación
-No incluye el frontend
-El código del archivo main.py se utiliza únicamente con fines demostrativos, como soporte para validar el comportamiento del stack y de Docker Swarm.

## Este proyecto es para demostrar:
-Entendimiento real de Docker Swarm
-Diseño de stacks reproducibles
-Manejo de routing y proxies
-Uso correcto de secrets
-Persistencia en entornos orquestados
-Escalado y alta disponibilidad
-Actualización sin downtime


## Ejecución Rápida
# Crear secrets
docker secret create postgres_password -
docker secret create jwt_secret -

# deploy
docker stack deploy -c docker-stack.yml taskboard

# API disponible en:
http://localhost:8080/api/health
http://localhost:8080/api/tasks

# Dashboard Traefik en:
http://localhost:8081/dashboard/


## Pipeline CI/CD
Se extendió el proyecto para incluir un pipeline completo de CI/CD con GitHub Actions

# ¿Cómo sigue?
La app originalmente se podía levantar con Docker Swarm o localmente usando Docker. A partir de la integración con GitHub Actions, ahora cada push a la rama main dispara automáticamente:
- Construcción de la imagen Docker desde el Dockerfile
- Etiquetado con latest y con el SHA del commit
- Publicación de la imagen en Docker Hub

Esto permite tener imágenes versionadas y listas para el despliegue sin intervención manual.

# ¿Cómo está implementado?
Debajo de la carpeta .github/workflows/ están los workflows que:
- configuran el trigger del pipeline
- hacen login a Docker Hub usando secrets
- construyen y taggean la imagen
- la pushean al registry

## Conclusión 
Al combinar Docker, Swarm, y GitHub Actions, este proyecto tiene como objetivo demostrar un flujo completo que va desde el desarrollo hasta la publicación automatizada de artefactos.