# 👑 Royal Handsome — Tienda Virtual

Tienda online con probador virtual de ropa usando IA (IDM-VTON via Replicate).

**Colección 2026 · Authentic Quality · Finest Apparel · London, England**

## Sucursales
- 🇨🇴 Bogotá, Colombia (Casa Matriz)
- 🇵🇪 Lima, Perú
- 🇺🇸 Miami, USA

## Tecnología
- Frontend: HTML + Tailwind CSS (sin frameworks)
- Backend: Python 3 (stdlib únicamente, sin dependencias)
- IA: IDM-VTON via Replicate API
- Hosting: Render.com

## Ejecutar localmente

```bash
python3 server.py
```
Abrir: http://localhost:8080

## Variables de entorno

| Variable | Descripción |
|---|---|
| `PORT` | Puerto del servidor (Render lo asigna automáticamente) |

El token de Replicate se ingresa desde la interfaz del usuario, no es una variable de entorno del servidor.

## Archivos principales

| Archivo | Descripción |
|---|---|
| `index.html` | Tienda completa (imágenes embebidas como base64) |
| `server.py` | Servidor Python + proxy para Replicate |
| `catalog.json` | Catálogo de productos con inventario (para integración AI) |
| `render.yaml` | Configuración de deploy en Render.com |
| `rh-assets/` | Imágenes PNG del catálogo |
