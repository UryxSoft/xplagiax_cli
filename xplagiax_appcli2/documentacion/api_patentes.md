# API de Detección de Infracción de Patentes

## Resumen

El módulo `genuine_service` proporciona endpoints para detectar posibles infracciones de patentes analizando documentos propuestos, comparando texto e imágenes con patentes existentes.

---

## Endpoints Disponibles

### 1. `POST /analyze_patent_infringement`

**Propósito:** Analiza un documento completo para detectar posibles infracciones de patentes.

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "paragraphs": [
    [1, 1, "Climate change remains one of the greatest challenges..."],
    [1, 2, "Artificial intelligence and data analytics also play..."],
    [1, 3, "In conclusion, while technology has contributed..."]
  ],
  "metadata": {
    "format": "PDF 1.7",
    "title": "Climate Change and Technology",
    "author": "Ruben Eduardo Gonzalez Nova",
    "creationDate": "D:20260114133855-04'00'"
  },
  "idiom": "en",
  "images": [
    {"page": 1, "url": "data:image/png;base64,...", "description": "Solar panel diagram"}
  ],
  "pages": 1,
  "theme": "Technology"
}
```

**Respuesta exitosa (200):**
```json
{
  "status": "success",
  "document_info": {
    "author": "Ruben Eduardo Gonzalez Nova",
    "title": "Climate Change and Technology",
    "pages": 1,
    "total_paragraphs": 3,
    "paragraphs_analyzed": 3,
    "language": "en",
    "creation_date": "D:20260114133855-04'00'"
  },
  "patent_matches": [
    {
      "page_number": 1,
      "paragraph_number": 2,
      "paragraph_text": "Artificial intelligence and data analytics...",
      "patent_title": "AI-Based Environmental Monitoring System",
      "patent_id": "US20210123456A1",
      "publication_date": "2021-05-15",
      "inventor": "John Doe",
      "assignee": "Tech Corp",
      "patent_pdf_url": "https://patents.google.com/patent/US20210123456A1",
      "similarity_percentage": 87.5,
      "match_type": "text"
    }
  ],
  "image_matches": [
    {
      "document_image_index": 0,
      "document_image_page": 1,
      "patent_id": "US20200987654A1",
      "patent_title": "Solar Panel Design Patent",
      "matched_image_url": "https://...",
      "similarity_percentage": 92.3
    }
  ],
  "summary": {
    "total_text_matches": 2,
    "total_image_matches": 1,
    "highest_similarity": 92.3,
    "risk_level": "HIGH",
    "recommendation": "⚠️ RIESGO ALTO: Se encontraron múltiples coincidencias..."
  },
  "api_usage": {
    "serpapi": 5,
    "zenserp": 0
  }
}
```

---

### 2. `POST /search_similar_patents`

**Propósito:** Busca patentes sobre el mismo tema que el documento propuesto.

**Body:**
```json
{
  "theme": "Climate Change Technology",
  "keywords": ["AI", "environmental monitoring", "renewable energy"],
  "paragraphs": [],
  "language": "en",
  "num_results": 20
}
```

**Respuesta exitosa (200):**
```json
{
  "status": "success",
  "query_used": "Climate Change Technology AI environmental monitoring",
  "patents": [
    {
      "title": "AI-Based Climate Prediction System",
      "patent_id": "US20210123456A1",
      "publication_date": "2021-05-15",
      "inventor": "Jane Smith",
      "assignee": "Green Tech Inc",
      "snippet": "A system for predicting climate changes using...",
      "link": "https://patents.google.com/patent/US20210123456A1",
      "pdf_url": "https://..."
    }
  ],
  "total_found": 20,
  "api_usage": {...}
}
```

---

### 3. `POST /compare_document_with_patent`

**Propósito:** Compara un documento específico con una patente conocida.

**Body:**
```json
{
  "paragraphs": [
    [1, 1, "Climate change remains one of the greatest challenges..."],
    [1, 2, "Artificial intelligence and data analytics..."]
  ],
  "patent_id": "US20210123456A1"
}
```

**Respuesta exitosa (200):**
```json
{
  "status": "success",
  "patent_info": {
    "patent_id": "US20210123456A1",
    "title": "AI-Based Environmental Monitoring System",
    "inventor": "John Doe",
    "assignee": "Tech Corp"
  },
  "comparisons": [
    {
      "page_number": 1,
      "paragraph_number": 2,
      "document_text": "Artificial intelligence and data analytics...",
      "similarity_percentage": 75.5
    }
  ],
  "overall_similarity": 45.2,
  "summary": {
    "paragraphs_analyzed": 10,
    "high_similarity_count": 2,
    "medium_similarity_count": 3,
    "low_similarity_count": 5
  },
  "api_usage": {...}
}
```

---

### 4. `POST /search_patents_by_text`

**Propósito:** Búsqueda simple de patentes por texto.

**Body:**
```json
{
  "query": "artificial intelligence climate change",
  "num_results": 10
}
```

---

### 5. `POST /search_patents_by_image`

**Propósito:** Búsqueda de patentes por imagen (reverse image search).

**Form Data:**
- `file`: Archivo de imagen
- O `image_url`: URL de la imagen
- `num_results`: Número de resultados (default: 10)

---

### 6. `GET /get_patent_details/<patent_id>`

**Propósito:** Obtiene detalles completos de una patente específica.

**Ejemplo:**
```
GET /get_patent_details/US20210123456A1
```

---

### 7. `GET /api_usage_status`

**Propósito:** Muestra estado de uso de las APIs (SerpAPI y Zenserp).

**Respuesta:**
```json
{
  "status": {
    "serpapi": {
      "used": 15,
      "limit": 250,
      "remaining": 235,
      "percent_used": 6.0
    },
    "zenserp": {
      "used": 2,
      "limit": 50,
      "remaining": 48,
      "percent_used": 4.0
    }
  },
  "last_reset": "2026-01"
}
```

---

## Niveles de Riesgo

| Nivel | Umbral | Descripción |
|-------|--------|-------------|
| `LOW` | < 50% similitud | Coincidencias menores, documento parece original |
| `MEDIUM` | 50-70% similitud | Algunas coincidencias, revisar patentes identificadas |
| `HIGH` | 70-85% similitud | Múltiples coincidencias, consultar con experto |
| `CRITICAL` | > 85% similitud | Coincidencias muy significativas, consultar abogado |

---

## Configuración Requerida

### Variables de Entorno

```bash
export SERPAPI_KEY="tu_serpapi_key"
export ZENSERP_KEY="tu_zenserp_key"
```

### Límites de API (Tier Gratuito)

| API | Límite Mensual |
|-----|----------------|
| SerpAPI | 250 búsquedas |
| Zenserp | 50 búsquedas |

---

## Dependencias

```
sentence-transformers  # Para similitud semántica
pillow                 # Para procesamiento de imágenes
requests               # Para llamadas a APIs
```

---

## Límites de Entrada

| Parámetro | Límite |
|-----------|--------|
| Párrafos | Máximo 100 |
| Imágenes | Máximo 20 |
| Párrafos analizados | Máximo 20 por solicitud |
| Keywords extraídos | Máximo 15 |

---

## Ejemplos de Uso con cURL

### Analizar documento
```bash
curl -X POST http://localhost:5000/x_genuine/analyze_patent_infringement \
  -H "Content-Type: application/json" \
  -d '{
    "paragraphs": [[1, 1, "Your document text here..."]],
    "metadata": {"author": "Author Name"},
    "idiom": "en",
    "pages": 1
  }'
```

### Buscar patentes similares
```bash
curl -X POST http://localhost:5000/x_genuine/search_similar_patents \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "Climate Change",
    "keywords": ["AI", "monitoring"],
    "num_results": 10
  }'
```

### Comparar con patente específica
```bash
curl -X POST http://localhost:5000/x_genuine/compare_document_with_patent \
  -H "Content-Type: application/json" \
  -d '{
    "paragraphs": [[1, 1, "Your document text..."]],
    "patent_id": "US20210123456A1"
  }'
```

---

## Fecha de Actualización
2026-01-18
