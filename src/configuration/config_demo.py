#🌻🌾🌴替换成你自己的配置
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
TEMPLATE_DIR = ROOT_DIR / 'src' / 'web' / 'templates'


NEO4J_CONFIG = {'uri':'neo4j://localhost:7687',
                'auth':('neo4j','12345678')}

DEEPSEEK_API_KEY = 'you deepseek api key'

