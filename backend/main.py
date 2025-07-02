#!/usr/bin/env python3
"""
KubeHealth Dashboard - Script Principal
Orquesta el análisis completo de clústeres Kubernetes y PagerDuty
"""

import os
import sys
import logging
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Importar módulos locales
from azure_client import create_azure_client
from kubernetes_analyzer import create_kubernetes_analyzer
from pagerduty_client import create_pagerduty_client
from data_processor import create_data_processor

def setup_logging(log_level: str = "INFO") -> None:
    """
    Configurar logging para el script
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('kubehealth.log', mode='a')
        ]
    )

def load_environment_variables() -> dict:
    """
    Cargar y validar variables de entorno necesarias
    
    Returns:
        dict: Variables de entorno validadas
    """
    # Cargar archivo .env si existe
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
        logging.info("📋 Archivo .env cargado")
    
    # Variables requeridas
    required_vars = {
        'PAGERDUTY_API_TOKEN': os.getenv('PAGERDUTY_API_TOKEN'),
        'AZURE_USER': os.getenv('AZURE_USER'),
    }
    
    # Variables opcionales
    optional_vars = {
        'PAGERDUTY_SERVICE_ID': os.getenv('PAGERDUTY_SERVICE_ID'),
        'CLUSTER_PREFIX': os.getenv('CLUSTER_PREFIX', 'ftdsp-prod-aks-cluster-'),
        'OUTPUT_PATH': os.getenv('OUTPUT_PATH', 'status.json'),
        'TENANTS_FILE': os.getenv('TENANTS_FILE', 'tenants.json'),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO')
    }
    
    # Validar variables requeridas
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        raise ValueError(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
    
    # Combinar todas las variables
    env_vars = {**required_vars, **optional_vars}
    
    logging.info("✅ Variables de entorno validadas")
    return env_vars

def validate_prerequisites(env_vars: dict) -> bool:
    """
    Validar prerrequisitos del sistema
    
    Args:
        env_vars: Variables de entorno
        
    Returns:
        bool: True si todos los prerrequisitos están cumplidos
    """
    logging.info("🔍 Validando prerrequisitos del sistema...")
    
    # Verificar archivo de tenants
    tenants_file = Path(env_vars['TENANTS_FILE'])
    if not tenants_file.exists():
        logging.warning(f"⚠️ Archivo de tenants no encontrado: {tenants_file}")
        logging.warning("ℹ️ Se continuará sin mapeo de organizaciones")
    else:
        logging.info(f"✅ Archivo de tenants encontrado: {tenants_file}")
    
    # Verificar herramientas Azure CLI
    import subprocess
    try:
        result = subprocess.run(['az', '--version'], 
                              capture_output=True, text=True, check=True)
        logging.info("✅ Azure CLI disponible")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error("❌ Azure CLI no encontrado o no funciona")
        return False
    
    # Verificar kubectl
    try:
        result = subprocess.run(['kubectl', 'version', '--client'], 
                              capture_output=True, text=True, check=True)
        logging.info("✅ kubectl disponible")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error("❌ kubectl no encontrado o no funciona")
        return False
    
    return True

def parse_arguments():
    """
    Parsear argumentos de línea de comandos
    
    Returns:
        argparse.Namespace: Argumentos parseados
    """
    parser = argparse.ArgumentParser(
        description="KubeHealth Dashboard - Monitor de Kubernetes y PagerDuty",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py                    # Ejecución normal
  python main.py --debug            # Modo debug con logs detallados
  python main.py --output custom.json # Archivo de salida personalizado
        """
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Activar modo debug con logging detallado'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='../frontend/status.json',
        help='Ruta del archivo de salida JSON (default: ../frontend/status.json)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Nivel de logging (anula la variable de entorno LOG_LEVEL)'
    )
    
    return parser.parse_args()

def main():
    """Función principal del script"""
    start_time = time.time()
    
    try:
        # Parsear argumentos de línea de comandos
        args = parse_arguments()
        
        # Configurar logging inicial (puede ser anulado más tarde)
        initial_log_level = 'DEBUG' if args.debug else 'INFO'
        setup_logging(initial_log_level)
        
        logging.info("🚀 Iniciando KubeHealth Dashboard Analysis")
        logging.info(f"⏰ Hora de inicio: {datetime.now(timezone.utc).isoformat()}")
        
        if args.debug:
            logging.info("🐛 Modo DEBUG activado")
        
        # Cargar variables de entorno
        env_vars = load_environment_variables()
        
        # Usar log level de argumentos si se especifica, sino usar el de env
        log_level = args.log_level or env_vars['LOG_LEVEL']
        if args.debug:
            log_level = 'DEBUG'
            
        # Reconfigurar logging con el nivel correcto
        setup_logging(log_level)
        
        # Usar output path de argumentos si se especifica
        if args.output:
            env_vars['OUTPUT_PATH'] = args.output
            logging.info(f"📄 Archivo de salida: {args.output}")
        
        # Validar prerrequisitos
        if not validate_prerequisites(env_vars):
            logging.error("❌ Prerrequisitos no cumplidos. Abortando.")
            sys.exit(1)
        
        # === FASE 1: AUTENTICACIÓN Y CONFIGURACIÓN ===
        logging.info("📋 FASE 1: Autenticación y configuración")
        
        # Inicializar Azure Client
        azure_client = create_azure_client()
        if not azure_client.authenticate():
            logging.error("❌ Error en autenticación Azure")
            sys.exit(1)
        
        # Inicializar PagerDuty Client
        pagerduty_client = create_pagerduty_client(env_vars['PAGERDUTY_API_TOKEN'])
        pd_connection = pagerduty_client.test_connection()
        if 'error' in pd_connection:
            logging.error(f"❌ Error en conexión PagerDuty: {pd_connection['error']}")
            sys.exit(1)
        logging.info(f"✅ PagerDuty conectado - Usuario: {pd_connection.get('user', 'N/A')}")
        
        # Inicializar Kubernetes Analyzer
        k8s_analyzer = create_kubernetes_analyzer()
        
        # Inicializar Data Processor
        data_processor = create_data_processor(env_vars['TENANTS_FILE'])
        tenant_mapping = data_processor.get_tenant_mapping()
        
        # === FASE 2: DESCUBRIMIENTO DE CLÚSTERES ===
        logging.info("🔍 FASE 2: Descubrimiento de clústeres")
        
        clusters = azure_client.discover_aks_clusters(env_vars['CLUSTER_PREFIX'])
        if not clusters:
            logging.warning("⚠️ No se encontraron clústeres AKS")
            # Generar respuesta vacía pero válida
            empty_data = data_processor.process_cluster_data([], {})
            data_processor.save_status_json(empty_data, env_vars['OUTPUT_PATH'])
            logging.info("📄 Status JSON vacío generado")
            return
        
        logging.info(f"📊 Encontrados {len(clusters)} clústeres para analizar")
        
        # === FASE 3: ANÁLISIS DE KUBERNETES ===
        logging.info("🔍 FASE 3: Análisis de clústeres Kubernetes")
        
        cluster_analysis = k8s_analyzer.analyze_all_clusters(clusters, azure_client)
        
        if not cluster_analysis:
            logging.error("❌ No se pudo analizar ningún clúster")
            sys.exit(1)
        
        # Extraer lista de namespaces para correlación
        all_namespaces = []
        for cluster_data in cluster_analysis:
            for namespace_data in cluster_data.get('namespaces', []):
                namespace_uuid = namespace_data.get('namespace')
                if namespace_uuid:
                    all_namespaces.append(namespace_uuid)
        
        logging.info(f"📋 Total namespaces UUID encontrados: {len(all_namespaces)}")
        
        # === FASE 4: CORRELACIÓN CON PAGERDUTY ===
        logging.info("🔗 FASE 4: Correlación con incidentes PagerDuty")
        
        pagerduty_correlations = {}
        if all_namespaces:
            pagerduty_correlations = pagerduty_client.correlate_incidents_with_namespaces(
                all_namespaces, 
                tenant_mapping,
                hours=24  # Buscar incidentes de las últimas 24 horas
            )
        
        total_incidents = sum(len(incidents) for incidents in pagerduty_correlations.values())
        logging.info(f"🔗 Total correlaciones de incidentes: {total_incidents}")
        
        # === FASE 5: PROCESAMIENTO Y GENERACIÓN ===
        logging.info("⚙️ FASE 5: Procesamiento de datos y generación de status.json")
        
        # Procesar todos los datos
        final_data = data_processor.process_cluster_data(
            cluster_analysis, 
            pagerduty_correlations
        )
        
        # Guardar archivo JSON final
        if data_processor.save_status_json(final_data, env_vars['OUTPUT_PATH']):
            logging.info("✅ Status JSON generado exitosamente")
        else:
            logging.error("❌ Error guardando status JSON")
            sys.exit(1)
        
        # === RESUMEN FINAL ===
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        
        summary = final_data.get('summary', {})
        logging.info("=" * 60)
        logging.info("📊 RESUMEN DE ANÁLISIS COMPLETADO")
        logging.info("=" * 60)
        logging.info(f"⏱️ Duración total: {duration} segundos")
        logging.info(f"🏗️ Clústeres analizados: {summary.get('total_clusters', 0)}")
        logging.info(f"📦 Namespaces monitoreados: {summary.get('total_namespaces_monitored', 0)}")
        logging.info(f"🟢 Pods ejecutándose: {summary.get('pods_running', 0)}")
        logging.info(f"🔴 Pods con problemas: {summary.get('pods_with_issues', 0)}")
        logging.info(f"⚠️ Incidentes activos: {summary.get('active_incidents', 0)}")
        logging.info(f"📈 Disponibilidad promedio: {summary.get('availability_average', 0)}%")
        logging.info(f"🎯 Estado general: {final_data.get('overall_status', 'unknown').upper()}")
        logging.info("=" * 60)
        
        # Log de ubicación del archivo
        output_path = Path(env_vars['OUTPUT_PATH']).absolute()
        logging.info(f"📄 Archivo generado: {output_path}")
        
        logging.info("🎉 Análisis completado exitosamente")
        
    except KeyboardInterrupt:
        logging.info("⏹️ Análisis interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        logging.error(f"❌ Error fatal en el análisis: {str(e)}")
        logging.exception("Detalles del error:")
        sys.exit(1)

if __name__ == "__main__":
    main() 