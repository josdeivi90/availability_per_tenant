"""
Data Processor Module
Procesa datos de Kubernetes y PagerDuty, aplica modelo de inferencia y genera status.json
"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class DataProcessor:
    """Procesador de datos para KubeHealth Dashboard"""
    
    def __init__(self, tenants_file_path: str = "tenants.json"):
        """
        Inicializar procesador de datos
        
        Args:
            tenants_file_path: Ruta al archivo de mapeo de tenants
        """
        self.tenants_file_path = tenants_file_path
        self.tenant_mapping = self._load_tenant_mapping()
    
    def _load_tenant_mapping(self) -> Dict[str, str]:
        """
        Cargar el mapeo de UUIDs a nombres de organizaciones
        
        Returns:
            Dict[str, str]: Mapeo UUID -> nombre de organización
        """
        try:
            tenants_path = Path(self.tenants_file_path)
            if not tenants_path.exists():
                logger.warning(f"⚠️ Archivo de tenants no encontrado: {self.tenants_file_path}")
                return {}
            
            with open(tenants_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convertir a diccionario plano UUID -> nombre
            mapping = {}
            for tenant in data.get('tenants', []):
                uuid = tenant.get('uuid')
                name = tenant.get('organization_name', tenant.get('name', ''))
                if uuid and name:
                    mapping[uuid] = name
            
            logger.info(f"📋 Cargado mapeo de {len(mapping)} tenants")
            return mapping
            
        except Exception as e:
            logger.error(f"❌ Error cargando mapeo de tenants: {str(e)}")
            return {}
    
    def get_organization_name(self, namespace_uuid: str) -> str:
        """
        Obtener el nombre de la organización para un UUID de namespace
        
        Args:
            namespace_uuid: UUID del namespace
            
        Returns:
            str: Nombre de la organización o UUID si no se encuentra
        """
        return self.tenant_mapping.get(namespace_uuid, namespace_uuid)
    
    def process_cluster_data(self, 
                           cluster_analysis: List[Dict], 
                           pagerduty_correlations: Dict[str, List[Dict]]) -> Dict:
        """
        Procesar datos de análisis de clústeres y correlaciones de PagerDuty
        
        Args:
            cluster_analysis: Análisis de clústeres de Kubernetes
            pagerduty_correlations: Correlaciones de incidentes por namespace
            
        Returns:
            Dict: Datos procesados listos para el frontend
        """
        try:
            # Estructura base del resultado
            processed_data = {
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "overall_status": "unknown",
                "summary": {
                    "total_clusters": len(cluster_analysis),
                    "total_namespaces_monitored": 0,
                    "pods_running": 0,
                    "pods_with_issues": 0,
                    "active_incidents": 0,
                    "availability_average": 0
                },
                "clusters": [],
                "health_distribution": {
                    "healthy": 0,
                    "warning": 0,
                    "critical": 0
                },
                "historical_data": {
                    "timestamps": [],
                    "availability_history": [],
                    "incident_history": []
                }
            }
            
            total_availability = 0
            namespace_count = 0
            
            # Procesar cada clúster
            for cluster_data in cluster_analysis:
                cluster_info = self._process_single_cluster(
                    cluster_data, 
                    pagerduty_correlations
                )
                processed_data["clusters"].append(cluster_info)
                
                # Acumular estadísticas generales
                for namespace in cluster_info["namespaces"]:
                    namespace_count += 1
                    total_availability += namespace["availability_percentage"]
                    
                    # Contabilizar pods
                    pods = namespace["pods"]
                    processed_data["summary"]["pods_running"] += pods["running"]
                    processed_data["summary"]["pods_with_issues"] += (
                        pods["pending"] + pods["failed"]
                    )
                    
                    # Contabilizar incidentes activos
                    active_incidents = [
                        inc for inc in namespace["related_incidents"]
                        if inc["status"] in ["triggered", "acknowledged"]
                    ]
                    processed_data["summary"]["active_incidents"] += len(active_incidents)
                    
                    # Distribución de salud
                    health_status = namespace["status"]
                    if health_status in processed_data["health_distribution"]:
                        processed_data["health_distribution"][health_status] += 1
            
            # Calcular estadísticas finales
            processed_data["summary"]["total_namespaces_monitored"] = namespace_count
            
            if namespace_count > 0:
                processed_data["summary"]["availability_average"] = round(
                    total_availability / namespace_count, 2
                )
            
            # Determinar estado general
            processed_data["overall_status"] = self._determine_overall_status(
                processed_data
            )
            
            # Generar datos históricos (placeholder por ahora)
            processed_data["historical_data"] = self._generate_historical_placeholder()
            
            logger.info(f"✅ Procesados datos de {namespace_count} namespaces "
                       f"en {len(cluster_analysis)} clústeres")
            
            return processed_data
            
        except Exception as e:
            logger.error(f"❌ Error procesando datos: {str(e)}")
            return self._generate_error_response(str(e))
    
    def _process_single_cluster(self, 
                              cluster_data: Dict, 
                              pagerduty_correlations: Dict[str, List[Dict]]) -> Dict:
        """
        Procesar datos de un clúster individual
        
        Args:
            cluster_data: Datos del análisis del clúster
            pagerduty_correlations: Correlaciones de incidentes
            
        Returns:
            Dict: Datos procesados del clúster
        """
        cluster_info = cluster_data.get("cluster_info", {})
        namespaces_data = cluster_data.get("namespaces", [])
        
        processed_cluster = {
            "name": cluster_info.get("name", "unknown"),
            "location": cluster_info.get("location", ""),
            "kubernetes_version": cluster_info.get("kubernetes_version", ""),
            "status": "unknown",
            "namespaces": []
        }
        
        # Contadores para determinar estado del clúster
        health_counts = {"healthy": 0, "warning": 0, "critical": 0}
        
        # Procesar cada namespace
        for namespace_data in namespaces_data:
            namespace_uuid = namespace_data.get("namespace", "")
            org_name = self.get_organization_name(namespace_uuid)
            
            # Obtener incidentes relacionados
            related_incidents = pagerduty_correlations.get(namespace_uuid, [])
            
            processed_namespace = {
                "uuid": namespace_uuid,
                "organization_name": org_name,
                "status": namespace_data.get("health_status", "unknown"),
                "availability_percentage": namespace_data.get("availability_percentage", 0),
                "pods": namespace_data.get("pods", {}),
                "containers": namespace_data.get("containers", {}),
                "related_incidents": related_incidents,
                "issues": self._extract_namespace_issues(namespace_data),
                "last_analyzed": datetime.now(timezone.utc).isoformat()
            }
            
            # Contabilizar estado de salud
            health_status = processed_namespace["status"]
            if health_status in health_counts:
                health_counts[health_status] += 1
            
            processed_cluster["namespaces"].append(processed_namespace)
        
        # Determinar estado del clúster
        processed_cluster["status"] = self._determine_cluster_status(health_counts)
        
        return processed_cluster
    
    def _extract_namespace_issues(self, namespace_data: Dict) -> List[str]:
        """
        Extraer lista de problemas detectados en el namespace
        
        Args:
            namespace_data: Datos del análisis del namespace
            
        Returns:
            List[str]: Lista de problemas identificados
        """
        issues = []
        
        containers = namespace_data.get("containers", {})
        pods = namespace_data.get("pods", {})
        
        # Problemas de contenedores
        if containers.get("crash_loop_backoff", 0) > 0:
            issues.append(f"{containers['crash_loop_backoff']} contenedores en CrashLoopBackOff")
        
        if containers.get("image_pull_backoff", 0) > 0:
            issues.append(f"{containers['image_pull_backoff']} contenedores con errores de imagen")
        
        if containers.get("total_restarts", 0) > 20:
            issues.append(f"Reinicios excesivos: {containers['total_restarts']} total")
        
        # Problemas de pods
        if pods.get("failed", 0) > 0:
            issues.append(f"{pods['failed']} pods fallidos")
        
        if pods.get("pending", 0) > 0:
            issues.append(f"{pods['pending']} pods pendientes")
        
        # Problema de disponibilidad
        availability = namespace_data.get("availability_percentage", 100)
        if availability < 95:
            issues.append(f"Disponibilidad baja: {availability}%")
        
        return issues
    
    def _determine_cluster_status(self, health_counts: Dict[str, int]) -> str:
        """
        Determinar estado de salud de un clúster basado en sus namespaces
        
        Args:
            health_counts: Contadores de estado de salud
            
        Returns:
            str: Estado del clúster
        """
        total = sum(health_counts.values())
        if total == 0:
            return "unknown"
        
        critical_ratio = health_counts["critical"] / total
        warning_ratio = health_counts["warning"] / total
        
        if critical_ratio > 0.1:  # Más del 10% crítico
            return "critical"
        elif warning_ratio > 0.3 or critical_ratio > 0:  # Más del 30% advertencia o alguno crítico
            return "warning"
        else:
            return "healthy"
    
    def _determine_overall_status(self, processed_data: Dict) -> str:
        """
        Determinar estado general del sistema
        
        Args:
            processed_data: Datos procesados del sistema
            
        Returns:
            str: Estado general
        """
        summary = processed_data["summary"]
        health_dist = processed_data["health_distribution"]
        
        total_namespaces = summary["total_namespaces_monitored"]
        if total_namespaces == 0:
            return "unknown"
        
        # Criterios para estado crítico
        critical_ratio = health_dist["critical"] / total_namespaces
        avg_availability = summary["availability_average"]
        active_incidents = summary["active_incidents"]
        
        if critical_ratio > 0.05 or avg_availability < 90 or active_incidents > 5:
            return "critical"
        
        # Criterios para advertencia
        warning_ratio = health_dist["warning"] / total_namespaces
        if warning_ratio > 0.2 or avg_availability < 95 or active_incidents > 0:
            return "warning"
        
        return "healthy"
    
    def _generate_historical_placeholder(self) -> Dict:
        """
        Generar datos históricos de placeholder
        
        Returns:
            Dict: Datos históricos simulados
        """
        # Por ahora, generar datos de ejemplo
        # En el futuro, esto se cargará de un almacén de datos históricos
        timestamps = []
        availability_history = []
        incident_history = []
        
        # Generar 48 puntos de datos (últimas 24 horas, cada 30 min)
        now = datetime.now(timezone.utc)
        for i in range(48, 0, -1):
            timestamp = now - timedelta(minutes=i * 30)  # 30 minutos atrás
            timestamps.append(timestamp.isoformat())
            
            # Simular datos históricos con algo de variación
            base_availability = 95 + (i % 5)  # Variación simple
            availability_history.append(base_availability)
            
            # Simular incidentes ocasionales
            incidents = 1 if i % 12 == 0 else 0  # Incidente cada 6 horas
            incident_history.append(incidents)
        
        return {
            "timestamps": timestamps,
            "availability_history": availability_history,
            "incident_history": incident_history
        }
    
    def _generate_error_response(self, error_message: str) -> Dict:
        """
        Generar respuesta de error estándar
        
        Args:
            error_message: Mensaje de error
            
        Returns:
            Dict: Respuesta de error
        """
        return {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "overall_status": "error",
            "error": error_message,
            "summary": {
                "total_clusters": 0,
                "total_namespaces_monitored": 0,
                "pods_running": 0,
                "pods_with_issues": 0,
                "active_incidents": 0,
                "availability_average": 0
            },
            "clusters": [],
            "health_distribution": {
                "healthy": 0,
                "warning": 0,
                "critical": 0
            },
            "historical_data": {
                "timestamps": [],
                "availability_history": [],
                "incident_history": []
            }
        }
    
    def save_status_json(self, processed_data: Dict, output_path: str = "status.json") -> bool:
        """
        Guardar los datos procesados en un archivo JSON
        
        Args:
            processed_data: Datos procesados
            output_path: Ruta del archivo de salida
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            output_file = Path(output_path)
            
            # Crear directorio si no existe
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Guardar archivo
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Status JSON guardado en: {output_file.absolute()}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando status JSON: {str(e)}")
            return False
    
    def get_tenant_mapping(self) -> Dict[str, str]:
        """
        Obtener el mapeo de tenants cargado
        
        Returns:
            Dict[str, str]: Mapeo UUID -> nombre de organización
        """
        return self.tenant_mapping.copy()

def create_data_processor(tenants_file_path: str = "tenants.json") -> DataProcessor:
    """
    Factory function para crear un procesador de datos
    
    Args:
        tenants_file_path: Ruta al archivo de mapeo de tenants
        
    Returns:
        DataProcessor: Procesador configurado
    """
    return DataProcessor(tenants_file_path) 