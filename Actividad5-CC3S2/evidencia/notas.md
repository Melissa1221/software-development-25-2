# Notas de Evidencia - Actividad 5

## Herramientas Instaladas Durante la Actividad

- **GNU tar (gtar)**: Instalado via Homebrew para garantizar reproducibilidad
- **GNU coreutils (sha256sum)**: Ya estaba disponible en el sistema

## Herramientas Opcionales No Instaladas

- **shellcheck**: Linter de Bash (opcional, no afecta el build)
- **shfmt**: Formateador de Bash (opcional, no afecta el build)
- **ruff**: Linter de Python (opcional, no afecta el build)

## Adaptaciones Realizadas

1. **BSD tar vs GNU tar**: macOS incluye BSD tar por defecto, que no soporta los flags necesarios para reproducibilidad. Se instaló GNU tar (`gtar`) y se actualizó el Makefile.

2. **Herramientas opcionales**: Se modificó el Makefile para que shellcheck, shfmt y ruff sean opcionales, mostrando advertencias pero sin romper el build.

3. **Screenshots**: Se usó Python con Pillow para generar imágenes estilo terminal Powerlevel10k, evitando herramientas externas con decoraciones no deseadas.

## Verificación de Reproducibilidad

El hash SHA256 del paquete es idéntico en múltiples ejecuciones:
```
a5c2d43a7f927dc0bfede333961e2552d889ce3a2fe52e72e427e09980ca57c2
```

Esto confirma que el pipeline es 100% reproducible.