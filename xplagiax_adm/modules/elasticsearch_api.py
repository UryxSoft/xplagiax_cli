from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from elasticsearch import Elasticsearch
import json
from datetime import datetime, timedelta
import structlog
import os
from collections import defaultdict
import numpy as np

# Configurar logging
logger = structlog.get_logger()

# Configuración de Elasticsearch
ELASTICSEARCH_CONFIG = {
    'host': os.getenv('ELASTICSEARCH_HOST', 'localhost'),
    'port': int(os.getenv('ELASTICSEARCH_PORT', 9200)),
    'timeout': 30
}

def get_elasticsearch_client():
    """Obtener cliente de Elasticsearch"""
    try:
        es = Elasticsearch(
            [f"http://{ELASTICSEARCH_CONFIG['host']}:{ELASTICSEARCH_CONFIG['port']}"],
            request_timeout=ELASTICSEARCH_CONFIG['timeout']
        )
        return es
    except Exception as e:
        logger.error("elasticsearch_connection_failed", error=str(e))
        return None

def format_field_value(value):
    """Formatear valores de campos para visualización"""
    if isinstance(value, (list, dict)):
        return json.dumps(value, default=str)[:100] + "..." if len(str(value)) > 100 else json.dumps(value, default=str)
    elif isinstance(value, (int, float)):
        return value
    else:
        return str(value)[:200] + "..." if len(str(value)) > 200 else str(value)

@app.route('/api/elasticsearch/indices')
def get_elasticsearch_indices():
    """Obtener lista de todos los índices en Elasticsearch"""
    try:
        es = get_elasticsearch_client()
        if not es:
            return jsonify({'error': 'No se puede conectar a Elasticsearch'}), 500
        
        # Obtener estadísticas de índices
        indices_stats = es.indices.stats()
        indices_info = es.indices.get_mapping()
        
        indices_list = []
        
        for index_name, stats in indices_stats['indices'].items():
            # Obtener información del mapping
            mapping_info = indices_info.get(index_name, {}).get('mappings', {})
            properties = mapping_info.get('properties', {})
            
            # Calcular estadísticas
            doc_count = stats['total']['docs']['count']
            size_bytes = stats['total']['store']['size_in_bytes']
            size_mb = round(size_bytes / (1024 * 1024), 2)
            
            indices_list.append({
                'name': index_name,
                'doc_count': doc_count,
                'size_mb': size_mb,
                'size_bytes': size_bytes,
                'fields_count': len(properties),
                'fields': list(properties.keys())[:20],  # Primeros 20 campos
                'health': 'green'  # Simplificado por ahora
            })
        
        # Ordenar por número de documentos
        indices_list.sort(key=lambda x: x['doc_count'], reverse=True)
        
        logger.info("elasticsearch_indices_retrieved", total_indices=len(indices_list))
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'total_indices': len(indices_list),
            'indices': indices_list
        })
        
    except Exception as e:
        logger.error("get_indices_failed", error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/elasticsearch/index/<index_name>/data')
def get_index_data(index_name):
    """Obtener datos de un índice específico para visualización"""
    try:
        es = get_elasticsearch_client()
        if not es:
            return jsonify({'error': 'No se puede conectar a Elasticsearch'}), 500
        
        # Parámetros de consulta
        size = request.args.get('size', 1000, type=int)
        from_param = request.args.get('from', 0, type=int)
        search_query = request.args.get('q', '*')
        
        # Construir query
        query = {
            "query": {
                "query_string": {
                    "query": search_query
                }
            },
            "size": min(size, 10000),  # Máximo 10k documentos
            "from": from_param,
            "sort": [
                {"_score": {"order": "desc"}},
                {"_id": {"order": "asc"}}
            ]
        }
        
        # Ejecutar búsqueda
        response = es.search(index=index_name, body=query)
        
        # Procesar resultados
        documents = []
        for hit in response['hits']['hits']:
            doc = {
                'id': hit['_id'],
                'score': hit['_score'],
                'source': hit['_source']
            }
            documents.append(doc)
        
        # Obtener estadísticas del índice
        stats = es.indices.stats(index=index_name)
        index_stats = stats['indices'][index_name]['total']
        
        logger.info("index_data_retrieved", 
                   index=index_name, 
                   documents=len(documents), 
                   total_hits=response['hits']['total']['value'])
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'index': index_name,
            'query': search_query,
            'total_hits': response['hits']['total']['value'],
            'returned_docs': len(documents),
            'documents': documents,
            'stats': {
                'doc_count': index_stats['docs']['count'],
                'size_bytes': index_stats['store']['size_in_bytes'],
                'size_mb': round(index_stats['store']['size_in_bytes'] / (1024 * 1024), 2)
            }
        })
        
    except Exception as e:
        logger.error("get_index_data_failed", index=index_name, error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/elasticsearch/index/<index_name>/graph')
def get_index_graph_data(index_name):
    """Obtener datos del índice formateados para gráfica de red"""
    try:
        es = get_elasticsearch_client()
        if not es:
            return jsonify({'error': 'No se puede conectar a Elasticsearch'}), 500
        
        # Parámetros
        max_nodes = request.args.get('max_nodes', 500, type=int)
        relationship_field = request.args.get('relationship_field', 'tags')  # Campo para relaciones
        
        # Obtener muestra de documentos
        query = {
            "query": {"match_all": {}},
            "size": min(max_nodes, 1000),
            "_source": True
        }
        
        response = es.search(index=index_name, body=query)
        
        nodes = []
        links = []
        categories = {}
        
        # Procesar documentos para crear nodos
        for i, hit in enumerate(response['hits']['hits']):
            doc = hit['_source']
            doc_id = hit['_id']
            
            # Determinar categoría basada en algún campo
            category = 'default'
            if 'type' in doc:
                category = str(doc['type'])
            elif 'category' in doc:
                category = str(doc['category'])
            elif '_index' in hit:
                category = hit['_index']
            
            if category not in categories:
                categories[category] = len(categories)
            
            # Crear nodo
            node = {
                'id': doc_id,
                'name': doc_id[:20],  # Nombre corto
                'symbolSize': min(30, max(10, len(str(doc)) / 100)),  # Tamaño basado en contenido
                'category': categories[category],
                'value': len(str(doc)),
                'draggable': True,
                'itemStyle': {
                    'color': f"hsl({(categories[category] * 137.5) % 360}, 70%, 60%)"
                },
                'label': {
                    'show': True,
                    'fontSize': 12
                },
                'data': doc  # Datos completos para tooltip
            }
            nodes.append(node)
            
            # Crear enlaces basados en campos relacionales
            if relationship_field in doc:
                rel_data = doc[relationship_field]
                if isinstance(rel_data, list):
                    for rel_item in rel_data[:5]:  # Máximo 5 relaciones por nodo
                        # Buscar otros nodos con esta relación
                        for j, other_hit in enumerate(response['hits']['hits']):
                            if i != j and relationship_field in other_hit['_source']:
                                other_rel_data = other_hit['_source'][relationship_field]
                                if isinstance(other_rel_data, list) and rel_item in other_rel_data:
                                    links.append({
                                        'source': doc_id,
                                        'target': other_hit['_id'],
                                        'value': 1,
                                        'lineStyle': {
                                            'width': 2,
                                            'opacity': 0.6
                                        }
                                    })
        
        # Si no hay suficientes enlaces, crear algunos basados en similitud de campos
        if len(links) < len(nodes) * 0.1:  # Menos del 10% de conectividad
            logger.info("creating_similarity_links", current_links=len(links))
            
            for i, node1 in enumerate(nodes[:100]):  # Limitar para performance
                for j, node2 in enumerate(nodes[i+1:i+11]):  # Comparar con siguientes 10
                    if i != j:
                        # Calcular similitud básica
                        doc1 = node1['data']
                        doc2 = node2['data']
                        
                        common_fields = set(doc1.keys()) & set(doc2.keys())
                        if len(common_fields) > 2:  # Si tienen campos en común
                            links.append({
                                'source': node1['id'],
                                'target': node2['id'],
                                'value': len(common_fields),
                                'lineStyle': {
                                    'width': 1,
                                    'opacity': 0.3,
                                    'type': 'dashed'
                                }
                            })
        
        # Preparar categorías para ECharts
        chart_categories = []
        for cat_name, cat_id in categories.items():
            chart_categories.append({
                'name': cat_name,
                'itemStyle': {
                    'color': f"hsl({(cat_id * 137.5) % 360}, 70%, 60%)"
                }
            })
        
        logger.info("graph_data_generated", 
                   index=index_name, 
                   nodes=len(nodes), 
                   links=len(links),
                   categories=len(categories))
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'index': index_name,
            'nodes': nodes,
            'links': links,
            'categories': chart_categories,
            'stats': {
                'total_nodes': len(nodes),
                'total_links': len(links),
                'total_categories': len(categories),
                'connectivity': round(len(links) / len(nodes), 2) if nodes else 0
            }
        })
        
    except Exception as e:
        logger.error("get_graph_data_failed", index=index_name, error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/elasticsearch/index/<index_name>/aggregations')
def get_index_aggregations(index_name):
    """Obtener agregaciones de un índice para gráficas estadísticas"""
    try:
        es = get_elasticsearch_client()
        if not es:
            return jsonify({'error': 'No se puede conectar a Elasticsearch'}), 500
        
        # Obtener mapping para identificar campos numéricos y de fecha
        mapping = es.indices.get_mapping(index=index_name)
        properties = mapping[index_name]['mappings'].get('properties', {})
        
        # Identificar campos por tipo
        date_fields = []
        numeric_fields = []
        keyword_fields = []
        
        for field_name, field_config in properties.items():
            field_type = field_config.get('type', 'text')
            if field_type in ['date']:
                date_fields.append(field_name)
            elif field_type in ['integer', 'long', 'float', 'double']:
                numeric_fields.append(field_name)
            elif field_type in ['keyword']:
                keyword_fields.append(field_name)
        
        # Construir agregaciones dinámicas
        aggs = {}
        
        # Agregación por fechas (histograma temporal)
        if date_fields:
            aggs['date_histogram'] = {
                'date_histogram': {
                    'field': date_fields[0],
                    'calendar_interval': 'day',
                    'min_doc_count': 1
                }
            }
        
        # Top términos para campos keyword
        for field in keyword_fields[:3]:  # Máximo 3 campos keyword
            aggs[f'top_{field}'] = {
                'terms': {
                    'field': field,
                    'size': 10
                }
            }
        
        # Estadísticas para campos numéricos
        for field in numeric_fields[:3]:  # Máximo 3 campos numéricos
            aggs[f'stats_{field}'] = {
                'stats': {
                    'field': field
                }
            }
        
        # Ejecutar agregaciones
        query = {
            'query': {'match_all': {}},
            'size': 0,  # Solo queremos agregaciones
            'aggs': aggs
        }
        
        response = es.search(index=index_name, body=query)
        
        # Procesar resultados de agregaciones
        processed_aggs = {}
        
        for agg_name, agg_result in response['aggregations'].items():
            if 'buckets' in agg_result:
                # Es una agregación de términos o histograma
                processed_aggs[agg_name] = {
                    'type': 'buckets',
                    'data': [
                        {
                            'key': bucket['key'],
                            'doc_count': bucket['doc_count'],
                            'key_as_string': bucket.get('key_as_string', str(bucket['key']))
                        }
                        for bucket in agg_result['buckets']
                    ]
                }
            else:
                # Es una agregación de estadísticas
                processed_aggs[agg_name] = {
                    'type': 'stats',
                    'data': agg_result
                }
        
        logger.info("aggregations_retrieved", 
                   index=index_name, 
                   aggregations=len(processed_aggs))
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'index': index_name,
            'field_types': {
                'date_fields': date_fields,
                'numeric_fields': numeric_fields,
                'keyword_fields': keyword_fields
            },
            'aggregations': processed_aggs
        })
        
    except Exception as e:
        logger.error("get_aggregations_failed", index=index_name, error=str(e))
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)