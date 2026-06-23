# db_batch_search


##  DESPUÉS (versión mejorada)

### Caso 1: Búsqueda exitosa

#### En Consola (Logs):
```
======================================================================
 INICIANDO BÚSQUEDA BATCH
======================================================================
   Tipo: fuzzy
   Índice: essays_index
   Total párrafos: 10
   Idioma: en
   Workers: 20
   Primer párrafo: Climate change is affecting agriculture worldwide...
======================================================================

======================================================================
  BÚSQUEDA COMPLETADA
======================================================================
   Total párrafos: 10
   Con matches: 7 (70.0%)
   Sin matches: 3 (30.0%)
   Score promedio: 0.6523

    Top 3 Matches:
      [1] Score: 0.7800 | Title: Environmental Essay
      [2] Score: 0.6500 | Title: Green Energy Paper
      [3] Score: 0.5900 | Title: Climate Research Document
======================================================================
```

#### En JSON (Response):
```json
{
  "success": true,
  "result": [
    {
      "original": "Climate change is affecting...",
      "matches": [
        {
          "title": "Environmental Essay",
          "author": "John Doe",
          "score": 25.3,
          "normalized_score": 0.78
        }
      ]
    },
    // ... más resultados ...
  ],
  "stats": {
    "total_paragraphs": 10,
    "with_matches": 7,
    "without_matches": 3,
    "avg_score": 0.6523,
    "match_rate": 70.0
  }
}
```

**Ventajas:**
- ✅ Ves el progreso en tiempo real
- ✅ Estadísticas agregadas útiles
- ✅ Sabes exactamente qué está pasando
- ✅ Top 3 matches inmediatamente visibles

---

### Caso 2: Error de validación


#### :
```
❌ No se proporcionaron textos para buscar
```

```json
{
  "success": false,
  "error": "No se encontraron párrafos para buscar (campo 'texts' vacío o ausente)",
  "result": []
}
```

---

### Caso 3: Error de conexión


#### :
```
❌ Error de conexión: HTTPConnectionPool(host='127.0.0.1', port=5000)...
```

```json
{
  "success": false,
  "error": "Error de conexión al servidor de búsqueda",
  "details": "HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded...",
  "result": []
}
```

---

### Caso 4: Timeout



####  ( mensaje, pero con logging):
```
❌ Timeout: La petición tardó más de 5 minutos
```

```json
{
  "success": false,
  "error": "Timeout: La petición tardó más de 5 minutos",
  "result": []
}
```

---

##  Ventajas de la Nueva Versión

|         Aspecto        | Antes | Después |
|------------------------|-----------------|---------|
| **Validación**         |  Robusta con filtrado |
| **Logging**            | ❌ Ninguno | ✅ Detallado y estructurado |
| **Estadísticas**       | ❌ No | ✅ Sí (agregadas y útiles) |
| **Errores**            | ⚠️ Genéricos | ✅ Específicos con detalles |
| **Debugging**          | 🔍 Difícil | ✅ Fácil con logs |
| **Top Matches**        | ❌ No visible | ✅ En logs inmediatamente |
| **Validación previa**  | ❌ No | ✅ Función `validate_es_document()` |

---

## 🎯 Uso en tu Código

### En `upload_analysis()`:

```python
if use_db_search:
    # Preparar documento
    es_document = {
        "texts": paragraphs,
        "language": language,
        "metadata": {
            "index_name": "essays_index",
            "theme": theme,
            "max_workers": min(32, len(paragraphs) * 2)
        }
    }
    
    # Validar ANTES de buscar (opcional pero recomendado)
    is_valid, error_msg = validate_es_document(es_document)
    if not is_valid:
        print(f"❌ Documento inválido: {error_msg}")
        results_db = {"success": False, "error": error_msg, "result": []}
    else:
        # Buscar con logging automático
        results_db = db_batch_search(es_document, search_type=findex_subcheck)
        
        # Usar estadísticas
        if results_db["success"]:
            stats = results_db["stats"]
            print(f"✅ {stats['with_matches']}/{stats['total_paragraphs']} párrafos con matches")
            print(f"   Match rate: {stats['match_rate']}%")
            print(f"   Avg score: {stats['avg_score']}")
```