import pytest
import os
from pathlib import Path
import sys

# Aggiungi la directory root al path di Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imposta le variabili d'ambiente per i test
os.environ['ENVIRONMENT'] = 'test'
os.environ['OPENROUTER_API_KEY'] = 'test_api_key'
os.environ['MAX_FILE_SIZE_MB'] = '10'
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['TEMP_FOLDER'] = '/tmp/railway-document-worker-test'

# Crea la directory temporanea per i test
Path(os.environ['TEMP_FOLDER']).mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    """Pulizia dopo l'esecuzione dei test"""
    def remove_test_dir():
        import shutil
        temp_dir = Path(os.environ['TEMP_FOLDER'])
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    request.addfinalizer(remove_test_dir)
