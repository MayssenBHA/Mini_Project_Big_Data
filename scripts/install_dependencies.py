# Script Python pour installer les dépendances dans le conteneur python-env
# À exécuter: docker exec -it python-env python /scripts/install_dependencies.py

import subprocess
import sys

print("=" * 60)
print("📦 Installation des dépendances Python")
print("=" * 60)

packages = [
    "kafka-python",
    "pandas",
    "cassandra-driver",
    "numpy"
]

for package in packages:
    print(f"\n📥 Installation de {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ {package} installé avec succès")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation de {package}: {e}")

print("\n" + "=" * 60)
print("✅ Installation terminée!")
print("=" * 60)
print("\n📋 Packages installés:")
subprocess.call([sys.executable, "-m", "pip", "list"])
