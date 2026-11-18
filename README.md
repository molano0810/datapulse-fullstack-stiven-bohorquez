# 📊 DataPulse Latam — Plataforma de Inteligencia Macroeconómica y Riesgo País (Backend)

API RESTful desarrollada en **Django** y **Django REST Framework (DRF)** para el monitoreo de indicadores macroeconómicos de Latinoamérica, cálculo automatizado del **Índice de Riesgo País Compuesto (IRPC)**, gestión de portafolios de inversión con simulación de escenarios y sistema de alertas tempranas.

---

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.12
* **Framework Web & API:** Django 6.x + Django REST Framework (DRF)
* **Base de Datos:** PostgreSQL
* **Autenticación y Seguridad:** JSON Web Tokens (`djangorestframework-simplejwt`) con control de acceso basado en roles (`ADMIN`, `ANALISTA`, `VIEWER`)
* **Integraciones Externas:**
  * **World Bank Open Data API** (PIB, Inflación, Desempleo)
  * **ExchangeRate-API** (Tasas de cambio frente al USD y cálculo de variación diaria)

---

## 📁 Arquitectura del Proyecto (`backend/`)

```text
backend/
├── api/
│   ├── management/
│   │   └── commands/
│   │       ├── seed_data.py        # Carga inicial de los 10 países monitoreados en Latam
│   │       └── run_sync.py         # Pipeline automatizado: Banco Mundial + FX + Cálculo IRPC
│   ├── models.py                   # 9 entidades relacionales (Usuario, Pais, Portafolio, IRPC, Alerta, etc.)
│   ├── serializers.py              # Validaciones de negocio y serialización JSON / JWT claims
│   ├── services.py                 # Consumo por lotes (batch) de APIs externas con transacciones atómicas
│   ├── services_irpc.py            # Motor de cálculo ponderado del IRPC y disparador de alertas
│   ├── views.py                    # ViewSets, permisos por rol, simulación, exportación CSV y dashboard
│   ├── urls.py                     # Enrutamiento RESTful de todos los módulos
│   └── admin.py                    # Panel administrativo personalizado
├── config/
│   ├── settings.py                 # Configuración general, PostgreSQL y políticas SIMPLE_JWT
│   └── urls.py                     # Punto de entrada principal de URLs
├── manage.py
└── requirements.txt

⚙️ Instalación y Ejecución Local (Paso a Paso)

1. Clonar el repositorio y preparar el entorno virtual

git clone <URL_DEL_REPOSITORIO>
cd datapulse-fullstack-stiven-bohorquez

python3 -m venv venv
source venv/bin/activate

2. Instalar dependencias

cd backend
pip install -r requirements.txt

3. Configurar variables de entorno

Crea un archivo .env en la raíz del proyecto (datapulse-fullstack-stiven-bohorquez/.env) con las credenciales de PostgreSQL:

SECRET_KEY=tu_clave_secreta_segura
DEBUG=True
DB_NAME=datapulse_db
DB_USER=postgres
DB_PASSWORD=tu_password_postgres
DB_HOST=localhost
DB_PORT=5432

4. Aplicar migraciones y crear superusuario administrador

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

5. Cargar datos semilla y ejecutar sincronización inicial

Ejecuta el comando de sincronización para poblar indicadores macroeconómicos desde el Banco Mundial, tasas de cambio actuales y calcular el IRPC inicial de los 10 países:

python manage.py run_sync

6. Levantar el servidor de desarrollo

python manage.py runserver

La API quedará disponible en http://127.0.0.1:8000/api/ y el panel administrativo en http://127.0.0.1:8000/admin/.


🧠 Lógica de Negocio Implementada
1. Motor de Cálculo del IRPC (services_irpc.py)
El Índice de Riesgo País Compuesto evalúa cada país en una escala de 0 a 100 (donde mayor puntaje representa mayor estabilidad y menor riesgo) mediante tres sub-índices ponderados:

Score Económico (40%): Evalúa PIB per cápita, inflación anual, tasa de desempleo y deuda pública (% del PIB).

Score Cambiario (30%): Analiza la volatilidad (desviación estándar de los últimos 30 días) y la depreciación acumulada frente al USD.

Score de Estabilidad (30%): Evalúa balanza comercial, tendencia de crecimiento interanual del PIB y concentración de indicadores negativos.

Clasificación de Riesgo:

75 - 100: BAJO

50 - 74.99: MODERADO

25 - 49.99: ALTO

0 - 24.99: CRÍTICO


2. Sistema de Alertas Automáticas
Durante la sincronización y el recálculo del IRPC, el sistema genera alertas proactivas:

CRITICAL: IRPC inferior a 25 puntos o inflación superior al 50%.

WARNING: Caída abrupta del IRPC mayor a 15 puntos respecto al período anterior o variación diaria del tipo de cambio superior al 3%.

INFO: Confirmación de actualización exitosa de nuevos datos macroeconómicos.


3. Reglas de Seguridad y Portafolios
Control de Roles:

ADMIN: Acceso total, recálculo manual global del IRPC y consulta de logs de auditoría.

ANALISTA: Creación, edición y simulación de portafolios propios o públicos.

VIEWER: Acceso estrictamente de solo lectura.

Validaciones Financieras: Monto mínimo de $1,000 USD por posición individual y tope máximo acumulado de $50,000,000 USD por portafolio activo.


## 🔌 Documentación de Endpoints REST

Todas las rutas (excepto `/auth/login/`, `/auth/refresh/` y `/auth/register/`) requieren cabecera `Authorization: Bearer <access_token>`.

### 🔐 Autenticación y Usuarios
| Método | Endpoint | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login/` | Autentica credenciales y retorna `access`, `refresh` y datos del usuario | Público |
| `POST` | `/api/auth/refresh/` | Renueva el `access` token usando el `refresh` token | Público |
| `POST` | `/api/auth/register/` | Registro de nuevo usuario en la plataforma | Público |
| `GET` | `/api/auth/me/` | Retorna el perfil del usuario autenticado | Autenticado |

### 🌎 Países e Indicadores
| Método | Endpoint | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/paises/` | Lista países monitoreados (filtros: `region`, `activo`, `search`) | Autenticado |
| `GET` | `/api/paises/{id}/` | Detalle completo de un país | Autenticado |
| `GET` | `/api/paises/{id}/indicadores/` | Histórico macroeconómico (filtros: `tipo`, `anio`) | Autenticado |
| `GET` | `/api/paises/{id}/tipo-cambio/` | Histórico de tasas de cambio (filtros: `fecha_inicio`, `fecha_fin`) | Autenticado |

### 📉 Índice de Riesgo País (IRPC)
| Método | Endpoint | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/riesgo/` | Ranking actual de países con su último IRPC calculado | Autenticado |
| `GET` | `/api/riesgo/{codigo_iso}/` | Detalle vigente del país + últimos 30 registros históricos | Autenticado |
| `GET` | `/api/riesgo/{codigo_iso}/historico/` | Serie histórica filtrable por `fecha_inicio` y `fecha_fin` | Autenticado |
| `POST` | `/api/riesgo/calcular/` | Ejecuta el recálculo global del IRPC para todos los países | Solo `ADMIN` |

### 🚨 Alertas Tempranas
| Método | Endpoint | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/alertas/` | Listado de alertas del usuario y globales (filtros: `leida`, `severidad`, `tipo_alerta`) | Autenticado |
| `GET` | `/api/alertas/resumen/` | Conteo de alertas pendientes agrupadas por severidad y tipo | Autenticado |
| `PUT` | `/api/alertas/{id}/leer/` | Marca una alerta individual como leída | Autenticado |
| `PUT` | `/api/alertas/leer-todas/` | Marca todas las alertas pendientes como leídas | Autenticado |

### 💼 Portafolios de Inversión
| Método | Endpoint | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/portafolios/` | Lista portafolios propios y públicos | Autenticado |
| `POST` | `/api/portafolios/` | Crea un nuevo portafolio | `ADMIN` / `ANALISTA` |
| `POST` | `/api/portafolios/{id}/posiciones/` | Agrega una posición validando límites financieros | `ADMIN` / `ANALISTA` |
| `POST` | `/api/portafolios/{id}/simular/` | Proyecta impacto en el portafolio ante escenarios cambiarios | Autenticado |
| `GET` | `/api/portafolios/{id}/exportar/` | Descarga reporte del portafolio y posiciones en formato `.csv` | Autenticado |

### 📊 Dashboard y Auditoría
| Método | Endpoint | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/dashboard/resumen/` | KPIs ejecutivos, países destacados y distribución por nivel de riesgo | Autenticado |
| `GET` | `/api/logs/` | Registro de auditoría de acciones en el sistema | Solo `ADMIN` |

