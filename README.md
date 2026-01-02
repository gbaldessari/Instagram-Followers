# Instagram-Followers

Script en Python para identificar **usuarios que sigues (following)** pero **que no te siguen (followers)** a partir del **export de datos de Instagram** (archivos JSON).

Genera una lista con el `username` y el enlace al perfil.

---

## Requisitos

- Python 3.10+.

---

## Cómo obtener los archivos JSON (export de Instagram)

1. En Instagram (app o web), ve a:
   - **Configuración y privacidad** → **Centro de cuentas** → **Tu información y permisos** → **Exportar tu información** → **Exportar al dispositivo**
2. Crea una solicitud de descarga:
   - Personalizar información: selecciona (al menos) la sección de **Conexiones / Seguidores y seguidos** (el nombre puede variar según idioma/versión).
   - Formato: **JSON**
   - Intervalo de fechas: **Desde el principio**
3. Espera a que Instagram prepare el archivo y descárgalo (normalmente es un `.zip`).
4. Descomprime el `.zip` y busca los archivos:
   - `followers_1.json`
   - `following.json`

Rutas típicas dentro del ZIP (pueden variar):

- `connections/followers_and_following/followers_1.json`
- `connections/followers_and_following/following.json`

Notas:

- A veces `followers_1.json` puede llamarse `followers.json` o venir particionado (`followers_1.json`, `followers_2.json`, etc.). Este script usa `followers_1.json` por defecto; si tienes otro nombre o ruta, pásalo por parámetro.

---

## Datos de entrada (export de Instagram)

Este proyecto trabaja con los JSON del export. Por defecto espera estos archivos en el mismo directorio:

- `followers_1.json`
- `following.json`

### Estructuras esperadas (resumen)

**followers_1.json** (lista):

- Cada elemento contiene `string_list_data` (lista).
- Cada ítem dentro de `string_list_data` contiene:
  - `value`: username
  - `href`: URL del perfil (ej: `https://www.instagram.com/usuario`)

**following.json** (objeto):

- Clave `relationships_following` (lista).
- Cada elemento contiene:
  - `title`: username
  - `string_list_data[0].href`: URL (a veces con `/_u/`)

> Nota: el script normaliza los usernames a minúsculas y también normaliza las URLs a formato canónico:
> `https://www.instagram.com/{username}/`

---

## Uso

### 1) Ejecución con valores por defecto

Desde la carpeta del repositorio:

```bash
python following_not_followers.py
```

Esto lee `followers_1.json` y `following.json` y escribe:

- `following_not_in_followers.json`

### 2) Ejecución con rutas explícitas

```bash
python following_not_followers.py --followers followers_1.json --following following.json --out salida.json
```

Parámetros:

- `--followers`: ruta al archivo de followers (por defecto: `followers_1.json`)
- `--following`: ruta al archivo de following (por defecto: `following.json`)
- `--out`: ruta del JSON de salida (por defecto: `following_not_in_followers.json`)

---

## Salida

El archivo de salida es un JSON con una lista de objetos:

```json
[
  { "username": "example_user", "href": "https://www.instagram.com/example_user/" }
]
```

- `username`: usuario que está en *following* pero no en *followers*
- `href`: enlace canónico al perfil

---

## Troubleshooting

- **“No existe el archivo de followers/following”**: ejecuta el script desde la carpeta donde están los JSON, o pasa rutas con `--followers` / `--following`.
- **Salida vacía**: significa que no hay diferencia (o que los JSON no corresponden al mismo export/cuenta).
- **Enlaces sin `/_u/`**: es normal; el script los estandariza al formato canónico.

---

## Privacidad

Este repositorio trabaja con datos personales (tu lista de seguidores/seguidos). Evita commitear tus JSON reales si el repositorio es público.
