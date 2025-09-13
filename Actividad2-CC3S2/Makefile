.PHONY: all prepare run run-bg stop hosts-setup tls-cert nginx-install nginx-config nginx-start check-http check-tls dns-demo check-ports logs-demo clean end-to-end table systemd

# Variables (pueden sobrescribirse con variables de entorno)
DOMAIN ?= miapp.local
PORT ?= 8080
MESSAGE ?= "Hola CC3S2"
RELEASE ?= "v1"

# Directorios
ROOT_DIR := $(shell pwd)
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
EVID = evidencias
CERT_DIR = certs

# Meta principal - flujo completo end-to-end
all: prepare hosts-setup tls-cert nginx-install nginx-config nginx-start run-bg check-http check-tls dns-demo logs-demo table

# Preparar entorno virtual e instalar Flask
prepare:
	@echo "🔧 Creando entorno virtual e instalando Flask..."
	@mkdir -p $(EVID) $(CERT_DIR)
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip > /dev/null
	$(PIP) install Flask > /dev/null
	@echo "✅ Entorno preparado"

# Ejecutar aplicación Flask
run:
	@echo "🚀 Iniciando aplicación Flask en puerto $(PORT)..."
	PORT=$(PORT) MESSAGE=$(MESSAGE) RELEASE=$(RELEASE) $(PYTHON) app.py

# Ejecutar aplicación en background
run-bg:
	@echo "🚀 Iniciando aplicación Flask en background..."
	@mkdir -p $(EVID)
	PORT=$(PORT) MESSAGE=$(MESSAGE) RELEASE=$(RELEASE) nohup $(PYTHON) app.py > $(EVID)/app-stdout.log 2>&1 &
	@echo $$! > app.pid
	@echo "✅ Aplicación ejecutándose en background (PID: $$(cat app.pid))"
	@echo "📝 Logs en: $(EVID)/app-stdout.log"
	@sleep 2

# Detener aplicación
stop:
	@echo "🛑 Deteniendo aplicación Flask..."
	@if [ -f app.pid ] && kill -0 $$(cat app.pid) 2>/dev/null; then \
		kill $$(cat app.pid) || true; \
		rm -f app.pid; \
	fi
	@pkill -f "python app.py" || true
	@echo "✅ Aplicación detenida"

# Configurar /etc/hosts
hosts-setup:
	@echo "🌐 Configurando /etc/hosts para $(DOMAIN)..."
	@if ! grep -q "$(DOMAIN)" /etc/hosts; then \
		echo "127.0.0.1 $(DOMAIN)" | sudo tee -a /etc/hosts > /dev/null; \
		echo "✅ $(DOMAIN) agregado a /etc/hosts"; \
	else \
		echo "✅ $(DOMAIN) ya existe en /etc/hosts"; \
	fi

# Generar certificados TLS
tls-cert:
	@echo "🔐 Generando certificados TLS autofirmados..."
	@mkdir -p $(CERT_DIR)
	@if [ ! -f $(CERT_DIR)/$(DOMAIN).crt ]; then \
		openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
			-keyout $(CERT_DIR)/$(DOMAIN).key \
			-out $(CERT_DIR)/$(DOMAIN).crt \
			-subj "/C=PE/ST=Lima/L=Lima/O=CC3S2/CN=$(DOMAIN)" \
			-addext "subjectAltName=DNS:$(DOMAIN),DNS:localhost,IP:127.0.0.1" > /dev/null 2>&1; \
		echo "✅ Certificados generados en $(CERT_DIR)/"; \
	else \
		echo "✅ Certificados ya existen"; \
	fi

# Instalar Nginx (macOS)
nginx-install:
	@echo "📦 Verificando instalación de Nginx..."
	@if ! command -v nginx &> /dev/null; then \
		echo "Instalando Nginx con Homebrew..."; \
		brew install nginx; \
	else \
		echo "✅ Nginx ya está instalado"; \
	fi

# Configurar Nginx
nginx-config:
	@echo "⚙️ Configurando Nginx..."
	@mkdir -p /opt/homebrew/etc/nginx/servers
	@echo 'server {' > /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '    listen 443 ssl;' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '    server_name miapp.local;' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '    ssl_certificate $(PWD)/certs/miapp.crt;' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '    ssl_certificate_key $(PWD)/certs/miapp.key;' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '    ssl_protocols TLSv1.2 TLSv1.3;' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '    ssl_ciphers HIGH:!aNULL:!MD5;' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '    location / {' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '        proxy_pass http://127.0.0.1:$(PORT);' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '        proxy_set_header Host $$host;' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '        proxy_set_header X-Real-IP $$remote_addr;' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '        proxy_set_header X-Forwarded-For $$proxy_add_x_forwarded_for;' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '        proxy_set_header X-Forwarded-Proto $$scheme;' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '    }' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '}' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo 'server {' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '    listen 80;' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '    server_name miapp.local;' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '    return 301 https://$$server_name$$request_uri;' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@echo '}' >> /opt/homebrew/etc/nginx/servers/miapp.conf
	@nginx -t
	@echo "✅ Nginx configurado"

# Iniciar Nginx
nginx-start:
	@echo "▶️ Iniciando Nginx..."
	@brew services start nginx || brew services restart nginx
	@echo "✅ Nginx iniciado"

# Verificar HTTP
check-http:
	@echo "🔍 Verificando endpoint HTTP..."
	@mkdir -p $(EVID)
	@echo "--- GET Request con curl -v ---"
	curl -sS -v http://127.0.0.1:$(PORT)/ -o /dev/null 2> $(EVID)/curl-v.txt || true
	@cat $(EVID)/curl-v.txt
	@echo "\n--- POST Request (debe fallar con 405) ---"
	curl -sS -i -X POST http://127.0.0.1:$(PORT)/ > $(EVID)/curl-post.txt || true
	@cat $(EVID)/curl-post.txt
	@echo "\n--- Puertos abiertos ---"
	lsof -i :$(PORT) | grep LISTEN > $(EVID)/lsof-port.txt || true
	@cat $(EVID)/lsof-port.txt

# Verificar TLS
check-tls:
	@echo "🔐 Verificando conexión TLS..."
	@mkdir -p $(EVID)
	@echo "--- Handshake TLS con openssl s_client ---"
	openssl s_client -connect $(DOMAIN):443 -servername $(DOMAIN) -showcerts </dev/null > $(EVID)/s_client.txt 2>&1 || true
	@head -20 $(EVID)/s_client.txt
	@echo "\n--- Acceso HTTPS con curl -k ---"
	curl -sS -k https://$(DOMAIN)/ -D $(EVID)/curl-https-headers.txt > $(EVID)/curl-https-body.json || true
	@cat $(EVID)/curl-https-body.json | python3 -m json.tool
	@echo "\n--- Puertos 443 y $(PORT) ---"
	lsof -i :443 -i :$(PORT) | grep LISTEN > $(EVID)/lsof-ports-tls.txt || true
	@cat $(EVID)/lsof-ports-tls.txt

# Demo DNS
dns-demo:
	@echo "🌐 Demostrando resolución DNS..."
	@mkdir -p $(EVID)
	@echo "--- Resolución de $(DOMAIN) ---"
	dscacheutil -q host -a name $(DOMAIN) > $(EVID)/dns-resolution.txt || true
	@cat $(EVID)/dns-resolution.txt
	@echo "\n--- Ping a $(DOMAIN) ---"
	ping -c 1 $(DOMAIN) > $(EVID)/ping.txt || true
	@cat $(EVID)/ping.txt
	@echo "\n--- TTL Demo con dig ---"
	dig example.com A > $(EVID)/ttl-demo.txt || true
	@grep -A2 "ANSWER SECTION" $(EVID)/ttl-demo.txt || true

# Verificar puertos
check-ports:
	@echo "🔍 Verificando puertos abiertos..."
	@echo "--- Puerto 8080 (Flask) ---"
	lsof -i :8080 | grep LISTEN || echo "No hay nada escuchando en 8080"
	@echo "\n--- Puerto 443 (HTTPS) ---"
	lsof -i :443 | grep LISTEN || echo "No hay nada escuchando en 443"
	@echo "\n--- Puerto 80 (HTTP) ---"
	lsof -i :80 | grep LISTEN || echo "No hay nada escuchando en 80"

# Demo de logs como flujo (12-Factor)
logs-demo:
	@echo "📝 Demostrando logs como flujo (stdout)..."
	@mkdir -p $(EVID)
	@echo "--- Generando peticiones para producir logs ---"
	@curl -s http://127.0.0.1:$(PORT)/ > /dev/null || true
	@curl -s -X POST http://127.0.0.1:$(PORT)/ > /dev/null || true
	@sleep 1
	@echo "\n--- Capturando logs con pipeline ---"
	@tail -n 10 $(EVID)/app-stdout.log > $(EVID)/logs-sample.txt || true
	@cat $(EVID)/logs-sample.txt
	@echo "\n--- Por qué stdout (12-Factor) ---"
	@echo "La app no escribe archivos de log. Emite a stdout/stderr."
	@echo "El entorno (Docker, systemd, etc.) decide dónde guardar/enviar los logs."
	@echo "Esto simplifica agregación y rotación."

# Limpiar todo
clean:
	@echo "🧹 Limpiando..."
	@make stop
	rm -rf $(VENV) __pycache__ *.log *.pid
	rm -rf $(EVID)
	@echo "✅ Limpieza completada (se conservan certs/)"

# Tabla de comandos y resultados esperados
table:
	@echo "📊 Generando tabla de comandos..."
	@mkdir -p $(EVID)
	@echo "# Comando -> Resultado esperado" > $(EVID)/tabla_comandos.md
	@echo "" >> $(EVID)/tabla_comandos.md
	@echo "| Comando | Resultado esperado |" >> $(EVID)/tabla_comandos.md
	@echo "|---------|-------------------|" >> $(EVID)/tabla_comandos.md
	@echo "| make prepare | Crea venv e instala Flask |" >> $(EVID)/tabla_comandos.md
	@echo "| make run | Inicia Flask en puerto $(PORT) |" >> $(EVID)/tabla_comandos.md
	@echo "| make hosts-setup | Agrega $(DOMAIN) a /etc/hosts |" >> $(EVID)/tabla_comandos.md
	@echo "| make tls-cert | Genera certificados autofirmados |" >> $(EVID)/tabla_comandos.md
	@echo "| make nginx-config | Configura Nginx como reverse proxy |" >> $(EVID)/tabla_comandos.md
	@echo "| make check-http | Verifica endpoints HTTP |" >> $(EVID)/tabla_comandos.md
	@echo "| make check-tls | Valida handshake TLS |" >> $(EVID)/tabla_comandos.md
	@echo "| make dns-demo | Demuestra resolución DNS |" >> $(EVID)/tabla_comandos.md
	@echo "| make logs-demo | Muestra logs como flujo |" >> $(EVID)/tabla_comandos.md
	@cat $(EVID)/tabla_comandos.md

# Test end-to-end completo
end-to-end: all
	@echo "\n✅ Flujo end-to-end completado"
	@echo "📁 Revisa las evidencias en: $(EVID)/"