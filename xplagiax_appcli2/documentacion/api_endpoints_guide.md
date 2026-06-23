# 📋 Guía de Uso - API de Detección de Infracción de Patentes

## Formato de Entrada del Documento

```json
{
  "paragraphs": [
    [page_number, paragraph_number, "texto del párrafo"],
    [1, 1, "Primer párrafo..."],
    [1, 2, "Segundo párrafo..."]
  ],
  "metadata": {
    "format": "PDF 1.7",
    "title": "Título del documento",
    "author": "Autor",
    "creationDate": "D:20260114133855-04'00'"
  },
  "idiom": "en",
  "images": ["base64_image_data..."],
  "urls": [],
  "pages": 1
}
```

---

## 🔍 Endpoint Principal: Análisis Completo

### `POST /x_genuine/full_patent_analysis`

**Descripción**: Ejecuta todos los analizadores y genera dashboard de riesgo completo.

**Request:**
```json
{
  "document_text": "Climate change remains one of the greatest challenges facing humanity. Rising global temperatures, melting glaciers, and extreme weather events remind us that our planet's balance is at risk. However, technology offers innovative solutions to combat and adapt to these changes. Artificial intelligence and data analytics also play a major role. Through predictive modeling, AI helps scientists forecast environmental changes, monitor deforestation, and optimize energy use.",
  "patent_text": "A method for predicting environmental changes using artificial intelligence comprising: collecting climate data from multiple sensors; processing said data using machine learning models; generating predictions for temperature and weather patterns.",
  "filing_date": "2020-01-15",
  "include_prior_art": true,
  "include_biotech": true,
  "include_chemical": true
}
```

**Response:**
```json
{
  "status": "success",
  "risk_dashboard": {
    "document_id": "analyzed_document",
    "analysis_date": "2026-01-18T01:39:00.000000",
    "overall_risk": {
      "score": 67.5,
      "level": "HIGH"
    },
    "category_breakdown": [
      {
        "category": "claims",
        "score": 75.0,
        "level": "HIGH",
        "details": "3 claims con alta probabilidad de infracción",
        "matched_items": 3,
        "total_items": 4,
        "weight": 0.35
      },
      {
        "category": "text_similarity",
        "score": 62.5,
        "level": "HIGH",
        "details": "Similitud máxima: 62.5%",
        "matched_items": 5,
        "total_items": 8,
        "weight": 0.25
      }
    ],
    "recommendations": [
      "⚠️ URGENTE: Consultar con abogado de propiedad intelectual antes de proceder",
      "Considerar rediseño de elementos identificados como infractores",
      "Revisar claims 3 identificados - considerar modificar implementación"
    ],
    "summary": "Análisis de 2 patentes completado. Riesgo global: 67.5% (HIGH). Áreas de mayor riesgo: claims, text_similarity."
  },
  "performance": {
    "total_time_ms": 1234.56
  }
}
```

---

## 📊 Endpoints Individuales

### 1. Análisis de Infracción de Patentes

#### `POST /x_genuine/analyze_patent_infringement`

**Request:**
```json
{
  "paragraphs": [
    [1, 1, "Gildan Internal Document  Climate Change and the Role of Technology  Climate change remains one of the greatest challenges facing humanity."],
    [1, 2, "Artificial intelligence and data analytics also play a major role. Through predictive modeling, AI helps scientists forecast environmental changes."],
    [1, 3, "In conclusion, while technology has contributed to environmental problems in the past, it now provides the tools to solve them."]
  ],
  "metadata": {
    "author": "Ruben Eduardo Gonzalez Nova",
    "creationDate": "D:20260114133855-04'00'"
  },
  "idiom": "en",
  "images": []
}
```

**Response Esperado:**
```json
{
  "status": "success",
  "analysis_id": "a1b2c3d4-5678-90ab-cdef",
  "document_info": {
    "author": "Ruben Eduardo Gonzalez Nova",
    "total_paragraphs": 3,
    "total_pages": 1,
    "language": "en"
  },
  "patent_matches": [
    {
      "page_number": 1,
      "paragraph_number": 2,
      "paragraph_text": "Artificial intelligence and data analytics also play a major role...",
      "patent": {
        "id": "US10123456B2",
        "title": "System and Method for Environmental Prediction Using AI",
        "publication_date": "2019-05-15",
        "author": "John Smith, Jane Doe",
        "assignee": "GreenTech Corporation",
        "similarity_percentage": 78.5,
        "pdf_url": "https://patents.google.com/patent/US10123456B2/en?oq=US10123456B2",
        "claims_matched": [1, 3, 7],
        "citation": {
          "column": 4,
          "lines": "15-32"
        }
      },
      "matched_text": "A method for predicting environmental changes using artificial intelligence and machine learning models to forecast weather patterns.",
      "match_type": "semantic"
    },
    {
      "page_number": 1,
      "paragraph_number": 1,
      "paragraph_text": "Climate change remains one of the greatest challenges...",
      "patent": {
        "id": "EP3456789A1",
        "title": "Climate Monitoring and Analysis System",
        "publication_date": "2018-11-20",
        "author": "Maria Garcia",
        "assignee": "European Climate Institute",
        "similarity_percentage": 65.2,
        "pdf_url": "https://worldwide.espacenet.com/patent/search/family/EP3456789A1",
        "claims_matched": [2],
        "citation": {
          "column": 2,
          "lines": "5-18"
        }
      },
      "matched_text": "Systems for monitoring global temperature changes and climate patterns.",
      "match_type": "semantic"
    }
  ],
  "image_matches": [],
  "summary": {
    "total_matches": 2,
    "highest_similarity": 78.5,
    "risk_level": "HIGH",
    "paragraphs_flagged": [1, 2]
  }
}
```

---

### 2. Análisis de Claims

#### `POST /x_genuine/analyze_claims`

**Request:**
```json
{
  "patent_text": "Claims:\n1. A method for predicting environmental changes comprising:\n   (a) collecting climate data from sensors;\n   (b) processing data using machine learning;\n   (c) generating temperature predictions.\n2. The method of claim 1, wherein the machine learning comprises neural networks.\n3. A system for implementing the method of claim 1.",
  "document_text": "Our system collects climate data from multiple sensors distributed globally. We process this data using advanced machine learning algorithms to generate accurate temperature predictions for the next 30 days.",
  "patent_id": "US10123456B2"
}
```

**Response:**
```json
{
  "status": "success",
  "patent_id": "US10123456B2",
  "total_claims": 3,
  "independent_claims": 2,
  "dependent_claims": 1,
  "overall_risk": 83.33,
  "highest_match_claim": 1,
  "claim_matches": [
    {
      "claim_number": 1,
      "claim_type": "method",
      "matched_elements": [
        {
          "element_text": "collecting climate data from sensors",
          "element_type": "step",
          "matched_keywords": ["climate", "data", "sensors", "collecting"],
          "match_ratio": 100.0
        },
        {
          "element_text": "processing data using machine learning",
          "element_type": "step",
          "matched_keywords": ["processing", "data", "machine", "learning"],
          "match_ratio": 100.0
        },
        {
          "element_text": "generating temperature predictions",
          "element_type": "step",
          "matched_keywords": ["generating", "temperature", "predictions"],
          "match_ratio": 100.0
        }
      ],
      "total_elements": 3,
      "matched_count": 3,
      "match_percentage": 100.0,
      "infringement_likely": true,
      "citation": {
        "claim": "Claim 1",
        "preamble": "A method for predicting environmental changes comprising:"
      }
    }
  ]
}
```

---

### 3. Fingerprint / Similitud Rápida

#### `POST /x_genuine/fingerprint_compare`

**Request:**
```json
{
  "text1": "Climate change remains one of the greatest challenges facing humanity. Rising global temperatures and melting glaciers remind us that our planet's balance is at risk.",
  "text2": "Global warming is among the most significant challenges for mankind. Increasing temperatures worldwide and melting ice caps show that Earth's equilibrium is threatened."
}
```

**Response:**
```json
{
  "status": "success",
  "similarity_percent": 72.34,
  "simhash_distance": 8,
  "is_near_duplicate": false,
  "interpretation": "HIGH: Alta similitud, posible plagio"
}
```

---

### 4. Búsqueda de Prior Art

#### `POST /x_genuine/search_prior_art`

**Request:**
```json
{
  "patent_text": "A method for predicting environmental changes using artificial intelligence comprising collecting climate data and processing using machine learning models.",
  "filing_date": "2020-01-15"
}
```

**Response:**
```json
{
  "status": "success",
  "query_terms": ["predicting", "environmental", "artificial", "intelligence", "climate", "machine", "learning"],
  "filing_date": "2020-01-15",
  "total_found": 25,
  "prior_art_count": 18,
  "potentially_invalidating": [
    {
      "title": "Machine Learning Approaches for Climate Prediction",
      "authors": ["J. Smith", "A. Johnson"],
      "publication_date": "2018-06-15",
      "source": "semantic_scholar",
      "url": "https://www.semanticscholar.org/paper/abc123",
      "abstract": "This paper presents novel machine learning techniques for predicting climate changes...",
      "is_prior_art": true,
      "relevance_score": 0.85
    },
    {
      "title": "AI-Based Environmental Monitoring Systems",
      "authors": ["M. Garcia"],
      "publication_date": "2019-02-20",
      "source": "arxiv",
      "url": "https://arxiv.org/abs/1902.12345",
      "abstract": "We propose an artificial intelligence system for monitoring environmental changes...",
      "is_prior_art": true,
      "relevance_score": 0.78
    }
  ],
  "timeline": {
    "2017": 3,
    "2018": 8,
    "2019": 7,
    "2020": 5,
    "2021": 2
  }
}
```

---

### 5. Análisis de Secuencias Biotecnológicas

#### `POST /x_genuine/analyze_biotech_sequences`

**Request:**
```json
{
  "text": "The invention relates to a nucleic acid sequence SEQ ID NO: 1: ATGGCCGGTTTAAACCCGGGAAATTTCCC. The protein sequence identified is MKVIFVLGGPGKGTQCEKIVQKYGYTHLSTGDVRREAIS.",
  "analyze_dna": true,
  "analyze_proteins": true,
  "run_blast": false
}
```

**Response:**
```json
{
  "status": "success",
  "biotech_context_detected": true,
  "dna_sequences": [
    {
      "sequence": "ATGGCCGGTTTAAACCCGGGAAATTTCCC",
      "length": 30,
      "gc_content": 53.33,
      "page_number": 1,
      "paragraph_number": 1,
      "seq_id": "1"
    }
  ],
  "protein_sequences": [
    {
      "sequence": "MKVIFVLGGPGKGTQCEKIVQKYGYTHLSTGDVRREAIS",
      "length": 40,
      "page_number": 1,
      "paragraph_number": 1
    }
  ],
  "blast_results": [],
  "summary": {
    "total_dna_sequences": 1,
    "total_protein_sequences": 1,
    "blast_hits_found": 0
  },
  "performance": {
    "total_time_ms": 45.23
  }
}
```

---

### 6. Análisis de Fórmulas Químicas

#### `POST /x_genuine/analyze_chemical_formulas`

**Request:**
```json
{
  "paragraphs": [
    [1, 1, "The compound H2O is essential. We also used NaCl and C6H12O6 (glucose) in our experiments."]
  ],
  "generate_images": true
}
```

**Response:**
```json
{
  "status": "success",
  "total_formulas_detected": 3,
  "formulas": ["H2O", "NaCl", "C6H12O6"],
  "detailed_matches": [
    {
      "match": {
        "formula": "H2O",
        "page_number": 1,
        "paragraph_number": 1,
        "is_valid": true
      },
      "analysis": {
        "formula": "H2O",
        "is_valid": true,
        "atom_counts": {"H": 2, "O": 1},
        "compounds": [
          {
            "formula_input": "H2O",
            "smiles": "O",
            "canonical_formula": "H2O",
            "molecular_weight": 18.02,
            "iupac_name": "oxidane",
            "synonyms": ["Water", "Dihydrogen monoxide"],
            "structure_image_base64": "data:image/png;base64,iVBORw0..."
          }
        ]
      }
    }
  ],
  "performance": {
    "total_time_ms": 234.56
  }
}
```

---

### 7. Dashboard de Riesgo

#### `POST /x_genuine/risk_dashboard`

**Request:**
```json
{
  "document_id": "DOC-2026-001",
  "claims_result": {
    "claim_matches": [
      {"infringement_likely": true},
      {"infringement_likely": true},
      {"infringement_likely": false}
    ]
  },
  "fingerprint_result": {
    "similarity_percent": 72.5,
    "is_near_duplicate": false
  },
  "biotech_result": {
    "summary": {
      "total_dna_sequences": 2,
      "total_protein_sequences": 1,
      "blast_hits_found": 1
    }
  },
  "prior_art_result": {
    "prior_art_count": 5,
    "potentially_invalidating": [
      {"title": "Prior Paper 1"},
      {"title": "Prior Paper 2"}
    ]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "document_id": "DOC-2026-001",
  "analysis_date": "2026-01-18T01:39:00.000000",
  "overall_risk": {
    "score": 65.8,
    "level": "HIGH"
  },
  "category_breakdown": [
    {
      "category": "claims",
      "score": 66.67,
      "level": "HIGH",
      "details": "2 claims con alta probabilidad de infracción",
      "matched_items": 2,
      "total_items": 3,
      "weight": 0.35
    },
    {
      "category": "text_similarity",
      "score": 72.5,
      "level": "HIGH",
      "details": "Fingerprint similarity: 72.5%",
      "matched_items": 72,
      "total_items": 100,
      "weight": 0.25
    },
    {
      "category": "biotech",
      "score": 33.33,
      "level": "LOW",
      "details": "1 secuencias con hits en bases de datos",
      "matched_items": 1,
      "total_items": 3,
      "weight": 0.10
    },
    {
      "category": "prior_art",
      "score": 60.0,
      "level": "MODERATE",
      "details": "2 publicaciones potencialmente invalidantes",
      "matched_items": 2,
      "total_items": 5,
      "weight": 0.05
    }
  ],
  "recommendations": [
    "⚠️ URGENTE: Consultar con abogado de propiedad intelectual antes de proceder",
    "Considerar rediseño de elementos identificados como infractores",
    "Revisar claims 2 identificados - considerar modificar implementación",
    "Alto overlap textual - reescribir descripciones técnicas",
    "💡 2 publicaciones de prior art pueden servir como defensa"
  ],
  "summary": "Análisis de 0 patentes completado. Riesgo global: 65.8% (HIGH). Áreas de mayor riesgo: claims, text_similarity.",
  "processing_time_ms": 12.34
}
```

---

## 📁 Formato de Respuesta de Coincidencia de Patentes

Cada coincidencia de patente incluye:

```json
{
  "page_number": 1,
  "paragraph_number": 2,
  "paragraph_text": "Texto original del documento...",
  "patent": {
    "id": "US10123456B2",
    "title": "Título de la Patente",
    "publication_date": "2019-05-15",
    "author": "Nombre del Inventor",
    "assignee": "Empresa Titular",
    "similarity_percentage": 78.5,
    "pdf_url": "https://patents.google.com/patent/US10123456B2",
    "claims_matched": [1, 3, 7],
    "citation": {
      "column": 4,
      "lines": "15-32"
    }
  },
  "image_matches": [
    {
      "document_image_index": 0,
      "patent_image_url": "https://patentimages.storage.googleapis.com/...",
      "similarity_score": 85.2,
      "match_type": "structural"
    }
  ],
  "matched_text": "Texto de la patente que coincide...",
  "match_type": "semantic"
}
```

---

## 🔧 Códigos de Estado

| Código | Significado |
|--------|-------------|
| 200 | Éxito |
| 400 | Error en parámetros de entrada |
| 503 | Servicio no disponible (analizador no inicializado) |
| 500 | Error interno del servidor |

---

## 📊 Niveles de Riesgo

| Nivel | Score | Acción Recomendada |
|-------|-------|-------------------|
| CRITICAL | 80-100% | 🔴 Detener inmediatamente. Consultar abogado. |
| HIGH | 60-79% | 🟠 Revisar urgente. Posible infracción. |
| MODERATE | 40-59% | 🟡 Revisar elementos específicos. |
| LOW | 20-39% | 🟢 Bajo riesgo. Monitorear. |
| MINIMAL | 0-19% | ✅ Sin riesgo significativo. |
