"""
PagerDuty Client Module
Maneja la integración con la API de PagerDuty para obtener incidentes
"""

import os
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

class PagerDutyClient:
    """Cliente para interactuar con la API de PagerDuty"""
    
    def __init__(self, api_token: str):
        """
        Inicializar cliente PagerDuty
        
        Args:
            api_token: Token de API de PagerDuty
        """
        self.api_token = api_token
        self.base_url = "https://api.pagerduty.com/incidents"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Token token={api_token}" #Security improvements
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_connection(self) -> Dict:
        """
        Probar la conexión a PagerDuty
        
        Returns:
            Dict: Información del usuario y estado de conexión
        """
        try:
            response = self.session.get(f"{self.base_url}")
            response.raise_for_status()
            
            user_data = response.json()
            return {
                "status": "connected",
                "user": user_data.get("user", {}).get("name"),
                "email": user_data.get("user", {}).get("email"),
                "role": user_data.get("user", {}).get("role")
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error conectando a PagerDuty: {str(e)}")
            return {"error": str(e)}
    
    def get_services(self, limit: int = 100) -> List[Dict]:
        """
        Obtener lista de servicios de PagerDuty
        
        Args:
            limit: Límite de servicios a obtener
            
        Returns:
            List[Dict]: Lista de servicios
        """
        try:
            params = {
                "limit": limit,
                "include[]": ["integrations", "escalation_policies"]
            }
            
            response = self.session.get(f"{self.base_url}/services", params=params)
            response.raise_for_status()
            
            data = response.json()
            services = data.get("services", [])
            
            logger.info(f"📋 Encontrados {len(services)} servicios en PagerDuty")
            return services
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error obteniendo servicios: {str(e)}")
            return []
    
    def get_incidents(self, 
                     service_ids: Optional[List[str]] = None,
                     since: Optional[datetime] = None,
                     until: Optional[datetime] = None,
                     statuses: Optional[List[str]] = None,
                     limit: int = 100) -> List[Dict]:
        """
        Obtener incidentes de PagerDuty
        
        Args:
            service_ids: Lista de IDs de servicios a filtrar
            since: Fecha desde (por defecto últimas 24 horas)
            until: Fecha hasta (por defecto ahora)
            statuses: Estados de incidentes a incluir
            limit: Límite de incidentes a obtener
            
        Returns:
            List[Dict]: Lista de incidentes
        """
        try:
            # Configurar fechas por defecto
            if not since:
                since = datetime.now(timezone.utc) - timedelta(hours=24)
            if not until:
                until = datetime.now(timezone.utc)
            
            # Configurar estados por defecto
            if not statuses:
                statuses = ["triggered", "acknowledged", "resolved"]
            
            params = {
                "since": since.isoformat(),
                "until": until.isoformat(),
                "statuses[]": statuses,
                "limit": limit,
                "include[]": ["services", "assignments", "acknowledgers", "teams"]
            }
            
            # Filtrar por servicios si se especifica
            if service_ids:
                params["service_ids[]"] = service_ids
            
            response = self.session.get(f"{self.base_url}/incidents", params=params)
            response.raise_for_status()
            
            data = response.json()
            incidents = data.get("incidents", [])
            print(f"Incidents: {incidents}")
            
            logger.info(f"📊 Encontrados {len(incidents)} incidentes")
            return incidents
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error obteniendo incidentes: {str(e)}")
            return []
    
    def get_recent_incidents(self, hours: int = 24) -> List[Dict]:
        """
        Obtener incidentes recientes
        
        Args:
            hours: Horas hacia atrás para buscar incidentes
            
        Returns:
            List[Dict]: Lista de incidentes recientes
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        return self.get_incidents(since=since)
    
    def get_active_incidents(self) -> List[Dict]:
        """
        Obtener solo incidentes activos (triggered o acknowledged)
        
        Returns:
            List[Dict]: Lista de incidentes activos
        """
        return self.get_incidents(statuses=["triggered", "acknowledged"])
    
    def find_incidents_by_service_name(self, service_name_pattern: str, hours: int = 24) -> List[Dict]:
        """
        Buscar incidentes por patrón en el nombre del servicio
        
        Args:
            service_name_pattern: Patrón a buscar en el nombre del servicio
            hours: Horas hacia atrás para buscar
            
        Returns:
            List[Dict]: Lista de incidentes que coinciden
        """
        try:
            # Obtener todos los incidentes recientes
            incidents = self.get_recent_incidents(hours=hours)
            
            # Filtrar por patrón en el nombre del servicio
            matching_incidents = []
            for incident in incidents:
                service = incident.get("service", {})
                service_name = service.get("name", "").lower()
                
                if service_name_pattern.lower() in service_name:
                    matching_incidents.append(incident)
            
            logger.info(f"🔍 Encontrados {len(matching_incidents)} incidentes "
                       f"que coinciden con '{service_name_pattern}'")
            return matching_incidents
            
        except Exception as e:
            logger.error(f"❌ Error buscando incidentes por servicio: {str(e)}")
            return []
    
    def correlate_incidents_with_namespaces(self, 
                                          namespaces: List[str], 
                                          tenant_mapping: Dict[str, str],
                                          hours: int = 24) -> Dict[str, List[Dict]]:
        """
        Correlacionar incidentes con namespaces basado en nombres de organizaciones
        
        Args:
            namespaces: Lista de namespaces UUID
            tenant_mapping: Mapeo de UUID a nombres de organizaciones
            hours: Horas hacia atrás para buscar incidentes
            
        Returns:
            Dict[str, List[Dict]]: Diccionario de namespace -> lista de incidentes
        """
        try:
            # Obtener todos los incidentes recientes
            all_incidents = self.get_recent_incidents(hours=hours)
            
            # Resultado: namespace -> lista de incidentes
            correlations = {ns: [] for ns in namespaces}
            
            for namespace in namespaces:
                org_name = tenant_mapping.get(namespace, "")
                if not org_name:
                    continue
                
                # Buscar incidentes que contengan palabras del nombre de la organización
                org_words = self._extract_keywords(org_name)
                
                for incident in all_incidents:
                    if self._incident_matches_organization(incident, org_words):
                        incident_info = self._extract_incident_info(incident)
                        correlations[namespace].append(incident_info)
                        logger.debug(f"🔗 Correlacionado incidente {incident_info['id']} "
                                   f"con namespace {namespace} ({org_name})")
            
            # Log del resumen
            total_correlations = sum(len(incidents) for incidents in correlations.values())
            logger.info(f"🔗 Total correlaciones encontradas: {total_correlations}")
            
            return correlations
            
        except Exception as e:
            logger.error(f"❌ Error correlacionando incidentes: {str(e)}")
            return {ns: [] for ns in namespaces}
    
    def _extract_keywords(self, org_name: str) -> List[str]:
        """
        Extraer palabras clave del nombre de la organización para búsqueda
        
        Args:
            org_name: Nombre de la organización
            
        Returns:
            List[str]: Lista de palabras clave
        """
        # Remover palabras comunes y extraer palabras significativas
        stop_words = {
            'de', 'la', 'el', 'y', 'del', 'las', 'los', 'en', 'con', 'por',
            'para', 'inc', 'llc', 'corp', 'corporation', 'company', 'co',
            'ltd', 'limited', 'sapi', 'cv', 'sa'
        }
        
        # Limpiar y dividir
        words = org_name.lower().replace(',', ' ').replace('.', ' ').split()
        keywords = [word.strip() for word in words 
                   if len(word) > 2 and word not in stop_words]
        
        return keywords
    
    def _incident_matches_organization(self, incident: Dict, org_keywords: List[str]) -> bool:
        """
        Verificar si un incidente coincide con las palabras clave de la organización
        
        Args:
            incident: Datos del incidente
            org_keywords: Palabras clave de la organización
            
        Returns:
            bool: True si hay coincidencia
        """
        # Campos del incidente a buscar
        search_fields = [
            incident.get("title", ""),
            incident.get("description", ""),
            incident.get("service", {}).get("name", ""),
            incident.get("service", {}).get("description", "")
        ]
        
        # Combinar todos los campos en un texto
        search_text = " ".join(search_fields).lower()
        
        # Buscar coincidencias con las palabras clave
        for keyword in org_keywords:
            if keyword in search_text:
                return True
        
        return False
    
    def _extract_incident_info(self, incident: Dict) -> Dict:
        """
        Extraer información relevante de un incidente
        
        Args:
            incident: Datos completos del incidente
            
        Returns:
            Dict: Información simplificada del incidente
        """
        return {
            "id": incident.get("id"),
            "incident_number": incident.get("incident_number"),
            "title": incident.get("title", ""),
            "description": incident.get("description", ""),
            "status": incident.get("status"),
            "urgency": incident.get("urgency"),
            "priority": incident.get("priority", {}).get("name", ""),
            "service": {
                "id": incident.get("service", {}).get("id"),
                "name": incident.get("service", {}).get("name", "")
            },
            "created_at": incident.get("created_at"),
            "updated_at": incident.get("updated_at"),
            "html_url": incident.get("html_url"),
            "assignments": [
                {
                    "assignee": assignment.get("assignee", {}).get("summary", "")
                }
                for assignment in incident.get("assignments", [])
            ]
        }

def create_pagerduty_client(api_token: str) -> PagerDutyClient:
    """
    Factory function para crear un cliente PagerDuty
    
    Args:
        api_token: Token de API de PagerDuty
        
    Returns:
        PagerDutyClient: Cliente configurado
    """
    return PagerDutyClient(api_token) 