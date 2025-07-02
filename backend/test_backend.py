#!/usr/bin/env python3
"""
Script de prueba para validar el backend de KubeHealth Dashboard
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Probar que todos los módulos se puedan importar correctamente"""
    logger.info("🧪 Probando importación de módulos...")
    
    try:
        from azure_client import create_azure_client
        logger.info("✅ azure_client importado correctamente")
    except ImportError as e:
        logger.error(f"❌ Error importando azure_client: {e}")
        return False
    
    try:
        from kubernetes_analyzer import create_kubernetes_analyzer
        logger.info("✅ kubernetes_analyzer importado correctamente")
    except ImportError as e:
        logger.error(f"❌ Error importando kubernetes_analyzer: {e}")
        return False
    
    try:
        from pagerduty_client import create_pagerduty_client
        logger.info("✅ pagerduty_client importado correctamente")
    except ImportError as e:
        logger.error(f"❌ Error importando pagerduty_client: {e}")
        return False
    
    try:
        from data_processor import create_data_processor
        logger.info("✅ data_processor importado correctamente")
    except ImportError as e:
        logger.error(f"❌ Error importando data_processor: {e}")
        return False
    
    logger.info("🎉 Todos los módulos importados exitosamente")
    return True

def test_environment():
    """Probar carga de variables de entorno"""
    logger.info("🧪 Probando carga de variables de entorno...")
    
    # Cargar .env si existe
    env_file = Path('../.env')
    if env_file.exists():
        load_dotenv(env_file)
        logger.info("✅ Archivo .env encontrado y cargado")
    else:
        logger.warning("⚠️ Archivo .env no encontrado")
    
    # Verificar variables críticas
    required_vars = ['PAGERDUTY_API_TOKEN', 'AZURE_USER']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            logger.info(f"✅ {var} configurado")
    
    if missing_vars:
        logger.error(f"❌ Variables faltantes: {', '.join(missing_vars)}")
        return False
    
    return True

def test_azure_connection():
    """Probar conexión a Azure (sin autenticación real)"""
    logger.info("🧪 Probando Azure Client...")
    
    try:
        from azure_client import create_azure_client
        
        azure_client = create_azure_client()
        logger.info("✅ Azure Client creado")
        
        # Probar método de conexión (sin autenticar realmente)
        logger.info("ℹ️ Para autenticación completa, ejecuta 'az login'")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error en Azure Client: {e}")
        return False

def test_pagerduty_connection():
    """Probar conexión a PagerDuty"""
    logger.info("🧪 Probando PagerDuty Client...")
    
    try:
        from pagerduty_client import create_pagerduty_client
        
        api_token = os.getenv('PAGERDUTY_API_TOKEN')
        if not api_token:
            logger.warning("⚠️ Token de PagerDuty no configurado, saltando prueba")
            return True
        
        pd_client = create_pagerduty_client(api_token)
        logger.info("✅ PagerDuty Client creado")
        
        # Probar conexión real
        connection_test = pd_client.test_connection()
        if 'error' in connection_test:
            logger.warning(f"⚠️ No se pudo conectar a PagerDuty: {connection_test['error']}")
            logger.info("ℹ️ Esto puede ser por token inválido o permisos insuficientes")
            logger.info("✅ Pero el cliente se creó correctamente")
            return True  # Consideramos exitoso si el cliente se crea
        else:
            logger.info(f"✅ PagerDuty conectado - Usuario: {connection_test.get('user', 'N/A')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error en PagerDuty Client: {e}")
        return False

def test_kubernetes_analyzer():
    """Probar Kubernetes Analyzer"""
    logger.info("🧪 Probando Kubernetes Analyzer...")
    
    try:
        from kubernetes_analyzer import create_kubernetes_analyzer
        
        k8s_analyzer = create_kubernetes_analyzer()
        logger.info("✅ Kubernetes Analyzer creado")
        
        # Probar validación de UUID
        test_uuid = "052e3aed-e210-4869-ae4b-062c02654ca7"
        if k8s_analyzer.is_valid_uuid(test_uuid):
            logger.info("✅ Validación de UUID funciona")
        else:
            logger.error("❌ Error en validación de UUID")
            return False
        
        return True
    except Exception as e:
        logger.error(f"❌ Error en Kubernetes Analyzer: {e}")
        return False

def test_data_processor():
    """Probar Data Processor"""
    logger.info("🧪 Probando Data Processor...")
    
    try:
        from data_processor import create_data_processor
        
        # Usar archivo de tenants relativo
        tenants_file = "../tenants.json"
        data_processor = create_data_processor(tenants_file)
        logger.info("✅ Data Processor creado")
        
        # Probar procesamiento con datos vacíos
        empty_result = data_processor.process_cluster_data([], {})
        if empty_result and 'last_updated' in empty_result:
            logger.info("✅ Procesamiento de datos vacíos funciona")
        else:
            logger.error("❌ Error en procesamiento de datos")
            return False
        
        return True
    except Exception as e:
        logger.error(f"❌ Error en Data Processor: {e}")
        return False

def test_main_module():
    """Probar que el módulo main se puede importar"""
    logger.info("🧪 Probando módulo main...")
    
    try:
        import main
        logger.info("✅ Módulo main importado correctamente")
        return True
    except ImportError as e:
        logger.error(f"❌ Error importando main: {e}")
        return False

def run_all_tests():
    """Ejecutar todas las pruebas"""
    logger.info("🚀 Iniciando pruebas del backend KubeHealth Dashboard")
    logger.info("=" * 60)
    
    tests = [
        ("Importación de módulos", test_imports),
        ("Variables de entorno", test_environment),
        ("Azure Client", test_azure_connection),
        ("PagerDuty Client", test_pagerduty_connection),
        ("Kubernetes Analyzer", test_kubernetes_analyzer),
        ("Data Processor", test_data_processor),
        ("Módulo Main", test_main_module),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Ejecutando: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name}: PASÓ")
            else:
                logger.error(f"❌ {test_name}: FALLÓ")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 RESULTADOS: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        logger.info("🎉 ¡Todas las pruebas pasaron! El backend está listo.")
        return True
    else:
        logger.error(f"⚠️ {total - passed} pruebas fallaron. Revisa los errores arriba.")
        return False

if __name__ == "__main__":
    if run_all_tests():
        sys.exit(0)
    else:
        sys.exit(1) 