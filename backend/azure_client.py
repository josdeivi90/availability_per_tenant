"""
Azure Client Module
Maneja la conexión a Azure y el descubrimiento de clústeres AKS
"""

import os
import subprocess
import json
import logging
from typing import List, Dict, Optional
from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.resource import ResourceManagementClient

logger = logging.getLogger(__name__)

class AzureClient:
    """Cliente para interactuar con Azure AKS"""
    
    def __init__(self):
        """Inicializar cliente Azure"""
        self.credential = None
        self.subscription_id = None
        self.container_client = None
        self.resource_client = None
    
    def authenticate(self) -> bool:
        """
        Autenticar con Azure usando Azure CLI
        Returns:
            bool: True si la autenticación fue exitosa
        """
        try:
            # Intentar usar credenciales de Azure CLI primero
            self.credential = AzureCliCredential()
            
            # Obtener subscription ID actual
            result = subprocess.run(
                ['az', 'account', 'show', '--query', 'id', '-o', 'tsv'],
                capture_output=True,
                text=True,
                check=True
            )
            self.subscription_id = result.stdout.strip()
            
            # Inicializar clientes
            self.container_client = ContainerServiceClient(
                self.credential, 
                self.subscription_id
            )
            self.resource_client = ResourceManagementClient(
                self.credential,
                self.subscription_id
            )
            
            logger.info(f"✅ Autenticado en Azure - Subscription: {self.subscription_id}")
            return True
            
        except subprocess.CalledProcessError:
            logger.error("❌ Error: Azure CLI no está autenticado. Ejecuta 'az login'")
            return False
        except Exception as e:
            logger.error(f"❌ Error de autenticación Azure: {str(e)}")
            return False
    
    def discover_aks_clusters(self, cluster_prefix: str = "ftdsp-prod-aks-cluster-") -> List[Dict]:
        """
        Descubrir clústeres AKS que coincidan con el prefijo
        
        Args:
            cluster_prefix: Prefijo para filtrar clústeres
            
        Returns:
            List[Dict]: Lista de clústeres encontrados
        """
        try:
            if not self.container_client:
                logger.error("❌ Cliente Azure no inicializado")
                return []
            
            clusters = []
            
            # Listar todos los clústeres AKS en la suscripción
            logger.info("🔍 Buscando clústeres AKS...")
            
            all_clusters = list(self.container_client.managed_clusters.list())
            
            for cluster in all_clusters:
                if cluster.name.startswith(cluster_prefix):
                    cluster_info = {
                        'name': cluster.name,
                        'resource_group': cluster.id.split('/')[4],
                        'location': cluster.location,
                        'status': cluster.provisioning_state,
                        'kubernetes_version': cluster.kubernetes_version,
                        'node_count': sum(
                            pool.count for pool in cluster.agent_pool_profiles
                        ) if cluster.agent_pool_profiles else 0
                    }
                    clusters.append(cluster_info)
                    logger.info(f"✅ Encontrado: {cluster.name} ({cluster_info['resource_group']})")
            
            logger.info(f"📊 Total clústeres encontrados: {len(clusters)}")
            return clusters
            
        except Exception as e:
            logger.error(f"❌ Error descubriendo clústeres: {str(e)}")
            return []
    
    def get_cluster_credentials(self, cluster_name: str, resource_group: str) -> bool:
        """
        Obtener credenciales para un clúster específico
        
        Args:
            cluster_name: Nombre del clúster
            resource_group: Grupo de recursos
            
        Returns:
            bool: True si las credenciales se obtuvieron correctamente
        """
        try:
            cmd = [
                'az', 'aks', 'get-credentials',
                '--resource-group', resource_group,
                '--name', cluster_name,
                '--overwrite-existing'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"✅ Credenciales obtenidas para {cluster_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error obteniendo credenciales para {cluster_name}: {e.stderr}")
            return False
    
    def test_connection(self) -> Dict:
        """
        Probar la conexión y devolver información de la cuenta
        
        Returns:
            Dict: Información de la cuenta de Azure
        """
        try:
            if not self.authenticate():
                return {"error": "No se pudo autenticar"}
            
            # Obtener información de la suscripción
            result = subprocess.run(
                ['az', 'account', 'show'],
                capture_output=True,
                text=True,
                check=True
            )
            
            account_info = json.loads(result.stdout)
            
            return {
                "subscription_id": account_info.get('id'),
                "subscription_name": account_info.get('name'),
                "user": account_info.get('user', {}).get('name'),
                "tenant_id": account_info.get('tenantId'),
                "status": "connected"
            }
            
        except Exception as e:
            logger.error(f"❌ Error probando conexión: {str(e)}")
            return {"error": str(e)}

def create_azure_client() -> AzureClient:
    """Factory function para crear un cliente Azure"""
    return AzureClient() 