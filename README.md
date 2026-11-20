# 📊 DataPulse Latam — Plataforma de Inteligencia Macroeconómica y Riesgo País (Fullstack)

Aplicación web **Fullstack** desarrollada con **Django REST Framework** y **Angular 21** para el monitoreo de indicadores macroeconómicos de Latinoamérica, cálculo automatizado del **Índice de Riesgo País Compuesto (IRPC)**, gestión de portafolios de inversión con simulación de escenarios cambiarios y sistema de alertas tempranas con control de acceso basado en roles (**RBAC**).

---

## 🌐 Despliegue en Producción

| Componente | Plataforma | URL Pública |
| :--- | :--- | :--- |
| **Frontend SPA (Angular 21)** | Vercel | https://datapulse-fullstack-stiven-bohorque.vercel.app |
| **Frontend (Alias alternativo)** | Vercel | https://datapulse-fullstack-stiven-bohorquez-molano1.vercel.app |
| **Backend API REST (Django + DRF)** | Render | https://datapulse-fullstack-stiven-bohorquez.onrender.com/api/ |
| **Panel Administrativo Django** | Render | https://datapulse-fullstack-stiven-bohorquez.onrender.com/admin/ |
| **Video Demostrativo (5–8 min)** | Youtube | https://youtu.be/5VbLPMW0hiI?si=jIUXYVzyFV9DImDV |

> **Nota sobre arranque en frío (Render Free Tier):** Si el servicio backend lleva más de 15 minutos sin tráfico, la primera petición puede tardar ~30–40 segundos mientras la instancia se activa.

---

## 🔑 Credenciales de Acceso en Producción (RBAC)

Puedes ingresar directamente a la aplicación desplegada en **Vercel** (`https://datapulse-fullstack-stiven-bohorque.vercel.app`) o autenticar peticiones contra la API en **Render** utilizando cualquiera de los siguientes usuarios precargados en producción:

| Rol | Correo Electrónico (Usuario) | Contraseña | Permisos y Alcance |
| :--- | :--- | :--- | :--- |
| **ADMIN** | `admin@datapulse.com` | `DataPulse2026!` | Acceso total: recálculo global del IRPC, consulta de logs de auditoría, gestión completa de portafolios y alertas. |
| **ANALISTA** | `analista@datapulse.com` | `DataPulse2026!` | Consulta de indicadores, creación/edición/simulación de portafolios propios o públicos y gestión de alertas. |
| **VIEWER** | `viewer@datapulse.com` | `DataPulse2026!` | Acceso estrictamente de solo lectura (acciones de escritura y recálculo deshabilitadas). |

---

## 🛠️ Stack Tecnológico

### Backend
- **Lenguaje y Framework:** Python 3.12 + Django + Django REST Framework (DRF)
- **Base de Datos:** PostgreSQL (`dj-database-url`)
- **Autenticación y Seguridad:** JSON Web Tokens (`djangorestframework-simplejwt`), `django-cors-headers`, permisos personalizados por rol (`ADMIN`, `ANALISTA`, `VIEWER`)
- **Servidor y Estáticos:** Gunicorn + WhiteNoise
- **Integraciones Externas (ETL):**
  - **World Bank Open Data API** (PIB, PIB per cápita, inflación, desempleo, deuda pública, balanza comercial)
  - **ExchangeRate-API** (tasas de cambio frente al USD y cálculo de variación diaria)

### Frontend
- **Framework:** Angular 21 (Standalone Components, Routing con Lazy Loading, Reactive Forms)
- **Seguridad y Estado:** Route Guards (`authGuard`), Functional HTTP Interceptor (`authInterceptor`) para inyección automática de `Bearer <token>` y manejo de sesión
- **Estilos:** SCSS modular responsivo

---

## 📁 Arquitectura del Monorepo

```text
datapulse-fullstack-stiven-bohorquez/
├── backend/
│   ├── api/
│   │   ├── management/commands/
│   │   │   ├── seed_data.py             # Carga inicial de los 10 países monitoreados y usuarios RBAC
│   │   │   ├── run_sync.py              # Pipeline ETL: Banco Mundial + FX + Cálculo IRPC
│   │   │   ├── seed_tipo_cambio.py      # Histórico de tasas de cambio (30 días)
│   │   │   ├── seed_riesgo_historico.py # Serie histórica de evaluaciones IRPC
│   │   │   ├── calcular_riesgo.py       # Recálculo batch del motor IRPC
│   │   │   └── seed_portafolios.py      # Portafolios de inversión y posiciones iniciales
│   │   ├── models.py                    # 9 entidades relacionales (Usuario, Pais, Portafolio, IRPC, Alerta, etc.)
│   │   ├── serializers.py               # Validaciones de negocio y serialización JSON / JWT claims
│   │   ├── services.py                  # Consumo por lotes (batch) de APIs externas con transacciones atómicas
│   │   ├── services_irpc.py             # Motor de cálculo ponderado del IRPC y disparador de alertas
│   │   ├── views.py                     # ViewSets, permisos por rol, simulación, exportación CSV y dashboard
│   │   ├── urls.py                      # Enrutamiento RESTful de todos los módulos
│   │   └── admin.py                     # Panel administrativo personalizado
│   ├── config/
│   │   ├── settings.py                  # Configuración general, PostgreSQL, CORS y políticas SIMPLE_JWT
│   │   └── urls.py                      # Punto de entrada principal de URLs
│   ├── build.sh                         # Script de despliegue continuo en Render (migrate + seeds)
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/                    # Guards, interceptores JWT, modelos TypeScript y servicios API/Auth
│   │   │   ├── features/                # Módulos: Login, Dashboard, Países, Motor IRPC, Alertas y Portafolios
│   │   │   └── shared/                  # Navbar y componentes compartidos
│   │   └── environments/                # Configuración de URLs de API (desarrollo y producción)
│   ├── angular.json
│   ├── package.json
│   └── vercel.json                      # Rewrites SPA para rutas de Angular en Vercel
├── .env.example                         # Plantilla de variables de entorno
└── README.md
```

---

## ⚙️ Instalación y Ejecución Local (Paso a Paso)

### 1. Clonar el repositorio
```bash
git clone [https://github.com/molano0810/datapulse-fullstack-stiven-bohorquez.git](https://github.com/molano0810/datapulse-fullstack-stiven-bohorquez.git)
cd datapulse-fullstack-stiven-bohorquez
```

### 2. Configurar y levantar el Backend (Django)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

cp .env.example .env
# Edita .env con tus credenciales locales de PostgreSQL (DB_NAME, DB_USER, DB_PASSWORD)

cd backend
python manage.py migrate
python manage.py seed_data
python manage.py run_sync
python manage.py seed_tipo_cambio
python manage.py seed_riesgo_historico
python manage.py calcular_riesgo
python manage.py seed_portafolios
python manage.py runserver
```
La API quedará disponible en `http://127.0.0.1:8000/api/` y el panel administrativo en `http://127.0.0.1:8000/admin/`.

### 3. Configurar y levantar el Frontend (Angular)
En una segunda terminal desde la raíz del repositorio:
```bash
cd frontend
npm install
npm start
```
La aplicación web quedará disponible en `http://localhost:4200`.

---

## 🧠 Lógica de Negocio Implementada

### 1. Motor de Cálculo del IRPC (`services_irpc.py`)
El **Índice de Riesgo País Compuesto** evalúa cada país en una escala de `0` a `100` (donde mayor puntaje representa mayor estabilidad y menor riesgo) mediante tres sub-índices ponderados:

- **Score Económico (40%):** Evalúa PIB per cápita, inflación anual, tasa de desempleo y deuda pública (`%` del PIB).
- **Score Cambiario (30%):** Analiza la volatilidad (desviación estándar de los últimos 30 días) y la depreciación acumulada frente al USD.
- **Score de Estabilidad (30%):** Evalúa balanza comercial, tendencia de crecimiento interanual del PIB y concentración de indicadores negativos.

**Clasificación de Riesgo:**
- `75 - 100`: **BAJO**
- `50 - 74.99`: **MODERADO**
- `25 - 49.99`: **ALTO**
- `0 - 24.99`: **CRÍTICO**

### 2. Sistema de Alertas Automáticas
Durante la sincronización y el recálculo del IRPC, el sistema genera alertas proactivas:
- **CRITICAL:** IRPC inferior a `25` puntos o inflación superior al `50%`.
- **WARNING:** Caída abrupta del IRPC mayor a `15` puntos respecto al período anterior o variación diaria del tipo de cambio superior al `3%`.
- **INFO:** Confirmación de actualización exitosa de nuevos datos macroeconómicos.

### 3. Reglas de Seguridad y Portafolios
- **Control de Roles (RBAC):**
  - `ADMIN`: Acceso total, recálculo manual global del IRPC y consulta de logs de auditoría.
  - `ANALISTA`: Creación, edición y simulación de portafolios propios o públicos.
  - `VIEWER`: Acceso estrictamente de solo lectura.
- **Validaciones Financieras:** Monto mínimo de **$1,000 USD** por posición individual y tope máximo acumulado de **$50,000,000 USD** por portafolio activo.

---

## 🔌 Documentación de Endpoints REST

Todas las rutas (excepto `/api/auth/login/`, `/api/auth/refresh/` y `/api/auth/register/`) requieren cabecera `Authorization: Bearer <access_token>`.

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

---

## 👤 Autor

**Stiven Bohorquez Molano** — Prueba Técnica Fullstack DataPulse Latam (2026)
