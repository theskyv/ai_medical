from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent


NEO4J_CONFIG = {'uri':'neo4j://localhost:7687',
                'auth':('neo4j','12345678')}
