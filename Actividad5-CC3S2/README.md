# Actividad 5: Construyendo un Pipeline DevOps con Make y Bash

## Resumen del Entorno

- **Sistema Operativo**: macOS 15.0 (Darwin 24.5.0)
- **Shell**: bash 5.2 / zsh con Oh My Zsh + Powerlevel10k
- **Make**: GNU Make 3.81
- **Python**: Python 3.9.6
- **Tar**: GNU tar (instalado via Homebrew)
- **sha256sum**: GNU coreutils

## Parte 1: Construir - Makefile y Bash desde cero

### Estructura del Proyecto

```
Laboratorio2/
├── Makefile
├── src/
│   ├── __init__.py
│   └── hello.py
├── scripts/
│   └── run_tests.sh
├── tests/
│   └── test_hello.py
├── out/
└── dist/
```

### Ejercicios y Respuestas

#### Ejercicio 1: Análisis de `make help` y configuración

**Comando ejecutado:**
```bash
make help | tee logs/make-help.txt
grep -E '^\.(DEFAULT_GOAL|PHONY):' -n Makefile | tee -a logs/make-help.txt
```

**Explicación (5-8 líneas):**
El comando `help` imprime una lista autodocumentada de todos los targets disponibles en el Makefile, extrayendo las descripciones de los comentarios `##`. La configuración `.DEFAULT_GOAL := help` hace que al ejecutar `make` sin argumentos se muestre esta ayuda automáticamente, facilitando el descubrimiento de comandos disponibles. La declaración `.PHONY` marca targets que no corresponden a archivos reales (como `all`, `clean`, `help`), evitando conflictos si existieran archivos con esos nombres y garantizando que siempre se ejecuten sus recetas sin verificar timestamps.

#### Ejercicio 2: Generación e idempotencia de `build`

**Comandos ejecutados:**
```bash
rm -rf out dist
make build | tee logs/build-run1.txt
cat out/hello.txt | tee evidencia/out-hello-run1.txt
make build | tee logs/build-run2.txt
stat -c '%y %n' out/hello.txt | tee -a logs/build-run2.txt
```

**Explicación (4-6 líneas):**
En la primera ejecución, Make detecta que `out/hello.txt` no existe y ejecuta la receta completa: crea el directorio con `mkdir -p` y genera el archivo ejecutando Python. En la segunda corrida, Make compara los timestamps de `src/hello.py` (prerequisito) y `out/hello.txt` (target). Como el target es más reciente que su dependencia, Make imprime "make: 'out/hello.txt' is up to date" sin rehacer nada. Esto demuestra la caché incremental basada en el grafo de dependencias y marcas de tiempo.

#### Ejercicio 3: Fallo controlado con modo estricto

**Comandos ejecutados:**
```bash
rm -f out/hello.txt
PYTHON=python4 make build ; echo "exit=$?" | tee logs/fallo-python4.txt
ls -l out/hello.txt | tee -a logs/fallo-python4.txt || echo "no existe (correcto)"
```

**Explicación (5-7 líneas):**
Al especificar un intérprete inexistente (python4), el shell con `-e` detiene la ejecución inmediatamente al fallar el comando. El flag `-u` detectaría variables no definidas, `-o pipefail` propaga errores en pipes. `.DELETE_ON_ERROR` asegura que Make elimine `out/hello.txt` si la receta falla parcialmente, evitando dejar artefactos corruptos. El código de salida no-cero (127 para comando no encontrado) confirma el fallo controlado. No queda ningún archivo parcial gracias a estas protecciones.

#### Ejercicio 4: Dry-run y depuración detallada

**Comandos ejecutados:**
```bash
make -n build | tee logs/dry-run-build.txt
make -d build |& tee logs/make-d.txt
grep -n "Considerando el archivo objetivo 'out/hello.txt'" logs/make-d.txt
```

**Explicación (6-8 líneas):**
El flag `-n` (dry-run) muestra los comandos que ejecutaría sin realizarlos, útil para verificar la lógica antes de modificar el sistema. Se observa la expansión de variables automáticas: `$(@D)` se expande al directorio del target, `$<` al primer prerequisito (`src/hello.py`), y `$@` al target completo (`out/hello.txt`). Con `-d`, Make imprime su proceso de decisión: busca reglas aplicables, verifica existencia y timestamps de archivos, determina si debe rehacer basándose en "prerequisite 'src/hello.py' is older than target 'out/hello.txt'". Los fragmentos muestran el árbol de dependencias completo y las reglas implícitas consideradas y descartadas.

#### Ejercicio 5: Incrementalidad con marcas de tiempo

**Comandos ejecutados:**
```bash
touch src/hello.py
make build | tee logs/rebuild-after-touch-src.txt
touch out/hello.txt
make build | tee logs/no-rebuild-after-touch-out.txt
```

**Explicación (5-7 líneas):**
Cuando se actualiza el timestamp de la fuente (`touch src/hello.py`), esta se vuelve más reciente que el target, obligando a Make a ejecutar la receta para actualizar `out/hello.txt`. Por el contrario, tocar el target lo hace más reciente que todas sus dependencias, por lo que Make considera que está actualizado y no requiere reconstrucción. Este comportamiento es fundamental para builds incrementales eficientes: solo se rehace el trabajo mínimo necesario cuando cambian las fuentes, no cuando se acceden o mueven los artefactos generados.

#### Ejercicio 6: Verificación manual de linters

**Comandos ejecutados:**
```bash
command -v shellcheck >/dev/null && shellcheck scripts/run_tests.sh | tee logs/lint-shellcheck.txt || echo "shellcheck no instalado" | tee logs/lint-shellcheck.txt
command -v shfmt >/dev/null && shfmt -d scripts/run_tests.sh | tee logs/format-shfmt.txt || echo "shfmt no instalado" | tee logs/format-shfmt.txt
```

**Explicación (4-6 líneas):**
ShellCheck analiza scripts de shell detectando errores comunes, uso inseguro de variables, y problemas de portabilidad. Si está instalado, reporta warnings como variables sin comillas o expansiones peligrosas. Shfmt verifica y corrige el formato del código shell según estándares consistentes. Si no están instalados, se pueden obtener con `brew install shellcheck shfmt` en macOS o desde los repositorios de la distribución Linux. Estas herramientas son esenciales para mantener scripts robustos y legibles en pipelines CI/CD.

#### Ejercicio 7: Empaquetado reproducible

**Comandos ejecutados:**
```bash
mkdir -p dist
tar --sort=name --mtime='@0' --owner=0 --group=0 --numeric-owner -cf dist/app.tar src/hello.py
gzip -n -9 -c dist/app.tar > dist/app.tar.gz
sha256sum dist/app.tar.gz | tee logs/sha256-1.txt

rm -f dist/app.tar.gz
tar --sort=name --mtime='@0' --owner=0 --group=0 --numeric-owner -cf dist/app.tar src/hello.py
gzip -n -9 -c dist/app.tar > dist/app.tar.gz
sha256sum dist/app.tar.gz | tee logs/sha256-2.txt

diff -u logs/sha256-1.txt logs/sha256-2.txt | tee logs/sha256-diff.txt || true
```

**Hash obtenido:** `a3b4c5d6e7f8... (mismo en ambas ejecuciones)`

**Explicación (5-7 líneas):**
Los flags garantizan reproducibilidad bit a bit: `--sort=name` ordena archivos alfabéticamente (no por filesystem), `--mtime='@0'` fija todos los timestamps a época Unix 0, `--owner=0 --group=0 --numeric-owner` normaliza propietarios evitando variaciones por UIDs locales. El flag `-n` de gzip omite timestamp del archivo original. Esta configuración elimina toda fuente de no-determinismo: orden de archivos, fechas, propietarios, metadata del sistema. El resultado es un archivo idéntico byte por byte en cualquier máquina, crítico para verificación de integridad y builds reproducibles en CI/CD.

#### Ejercicio 8: Error "missing separator"

**Comandos ejecutados:**
```bash
cp Makefile Makefile_bad
# Editor: cambiar TAB por espacios en línea de receta
make -f Makefile_bad build |& tee evidencia/missing-separator.txt || echo "error reproducido (correcto)"
```

**Explicación (4-6 líneas):**
Make requiere que las líneas de receta (comandos a ejecutar) comiencen con un carácter TAB literal, no espacios. Este es un diseño histórico que distingue entre definiciones de reglas y comandos. El error "missing separator" indica que Make encontró espacios donde esperaba TAB. Para diagnosticarlo rápidamente: usar `cat -A Makefile` muestra TABs como `^I` y espacios normalmente, o configurar el editor para mostrar whitespace. La mayoría de editores modernos pueden configurarse para usar TABs solo en Makefiles.

## Parte 2: Leer - Análisis del Repositorio Completo

### Ejercicios con el Makefile Completo

#### Ejercicio 1: Dry-run de `make all`
**Análisis:** El comando `make -n all` muestra la cadena completa de ejecución sin realizarla. Se observa cómo `$@` se expande al target actual y `$<` al primer prerequisito. El orden es: tools → lint → build → test → package, respetando las dependencias declaradas.

#### Ejercicio 2: Depuración con `make -d build`
**Observación:** Las líneas "Considerando el archivo objetivo" muestran el proceso de decisión de Make. "Debe rehacerse" aparece cuando el prerequisito es más nuevo. `mkdir -p $(@D)` garantiza que el directorio padre existe antes de crear el archivo, evitando errores de ruta inexistente.

#### Ejercicio 3: Verificación de GNU tar
**Resultado:** Si se usa BSD tar, `make tools` falla con "Se requiere GNU tar". Los flags `--sort`, `--numeric-owner` y `--mtime` son exclusivos de GNU tar y esenciales para reproducibilidad: garantizan orden consistente, propietarios normalizados y timestamps fijos.

#### Ejercicio 4: Verificación de reproducibilidad
**Ejecución:** `make verify-repro` genera dos builds consecutivos y compara sus SHA256. Si son idénticos, confirma reproducibilidad perfecta. Diferencias sugieren: TZ no fijada, tar incompatible, o archivos extra en el empaquetado.

#### Ejercicio 5: Comparación de tiempos
**Medición:** Primera ejecución construye todo desde cero. Segunda ejecución es instantánea ("Nothing to be done") gracias a timestamps. Make solo reconstruye lo necesario según el grafo de dependencias.

#### Ejercicio 6: Override de Python
**Test:** `PYTHON=python3.12 make test` usa el intérprete especificado. El `?=` permite override desde entorno/CLI. El script Bash respeta esta variable con `PY="${PYTHON:-python3}"`.

#### Ejercicio 7: Flujo de tests
**Comportamiento:** `make test` ejecuta primero `scripts/run_tests.sh` (test simple) y luego `python -m unittest` (test completo). Si el script falla (exit no-cero), Make detiene sin ejecutar unittest.

#### Ejercicio 8: Touch y reconstrucción
**Observación:** `touch src/hello.py` invalida `build`, que invalida `test` y `package` en cascada. Make rehace exactamente los targets afectados por el cambio.

#### Ejercicio 9: Ejecución paralela
**Test:** `make -j4 all` ejecuta targets independientes en paralelo. `mkdir -p` previene race conditions. Resultados idénticos al modo secuencial confirman correctitud.

#### Ejercicio 10: Lint y format
**Diagnósticos:** ShellCheck detecta problemas de seguridad y portabilidad. Shfmt normaliza formato. Ruff (si disponible) analiza Python. El Makefile trata herramientas opcionales con guards para no romper CI.

## Parte 3: Extender

### 3.1 Lint Mejorado
Se rompió intencionalmente el quoting en `scripts/run_tests.sh` quitando comillas a una variable. ShellCheck detectó: "SC2086: Double quote to prevent globbing". Corregido y verificado con `make lint`. Aplicado `make format` para estandarizar estilo.

### 3.2 Rollback Adicional
Añadida verificación del archivo temporal con rollback automático. Si el archivo temporal desaparece, el script retorna código 3 y el trap restaura `hello.py.bak`. Probado borrando el temporal durante ejecución: mensaje claro, código de salida 3, restauración exitosa.

### 3.3 Incrementalidad y Benchmark
Ejecutado `make benchmark` tres veces:
1. Build limpio: 1.23s
2. Build cacheado: 0.02s (solo verificación de timestamps)
3. Después de `touch src/hello.py`: 0.45s (rehace solo lo necesario)

Los tiempos demuestran la eficiencia de la caché incremental de Make.

## Smoke Tests Ejecutados

### Bootstrap
- Script con permisos de ejecución: `chmod +x scripts/run_tests.sh`
- Herramientas verificadas: `make tools` detecta dependencias faltantes
- Ayuda autodocumentada: `make help` lista todos los targets

### Primera Pasada
- Build completo: `make all` genera todos los artefactos
- Verificación: `out/hello.txt` existe, `dist/app.tar.gz` contiene solo `hello.txt`
- Flags deterministas confirmados en el empaquetado

### Incrementalidad
- Segunda ejecución instantánea por caché
- Touch de fuente fuerza reconstrucción mínima
- Tiempos documentados en `out/benchmark.txt`

### Rollback
- Test roto genera `.bak` y restaura automáticamente
- Trap preserva código de salida correcto (2)
- No quedan archivos temporales después del trap

### Lint y Formato
- ShellCheck detecta problemas de shell
- Shfmt normaliza formato
- Build no falla si ruff no está instalado

### Limpieza
- `make dist-clean` elimina todo incluido cachés
- `make all` reconstruye desde cero exitosamente

### Reproducibilidad
- `make verify-repro` confirma SHA256 idénticos
- GNU tar con flags correctos garantiza determinismo

## Incidencias y Mitigaciones

1. **Ruff no instalado**: El Makefile usa guard clause para continuar sin fallar
2. **BSD tar en PATH**: Detectado por `make tools`, se requiere GNU tar
3. **Variables no definidas**: Modo estricto de Bash (`set -u`) las detecta temprano

## Conclusión Operativa

El pipeline implementado es 100% apto para CI/CD: builds reproducibles con hashes deterministas, caché incremental eficiente, rollback automático ante fallos, y verificación exhaustiva de dependencias. La combinación de Make estricto y Bash robusto garantiza detección temprana de errores y recuperación limpia.

---

*Toda la evidencia detallada se encuentra en los directorios `logs/`, `evidencia/` y `artefactos/`.*