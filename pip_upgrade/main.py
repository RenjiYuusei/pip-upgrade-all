import subprocess
import sys
import json
import argparse
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from packaging import version
import time

class PipUpgrader:
    def __init__(self, skip_packages: List[str] = None, concurrent: bool = True, max_workers: int = 5):
        """
        Initialize PipUpgrader
        
        Args:
            skip_packages: List of packages to skip during upgrade
            concurrent: Whether to use concurrent upgrades
            max_workers: Maximum number of concurrent upgrades
        """
        self.skip_packages = skip_packages or []
        self.concurrent = concurrent
        self.max_workers = max_workers

    def get_outdated_packages(self) -> List[Dict]:
        """Get a list of outdated packages."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                check=True
            )
            packages = json.loads(result.stdout)
            return [pkg for pkg in packages if pkg['name'] not in self.skip_packages]
        except subprocess.CalledProcessError as e:
            print(f"Error checking for outdated packages: {e}")
            return []
        except json.JSONDecodeError:
            print("Error parsing pip output")
            return []

    def upgrade_package(self, package: Dict) -> Tuple[str, bool, str]:
        """
        Upgrade a single package to its latest version.
        
        Returns:
            Tuple of (package_name, success, message)
        """
        package_name = package['name']
        try:
            start_time = time.time()
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", package_name],
                capture_output=True,
                text=True,
                check=True
            )
            duration = time.time() - start_time
            return (package_name, True, f"Upgraded in {duration:.1f}s")
        except subprocess.CalledProcessError as e:
            return (package_name, False, str(e))

    def upgrade_all_packages(self, outdated: List[Dict]) -> Tuple[List[str], List[Tuple[str, str]]]:
        """
        Upgrade all outdated packages.
        
        Returns:
            Tuple of (successful packages, failed packages with errors)
        """
        successful = []
        failed = []

        if self.concurrent:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_pkg = {executor.submit(self.upgrade_package, pkg): pkg for pkg in outdated}
                for future in as_completed(future_to_pkg):
                    name, success, message = future.result()
                    if success:
                        successful.append(name)
                        print(f"✓ {name}: {message}")
                    else:
                        failed.append((name, message))
                        print(f"✗ {name}: {message}")
        else:
            for pkg in outdated:
                name, success, message = self.upgrade_package(pkg)
                if success:
                    successful.append(name)
                    print(f"✓ {name}: {message}")
                else:
                    failed.append((name, message))
                    print(f"✗ {name}: {message}")

        return successful, failed

def parse_args():
    parser = argparse.ArgumentParser(description="Upgrade all outdated Python packages")
    parser.add_argument("--skip", "-s", nargs="+", help="Packages to skip during upgrade")
    parser.add_argument("--no-concurrent", action="store_true", help="Disable concurrent upgrades")
    parser.add_argument("--workers", "-w", type=int, default=5, help="Number of concurrent workers")
    return parser.parse_args()

def main():
    """Main function to upgrade all outdated packages."""
    args = parse_args()
    
    upgrader = PipUpgrader(
        skip_packages=args.skip,
        concurrent=not args.no_concurrent,
        max_workers=args.workers
    )

    print("🔍 Checking for outdated packages...")
    outdated = upgrader.get_outdated_packages()
    
    if not outdated:
        print("✨ All packages are up to date!")
        return
    
    print(f"\n📦 Found {len(outdated)} outdated package(s):")
    for pkg in outdated:
        print(f"  • {pkg['name']}: {pkg['version']} → {pkg['latest_version']}")
    
    print("\n🚀 Starting upgrade process...")
    start_time = time.time()
    successful, failed = upgrader.upgrade_all_packages(outdated)
    total_time = time.time() - start_time

    print(f"\n📊 Upgrade Summary (completed in {total_time:.1f}s):")
    print(f"✓ Successfully upgraded: {len(successful)} package(s)")
    if successful:
        print("  Successfully upgraded packages:")
        for pkg in successful:
            print(f"  • {pkg}")

    if failed:
        print(f"\n✗ Failed to upgrade: {len(failed)} package(s)")
        print("  Failed packages:")
        for pkg, error in failed:
            print(f"  • {pkg}: {error}")

if __name__ == "__main__":
    main() 