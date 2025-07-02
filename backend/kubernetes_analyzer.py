"""
Kubernetes Analyzer Module
Analiza pods, namespaces y estado de contenedores en clústeres de Kubernetes
"""

import re
import uuid
import logging
from typing import List, Dict, Optional, Tuple
from kubernetes import client, config
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class KubernetesAnalyzer:
    """Analizador para clústeres de Kubernetes"""
    
    def __init__(self):
        """Inicializar analizador de Kubernetes"""
        self.v1 = None
        self.current_cluster = None
    
    def connect_to_cluster(self, cluster_name: str) -> bool:
        """
        Conectar al clúster de Kubernetes
        
        Args:
            cluster_name: Nombre del clúster
            
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            # Cargar configuración de kubectl
            config.load_kube_config()
            self.v1 = client.CoreV1Api()
            self.current_cluster = cluster_name
            
            # Probar conexión
            version = self.v1.get_api_versions()
            logger.info(f"✅ Conectado a Kubernetes cluster: {cluster_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conectando a {cluster_name}: {str(e)}")
            return False
    
    def is_valid_uuid(self, namespace_name: str) -> bool:
        """
        Verificar si un nombre de namespace es un UUID válido
        
        Args:
            namespace_name: Nombre del namespace
            
        Returns:
            bool: True si es un UUID válido
        """
        try:
            uuid.UUID(namespace_name)
            return True
        except ValueError:
            return False
    
    def get_uuid_namespaces(self) -> List[str]:
        """
        Obtener lista de namespaces que son UUIDs válidos
        
        Returns:
            List[str]: Lista de namespaces UUID
        """
        try:
            if not self.v1:
                logger.error("❌ No conectado a Kubernetes")
                return []
            
            # Obtener todos los namespaces
            namespaces = self.v1.list_namespace()
            uuid_namespaces = []
            
            for ns in namespaces.items:
                if self.is_valid_uuid(ns.metadata.name):
                    uuid_namespaces.append(ns.metadata.name)
                    logger.debug(f"📋 Namespace UUID encontrado: {ns.metadata.name}")
            
            logger.info(f"📊 Total namespaces UUID: {len(uuid_namespaces)}")
            return uuid_namespaces
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo namespaces: {str(e)}")
            return []
    
    def analyze_namespace_pods(self, namespace: str) -> Dict:
        """
        Analizar todos los pods en un namespace específico
        
        Args:
            namespace: Nombre del namespace
            
        Returns:
            Dict: Análisis completo del namespace
        """
        try:
            if not self.v1:
                logger.error("❌ No conectado a Kubernetes")
                return {}
            
            # Obtener todos los pods del namespace
            pods = self.v1.list_namespaced_pod(namespace=namespace)
            
            analysis = {
                'namespace': namespace,
                'cluster': self.current_cluster,
                'pods': {
                    'running': 0,
                    'pending': 0,
                    'failed': 0,
                    'succeeded': 0,
                    'unknown': 0
                },
                'containers': {
                    'total': 0,
                    'ready': 0,
                    'not_ready': 0,
                    'crash_loop_backoff': 0,
                    'image_pull_backoff': 0,
                    'total_restarts': 0
                },
                'detailed_pods': [],
                'availability_percentage': 0,
                'health_status': 'unknown'
            }
            
            for pod in pods.items:
                pod_info = self._analyze_single_pod(pod)
                analysis['detailed_pods'].append(pod_info)
                
                # Contadores por estado
                phase = pod.status.phase.lower() if pod.status.phase else 'unknown'
                if phase in analysis['pods']:
                    analysis['pods'][phase] += 1
                else:
                    analysis['pods']['unknown'] += 1
                
                # Análisis de contenedores
                if pod.status.container_statuses:
                    for container in pod.status.container_statuses:
                        analysis['containers']['total'] += 1
                        
                        if container.ready:
                            analysis['containers']['ready'] += 1
                        else:
                            analysis['containers']['not_ready'] += 1
                        
                        # Contabilizar reinicios
                        if container.restart_count:
                            analysis['containers']['total_restarts'] += container.restart_count
                        
                        # Detectar problemas específicos
                        if container.state:
                            if (container.state.waiting and 
                                container.state.waiting.reason == 'CrashLoopBackOff'):
                                analysis['containers']['crash_loop_backoff'] += 1
                            elif (container.state.waiting and 
                                  'ImagePull' in container.state.waiting.reason):
                                analysis['containers']['image_pull_backoff'] += 1
            
            # Calcular porcentaje de disponibilidad
            total_pods = len(pods.items)
            running_pods = analysis['pods']['running']
            
            if total_pods > 0:
                analysis['availability_percentage'] = round(
                    (running_pods / total_pods) * 100, 2
                )
            
            # Determinar estado de salud
            analysis['health_status'] = self._determine_health_status(analysis)
            
            logger.info(f"📊 Namespace {namespace}: {total_pods} pods, "
                       f"{analysis['availability_percentage']}% disponibilidad")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analizando namespace {namespace}: {str(e)}")
            return {}
    
    def _analyze_single_pod(self, pod) -> Dict:
        """
        Analizar un pod individual
        
        Args:
            pod: Objeto pod de Kubernetes
            
        Returns:
            Dict: Información detallada del pod
        """
        pod_info = {
            'name': pod.metadata.name,
            'phase': pod.status.phase,
            'ready': False,
            'restarts': 0,
            'age_hours': 0,
            'containers': [],
            'issues': []
        }
        
        # Calcular edad del pod
        if pod.metadata.creation_timestamp:
            now = datetime.now(timezone.utc)
            age = now - pod.metadata.creation_timestamp
            pod_info['age_hours'] = round(age.total_seconds() / 3600, 2)
        
        # Analizar contenedores
        if pod.status.container_statuses:
            ready_containers = 0
            total_containers = len(pod.status.container_statuses)
            
            for container in pod.status.container_statuses:
                container_info = {
                    'name': container.name,
                    'ready': container.ready,
                    'restart_count': container.restart_count or 0,
                    'state': 'running' if container.ready else 'not_ready'
                }
                
                # Acumular reinicios
                pod_info['restarts'] += container_info['restart_count']
                
                # Detectar problemas
                if container.state:
                    if container.state.waiting:
                        reason = container.state.waiting.reason
                        container_info['state'] = reason
                        
                        if reason == 'CrashLoopBackOff':
                            pod_info['issues'].append(f"Container {container.name}: CrashLoopBackOff")
                        elif 'ImagePull' in reason:
                            pod_info['issues'].append(f"Container {container.name}: {reason}")
                        elif 'Error' in reason:
                            pod_info['issues'].append(f"Container {container.name}: {reason}")
                    
                    elif container.state.terminated:
                        reason = container.state.terminated.reason
                        if reason != 'Completed':
                            pod_info['issues'].append(f"Container {container.name}: Terminated ({reason})")
                
                if container.ready:
                    ready_containers += 1
                
                pod_info['containers'].append(container_info)
            
            # Pod está listo si todos los contenedores están listos
            pod_info['ready'] = ready_containers == total_containers
        
        # Detectar reinicios excesivos
        if pod_info['restarts'] > 10:
            pod_info['issues'].append(f"Excessive restarts: {pod_info['restarts']}")
        
        return pod_info
    
    def _determine_health_status(self, analysis: Dict) -> str:
        """
        Determinar el estado de salud basado en el análisis
        
        Args:
            analysis: Datos del análisis del namespace
            
        Returns:
            str: Estado de salud ('healthy', 'warning', 'critical')
        """
        availability = analysis['availability_percentage']
        crash_loops = analysis['containers']['crash_loop_backoff']
        failed_pods = analysis['pods']['failed']
        
        # Criterios para estado crítico
        if availability < 80 or crash_loops > 0 or failed_pods > 0:
            return 'critical'
        
        # Criterios para advertencia
        elif availability < 95 or analysis['containers']['total_restarts'] > 20:
            return 'warning'
        
        # Estado saludable
        else:
            return 'healthy'
    
    def analyze_all_clusters(self, clusters: List[Dict], azure_client) -> List[Dict]:
        """
        Analizar todos los clústeres proporcionados
        
        Args:
            clusters: Lista de clústeres a analizar
            azure_client: Cliente de Azure para obtener credenciales
            
        Returns:
            List[Dict]: Análisis de todos los clústeres
        """
        results = []
        
        for cluster in clusters:
            cluster_name = cluster['name']
            resource_group = cluster['resource_group']
            
            logger.info(f"🔍 Analizando clúster: {cluster_name}")
            
            # Obtener credenciales para el clúster
            if not azure_client.get_cluster_credentials(cluster_name, resource_group):
                logger.error(f"❌ No se pudieron obtener credenciales para {cluster_name}")
                continue
            
            # Conectar al clúster
            if not self.connect_to_cluster(cluster_name):
                logger.error(f"❌ No se pudo conectar a {cluster_name}")
                continue
            
            # Obtener namespaces UUID
            uuid_namespaces = self.get_uuid_namespaces()
            
            cluster_analysis = {
                'cluster_info': cluster,
                'namespaces': [],
                'summary': {
                    'total_namespaces': len(uuid_namespaces),
                    'healthy': 0,
                    'warning': 0,
                    'critical': 0
                }
            }
            
            # Analizar cada namespace
            for namespace in uuid_namespaces:
                namespace_analysis = self.analyze_namespace_pods(namespace)
                if namespace_analysis:
                    cluster_analysis['namespaces'].append(namespace_analysis)
                    
                    # Contabilizar por estado de salud
                    health_status = namespace_analysis.get('health_status', 'unknown')
                    if health_status in cluster_analysis['summary']:
                        cluster_analysis['summary'][health_status] += 1
            
            results.append(cluster_analysis)
            logger.info(f"✅ Completado análisis de {cluster_name}: "
                       f"{len(uuid_namespaces)} namespaces")
        
        return results

def create_kubernetes_analyzer() -> KubernetesAnalyzer:
    """Factory function para crear un analizador de Kubernetes"""
    return KubernetesAnalyzer() 