# DRIFT

DRIFT es un comparador de videojuegos que permite descubrir títulos y consultar
sus precios entre plataformas. El corte vertical implementado busca juegos en
Steam por medio de una API FastAPI y los presenta en una interfaz Next.js.

## Arquitectura

El proyecto usa arquitectura hexagonal (Ports and Adapters). El dominio y los
casos de uso no dependen de React, FastAPI, HTTPX, Steam ni de detalles HTTP;
los puertos expresan sus contratos y los adaptadores traducen cada tecnología
externa.

```text
Frontend React -> caso de uso -> puerto -> adaptador HTTP -> API FastAPI
                                                          |
FastAPI -> caso de uso -> puerto -> adaptador Steam ------+
```

Consulta la descripción de cada bloque de código, el flujo de datos y la
justificación detallada en [docs/guia_codigo.md](docs/guia_codigo.md).

## Organización del proyecto

```text
DRIFT/
├── .github/
│   └── workflows/
│       └── ci.yml                     # pruebas y smoke tests en GitHub Actions
├── backend/
│   ├── app/
│   │   ├── domain/
│   │   │   ├── model/game.py          # entidad Game
│   │   │   └── ports/game_repository.py
│   │   ├── application/
│   │   │   └── usecases/search_games.py
│   │   ├── infrastructure/
│   │   │   ├── external/steam/steam_game_repository.py
│   │   │   └── persistence/in_memory_game_repository.py
│   │   └── main.py                    # API FastAPI y composition root
│   ├── tests/test_health.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── layout.js
│   │   └── page.js
│   ├── domain/model/Game.js
│   ├── application/
│   │   ├── ports/GameSearchPort.js
│   │   └── usecases/searchGames.js
│   ├── infrastructure/http/FastApiGameRepository.js
│   ├── ui/components/
│   │   ├── DriftHome.js
│   │   └── DriftHome.module.css
│   ├── package.json
│   └── next.config.js
└── docs/
    ├── guia_codigo.md                  # guía técnica del código actual
    ├── adr/                            # decisiones arquitectónicas
    ├── arc42/                          # documentación arc42
    └── c4/                             # diagramas de contexto y contenedores
```

## Requisitos

- Python 3.12 o superior
- Node.js 22 o superior

## Ejecución local

En una terminal, instala las dependencias y ejecuta la API:

```bash
cd backend
python -m pip install fastapi==0.141.1 httpx==0.28.1 pytest uvicorn==0.52.4
python -m uvicorn app.main:app --reload --port 8000
```

En otra terminal, inicia el frontend:

```bash
cd frontend
npm ci
npm run dev
```


## Pruebas automatizadas

### Backend

```bash
cd backend
python -m pytest tests -q
```

Las pruebas validan el endpoint de salud y el corte vertical de búsqueda. La
API de Steam se simula durante el test de búsqueda para conservar resultados
deterministas.

### Frontend

```bash
cd frontend
npm run build
```

La compilación asegura que la aplicación Next.js y sus límites cliente/servidor
sean válidos.

## Integración continua

El workflow [.github/workflows/ci.yml](.github/workflows/ci.yml) se ejecuta en
`push` y `pull_request` sobre `master` y tiene dos trabajos:

1. **Pruebas del backend:** instala las dependencias y ejecuta `pytest`.
2. **Frontend conectado a la API:** inicia FastAPI en `127.0.0.1:8000`, comprueba
   el endpoint de salud, compila Next.js con
   `NEXT_PUBLIC_DRIFT_API_URL=http://127.0.0.1:8000`, sirve el frontend y comprueba
   que la portada responde en `127.0.0.1:3000`.

Así CI valida que la aplicación funciona con una API real levantada en el
runner, sin hacer que sus pruebas dependan de la disponibilidad de Steam.

## Documentación adicional

- [Guía del código](docs/guia_codigo.md)
- [ADR de arquitectura](docs/adr/0002-arquitectura-base.md)
- [Contexto C4](docs/c4/contexto.md)
- [Contenedores C4](docs/c4/contenedores.md)
- [Documentación arc42](docs/arc42)

## Equipo

- Mauricio Fernández Espinosa
- Jerry Buelvas Mejía
- Luis Pérez Diaz
- Joshua Reyes Leones
