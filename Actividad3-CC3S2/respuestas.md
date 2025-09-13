# Respuestas Actividad 3: Integración de DevOps y DevSecOps

## Parte teórica

### 1. Introducción a DevOps: ¿Qué es y qué no es?

DevOps es básicamente unir desarrollo y operaciones en un solo flujo de trabajo continuo, muy diferente a waterfall donde todo es secuencial y los equipos no se hablan entre sí. En el laboratorio vemos "you build it, you run it" cuando el mismo equipo que programa la app Flask también configura el Nginx y el Makefile, haciéndose cargo de todo el ciclo de vida.

Lo importante es entender que DevOps no es solo usar Docker o Jenkins, es más bien un cambio cultural basado en CALMS con colaboración y automatización real. Los gates son como checkpoints automáticos que no dejan pasar código malo. Por ejemplo, en el Makefile podríamos agregar un target que revise si las pruebas tienen más del 80% de cobertura, y si no, falla con exit 1 y para todo el pipeline.

### 2. Marco CALMS en acción

CALMS son los cinco pilares de DevOps en la práctica. Culture se ve cuando desarrollo y operaciones trabajan juntos en el mismo código y configuración. Automation está en el Makefile que hace todo automático desde instalar dependencias hasta desplegar. Lean es eliminar lo que no sirve, cada target del Makefile hace algo específico sin repetir.

Measurement aparece con los endpoints `/health/ready` y `/health/live` que nos dicen cómo está la app. Sharing es compartir conocimiento con runbooks para resolver problemas y postmortems para aprender de errores sin echar culpas. En el lab cada archivo cumple su rol: Makefile automatiza, app.py mide con sus endpoints, Nginx y systemd dan la infraestructura, y los docs comparten el conocimiento.

### 3. Visión cultural de DevOps y paso a DevSecOps

DevSecOps es implementar seguridad desde el principio, no al final como antes. Ya no es que el equipo de seguridad revise todo al último, sino que todos somos responsables. En el laboratorio esto se ve con TLS en Nginx y las cabeceras de seguridad HTTP.

Si se nos expira un certificado TLS en producción, haríamos un postmortem sin buscar culpables, veríamos que faltó automatizar la renovación, pondríamos alertas 30 días antes y haríamos un runbook de emergencia. Tres controles de seguridad sin contenedores serían: escanear dependencias con Safety en el CI/CD para encontrar vulnerabilidades, usar pre-commit hooks para que no se suban passwords por error, y análisis de código con Bandit para detectar SQL injections. Todo esto se conecta con Nginx manejando TLS y systemd poniendo permisos al servicio.

### 4. Metodología 12-Factor App

12-Factor App son principios para hacer apps que escalen bien en la nube. La configuración por variables de entorno la vemos cuando app.py usa `os.environ.get()` para cambiar el puerto o mensajes sin tocar código. Port binding es cuando la app se basta sola para servir en un puerto, no necesita que Apache le inyecte nada. Los logs como flujos significa escribir todo a stdout y que systemd/journald se encargue de guardarlos, por eso usamos `journalctl -u myapp`.

El cuarto factor importante es statelessness, o sea que la app no guarde nada entre peticiones. El lab fallaría si guardara datos en memoria o archivos locales en vez de usar Redis o una base de datos. Para producción habría que sacar todo el estado a servicios externos, usar cache distribuido y asegurar que cualquier instancia pueda atender cualquier request. Los backing services son recursos que cambias por configuración, como pasar de Redis a Memcached solo cambiando una variable de entorno.

## Parte Práctica

