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