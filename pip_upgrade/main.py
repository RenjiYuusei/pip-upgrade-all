import subprocess
import sys
import json
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from packaging import version

class PipUpgrader:
    def __init__(self):
        self.max_workers = 10
        self.timeout = 300

    def get_outdated_packages(self) -> List[Dict]:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except:
            print("Error when checking outdated packages")
            return []

    def upgrade_package(self, package: Dict) -> Tuple[str, bool, str]:
        package_name = package['name']
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", package_name],
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout
            )
            return (package_name, True, "Successfully upgraded")
        except:
            return (package_name, False, "Error when upgrading")

    def upgrade_all_packages(self, outdated: List[Dict]) -> None:
        print(f"\n📦 Found {len(outdated)} packages to upgrade:")
        for pkg in outdated:
            print(f"  • {pkg['name']}: {pkg['version']} → {pkg['latest_version']}")
        
        print("\n🚀 Upgrading...")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_pkg = {executor.submit(self.upgrade_package, pkg): pkg for pkg in outdated}
            for future in as_completed(future_to_pkg):
                name, success, message = future.result()
                if success:
                    print(f"✓ {name}: {message}")
                else:
                    print(f"✗ {name}: {message}")

def main():
    upgrader = PipUpgrader()
    outdated = upgrader.get_outdated_packages()
    
    if not outdated:
        print("✨ All packages are up to date!")
        return
    
    upgrader.upgrade_all_packages(outdated)
    print("\n✨ Complete !")

if __name__ == "__main__":
    main() 