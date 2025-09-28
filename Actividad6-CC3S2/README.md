# Actividad 6: Git Conceptos Básicos - CC3S2

## Configuración
- **git config**: Configurado con nombre "Melissa Iman Noriega" y email "melissa.iman.n@uni.pe"
- **git init**: Inicializado repositorio en kapumota-repo/

## Comandos Básicos
- **add/commit**: Primer commit con README.md usando `git add` y `git commit -m "feat: inicial con README"`
- **git log**: Historial mostrado con `git log --oneline`

## Trabajo con Ramas
- **crear/cambiar**: Creada rama feature/new-feature con `git branch` y `git checkout`
- **merge y resolución**: Fusión con conflicto en main.py, resuelto manualmente combinando cambios

## Comandos Avanzados (Opcionales)
- **revert**: Revertido commit de test.txt
- **cherry-pick**: Aplicado commit específico de rama experimental
- **stash**: Guardado trabajo temporal con `git stash save`

## Archivos de Logs Generados

| Archivo | Comando que lo generó |
|---------|----------------------|
| `logs/git-version.txt` | `git --version` |
| `logs/config.txt` | `git config --list` |
| `logs/init-status.txt` | `git init` + `git status` |
| `logs/add-commit.txt` | `git log --oneline` (después del primer commit) |
| `logs/log-oneline.txt` | `git log --oneline` |
| `logs/branches.txt` | `git branch -vv` |
| `logs/merge-o-conflicto.txt` | `git merge feature/new-feature` (con resolución) |
| `logs/revert.txt` | `git revert HEAD` |
| `logs/cherry-pick.txt` | `git cherry-pick edd6164` |
| `logs/stash.txt` | `git stash save` + `git stash list` |

## Remoto
Sin remoto configurado (trabajo local únicamente)