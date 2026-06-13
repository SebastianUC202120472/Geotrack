# Flujo de trabajo Git — GeoTrack (Gitflow)

Este repositorio sigue el modelo **Gitflow** como estándar de ramas. Está
configurado con la extensión `git-flow` (AVH Edition), pero todo se puede hacer
también con `git` "puro" (los comandos equivalentes están más abajo).

---

## 1. Ramas permanentes

| Rama | Propósito | ¿Se trabaja directo aquí? |
|---|---|---|
| **`main`** | Código en **producción**. Cada commit aquí es una versión liberada y va **etiquetada** (`v1.0.0`, `v1.1.0`, …). | ❌ NO. Solo recibe merges de `release/*` y `hotfix/*`. |
| **`develop`** | Rama de **integración**. Acumula lo terminado de la próxima versión. | ❌ NO directo. Recibe merges de `feature/*`. |

> El CI/CD (`.github/workflows/ci.yml`) se ejecuta automáticamente en cada
> `push` y `pull request` a **`develop`** y **`main`**.

## 2. Ramas temporales

| Prefijo | Nace de | Se fusiona en | ¿Para qué? |
|---|---|---|---|
| `feature/` | `develop` | `develop` | Una funcionalidad nueva (ej. un CUS, un endpoint, una página). |
| `release/` | `develop` | `main` **y** `develop` | Preparar una versión: ajustes finales, número de versión, QA. |
| `hotfix/` | `main` | `main` **y** `develop` | Arreglo urgente de un bug que ya está en producción. |
| `bugfix/` | `develop` | `develop` | Corregir un bug detectado durante el desarrollo (aún no liberado). |

---

## 3. Comandos del día a día

### Funcionalidad nueva (lo más común)

```bash
# Empezar (crea feature/<nombre> desde develop)
git flow feature start mi-funcionalidad
#   equivalente puro:  git checkout develop && git checkout -b feature/mi-funcionalidad

# ... programar y commitear normalmente ...
git add .
git commit -m "feat: descripción del cambio"

# Terminar (fusiona en develop y borra la rama feature)
git flow feature finish mi-funcionalidad
#   equivalente puro:  git checkout develop && git merge --no-ff feature/mi-funcionalidad && git branch -d feature/mi-funcionalidad
```

### Publicar una versión (release)

```bash
git flow release start 1.0.0          # nace de develop
# ... ajustes finales / fijar versión ...
git flow release finish 1.0.0         # fusiona en main + develop y crea el tag v1.0.0
git push origin main develop --tags
```

### Arreglo urgente en producción (hotfix)

```bash
git flow hotfix start 1.0.1           # nace de main
# ... corregir el bug ...
git flow hotfix finish 1.0.1          # fusiona en main + develop y crea el tag v1.0.1
git push origin main develop --tags
```

---

## 4. Convención de mensajes de commit

Se recomienda **Conventional Commits** para que el historial sea legible:

| Prefijo | Cuándo |
|---|---|
| `feat:` | nueva funcionalidad |
| `fix:` | corrección de bug |
| `docs:` | solo documentación |
| `refactor:` | reestructurar sin cambiar comportamiento |
| `test:` | añadir o corregir pruebas |
| `chore:` | tareas varias (deps, config, build) |

Ejemplo: `feat(conductor): endpoint para validar QR en almacén (CUS-22)`

---

## 5. Regla de oro

> **Nunca se hace `commit` directo a `main` ni a `develop`.**
> Todo cambio entra por una rama `feature/`, `bugfix/`, `release/` o `hotfix/`.
> Así el CI valida el código antes de integrarse y el historial queda limpio.
