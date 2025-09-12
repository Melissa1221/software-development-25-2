# Reporte - Actividad 2: HTTP, DNS, TLS y 12-Factor

## 1) HTTP: Fundamentos y herramientas

### 1.1 Levantando la aplicación con variables de entorno

Para comenzar esta actividad, primero necesité preparar el entorno de desarrollo. Como estoy trabajando en macOS, tuve que hacer algunos ajustes específicos para mi sistema.

#### Preparación del entorno
Primero creé un entorno virtual de Python para mantener las dependencias aisladas:

```bash
python3 -m venv venv
```

Luego instalé Flask en este entorno:

```bash
venv/bin/pip install Flask
```

#### Ejecución con variables de entorno (12-Factor)
Ejecuté la aplicación pasándole las variables de entorno según los principios 12-Factor:

```bash
PORT=8080 MESSAGE="Hola CC3S2" RELEASE="v1" venv/bin/python app.py
```

#### Extracto de salida (stdout)
La aplicación arrancó correctamente y esto es lo que mostró en la salida estándar:

![Imagen 1](images/1.png)

Como podemos ver, la aplicación:
- **Escucha** en el puerto 8080 (configurado por la variable `PORT`)
- **Loggea en stdout** siguiendo los principios 12-Factor
- Usa las variables `MESSAGE` y `RELEASE` desde el entorno

### 1.2 Inspección con curl

Para verificar que la aplicación funciona correctamente, utilicé curl para hacer peticiones HTTP.

#### GET Request
```bash
curl -v http://127.0.0.1:8080/
```

**Salida completa:**
![Imagen 2](images/2.png)

La respuesta muestra que la aplicación está usando correctamente las variables de entorno que le pasamos.

#### POST Request (método no permitido)
También probé hacer una petición POST para ver cómo maneja métodos no permitidos:

```bash
curl -i -X POST http://127.0.0.1:8080/
```

**Salida:**
![Imagen 3](images/3.png)

Como era de esperarse, la aplicación devuelve un error 405 indicando que el método POST no está permitido en esa ruta.

#### Pregunta guía
**¿Qué campos de respuesta cambian si actualizas MESSAGE/RELEASE sin reiniciar el proceso?**

La respuesta es que **ningún campo cambiaría**. Las variables de entorno se leen una sola vez cuando el proceso Python inicia. Si cambio las variables en mi terminal después de que la aplicación ya está corriendo, estos cambios no se reflejarán en las respuestas. Para que la aplicación tome los nuevos valores, necesito detenerla (Ctrl+C) y volver a ejecutarla con las nuevas variables.

### 1.3 Puertos abiertos (en macOS uso lsof en lugar de ss)

Como estoy en macOS, el comando `ss` no está disponible, así que uso `lsof` para ver qué proceso está escuchando en el puerto:

```bash
lsof -i :8080
```

**Salida:**
![Imagen 4](images/4.png)

Esta salida muestra:
- El proceso Python con PID 10486 está escuchando
- Está usando IPv4 en localhost:8080 (http-alt es el nombre del servicio para el puerto 8080)
- El estado es LISTEN, esperando conexiones

### 1.4 Logs como flujo (stdout)

Los logs de la aplicación salen por stdout, lo cual es fundamental para el principio 12-Factor de tratar los logs como streams de eventos:

**Ejemplo real de logs capturados:**
```
2025-09-12 15:18:22,721 - __main__ - INFO - Starting Flask application on port 8080
2025-09-12 15:18:22,721 - __main__ - INFO - Configuration: MESSAGE='Hola CC3S2', RELEASE='v1'
2025-09-12 15:18:22,724 - werkzeug - INFO - WARNING: This is a development server.
2025-09-12 15:18:22,724 - werkzeug - INFO - Running on http://127.0.0.1:8080
2025-09-12 15:18:30,570 - __main__ - INFO - Request received: GET / from 127.0.0.1
2025-09-12 15:18:30,570 - __main__ - INFO - Response sent: {"message": "Hola CC3S2", "release": "v1"}
2025-09-12 15:18:30,570 - werkzeug - INFO - 127.0.0.1 - - [12/Sep/2025 15:18:30] "GET / HTTP/1.1" 200 -
2025-09-12 15:18:36,071 - __main__ - INFO - POST request received from 127.0.0.1
2025-09-12 15:18:36,071 - werkzeug - INFO - 127.0.0.1 - - [12/Sep/2025 15:18:36] "POST / HTTP/1.1" 405 -
```

**¿Por qué NO se escriben en archivo?**

La filosofía 12-Factor dice que los logs deben tratarse como un flujo de eventos que sale por stdout/stderr. La aplicación NO debe preocuparse por dónde se guardan los logs porque:

1. **Simplifica el despliegue en contenedores** - Docker y Kubernetes capturan stdout automáticamente
2. **La plataforma decide qué hacer con los logs** - Pueden ir a un archivo, a un servicio de agregación, o a múltiples destinos
3. **Evita problemas de permisos** - No necesitas preocuparte por permisos de escritura en directorios
4. **Facilita la agregación centralizada** - Los logs de múltiples instancias se pueden combinar fácilmente

## 2) DNS: Nombres, registros y caché

### 2.1 Configuración de hosts local

Para poder acceder a la aplicación usando un nombre de dominio en lugar de una IP, agregué una entrada al archivo `/etc/hosts`:

```bash
echo "127.0.0.1 miapp.local" | sudo tee -a /etc/hosts
```

### 2.2 Comprobación de resolución

En macOS, `dig` no lee `/etc/hosts` (solo consulta DNS real), así que uso `dscacheutil` que sí respeta el archivo hosts:

```bash
dscacheutil -q host -a name miapp.local
```

**Salida:**
![Imagen 5](images/5.png)

También puedo verificar con ping:
```bash
ping -c 1 miapp.local
```

Que resuelve correctamente a 127.0.0.1.

### 2.3 TTL y caché (conceptual)

Para entender el TTL, consulté un dominio real:

```bash
dig example.com A
```

**Salida (extracto):**
![Imagen 6](images/6.png)

El número `28` es el TTL en segundos. Esto significa que mi resolver puede cachear esta respuesta por 28 segundos antes de tener que consultar de nuevo.

### 2.4 Pregunta guía
**¿Qué diferencia hay entre /etc/hosts y una zona DNS autoritativa?**

La diferencia es bastante significativa:

- **/etc/hosts** es un archivo local en mi máquina que solo afecta a mi computadora. Es estático, no tiene concepto de TTL, y tengo control total sobre él. Es perfecto para desarrollo porque puedo simular cualquier dominio sin afectar a nadie más.

- **Una zona DNS autoritativa** es un servidor DNS que tiene la autoridad oficial sobre un dominio. Responde consultas desde cualquier parte de internet, maneja TTLs, puede tener múltiples tipos de registros (A, AAAA, MX, TXT, etc.), y los cambios se propagan globalmente.

**/etc/hosts sirve para laboratorio** porque es inmediato (no hay propagación DNS), no requiere configurar un servidor DNS real, y me permite trabajar con dominios ficticios sin comprar un dominio real. Es la solución perfecta para desarrollo local.

## 3) TLS: Seguridad en tránsito con Nginx

### 3.1 Generación de certificado autofirmado

Para simular HTTPS en desarrollo, generé un certificado autofirmado:

```bash
mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout certs/miapp.key \
    -out certs/miapp.crt \
    -subj "/C=PE/ST=Lima/L=Lima/O=CC3S2/CN=miapp.local" \
    -addext "subjectAltName = DNS:miapp.local,DNS:localhost,IP:127.0.0.1"
```

**Salida:**
![Imagen 7](images/7.png)

Verifiqué que se crearon correctamente:
```bash
ls -la certs/
```

**Resultado:**
```
total 16
drwxr-xr-x@  4 melissaimannoriega  staff   128 Sep 12 15:19 .
drwxr-xr-x  12 melissaimannoriega  staff   384 Sep 12 15:19 ..
-rw-r--r--@  1 melissaimannoriega  staff  1208 Sep 12 15:19 miapp.crt
-rw-r--r--@  1 melissaimannoriega  staff  1708 Sep 12 15:19 miapp.key
```

### 3.2 Configuración de Nginx

Primero instalé Nginx en macOS usando Homebrew:

```bash
brew install nginx
```

**Salida:**
```
==> Installing nginx
==> Pouring nginx--1.29.1.arm64_sequoia.bottle.tar.gz
🍺  /opt/homebrew/Cellar/nginx/1.29.1: 27 files, 2.5MB
```

Luego creé la configuración de Nginx como reverse proxy con terminación TLS:

**Archivo: /opt/homebrew/etc/nginx/servers/miapp.conf**
```nginx
server {
    listen 443 ssl;
    server_name miapp.local;

    # Certificados TLS
    ssl_certificate /Users/melissaimannoriega/Documents/UNI/7CICLO/DS/software-development-25-2/Actividad2-CC3S2/certs/miapp.crt;
    ssl_certificate_key /Users/melissaimannoriega/Documents/UNI/7CICLO/DS/software-development-25-2/Actividad2-CC3S2/certs/miapp.key;

    # Configuración SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Logs
    access_log /opt/homebrew/var/log/nginx/miapp_access.log;
    error_log /opt/homebrew/var/log/nginx/miapp_error.log;

    location / {
        # Proxy a Flask
        proxy_pass http://127.0.0.1:8080;
        
        # Headers X-Forwarded
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
    }
}

# Redirección HTTP a HTTPS
server {
    listen 80;
    server_name miapp.local;
    return 301 https://$server_name$request_uri;
}
```

Verifiqué la configuración:
```bash
nginx -t
```

**Salida:**
![Imagen 8](images/8.png)

Inicié el servicio de Nginx:
```bash
brew services start nginx
```

**Salida:**
```
==> Successfully started `nginx` (label: homebrew.mxcl.nginx)
```

Esta configuración hace que Nginx:
- Escuche en el puerto 443 (HTTPS) con nuestro certificado
- Redirija todo el tráfico HTTP (puerto 80) a HTTPS
- Actúe como proxy reverso, enviando las peticiones a Flask en el puerto 8080
- Agregue headers X-Forwarded-* para que Flask sepa la IP real del cliente

### 3.3 Validación del handshake TLS

Validé el handshake TLS conectándome al servidor Nginx:

```bash
echo | openssl s_client -connect miapp.local:443 -servername miapp.local -showcerts 2>/dev/null | head -20
```

**Salida:**
![Imagen 11](images/11.png)

Se puede ver que:
- La conexión TLS se estableció correctamente (CONNECTED)
- El certificado es autofirmado (s: e i: son iguales)
- El CN del certificado es miapp.local
- SNI (Server Name Indication) funcionó correctamente

Probé el acceso HTTPS con curl:
```bash
curl -k https://miapp.local/
```

**Salida:**
```json
{"message":"Hola CC3S2","method":"GET","path":"/","release":"v1","timestamp":"2025-09-12T21:45:36.431415"}
```

El flag `-k` ignora el error de certificado autofirmado. En producción NUNCA usaríamos este flag y tendríamos certificados válidos de una CA real.

### 3.4 Puertos y logs

Verifiqué que tanto Nginx (443, 80) como Flask (8080) están escuchando:

```bash
lsof -i :443 -i :80 -i :8080 | grep LISTEN
```

**Salida:**
![Imagen 12](images/12.png)

Se puede observar que:
- **Python** (Flask) está escuchando en el puerto 8080 (http-alt)
- **Nginx** está escuchando en:
  - Puerto 443 (https) para TLS
  - Puerto 80 (http) para redireccionar a HTTPS
  - También tiene configurado el puerto 8080 por defecto de Homebrew

Los logs de Nginx en macOS con Homebrew están en:
```bash
ls -la /opt/homebrew/var/log/nginx/
```

**Salida:**
```
total 8
drwxr-xr-x  4 melissaimannoriega  admin  128 Sep 12 15:43 .
drwxr-xr-x  3 melissaimannoriega  admin   96 Sep 12 15:43 ..
-rw-r--r--  1 melissaimannoriega  admin   89 Sep 12 15:45 miapp_access.log
-rw-r--r--  1 melissaimannoriega  admin    0 Sep 12 15:43 miapp_error.log
```
