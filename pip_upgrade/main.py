import subprocess
import sys
import json
import argparse
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from packaging import version
import time
import logging
from datetime import datetime
import os

class PipUpgrader:
    def __init__(self, skip_packages: List[str] = None, concurrent: bool = True, 
                 max_workers: int = 5, timeout: int = 300, max_version: str = None):
        """
        Initialize PipUpgrader
        
        Args:
            skip_packages: List of packages to skip during upgrade
            concurrent: Whether to use concurrent upgrades
            max_workers: Maximum number of concurrent upgrades
            timeout: Timeout in seconds for each package upgrade
            max_version: Maximum version to upgrade to (e.g. 2.0.0)
        """
        self.skip_packages = skip_packages or []
        self.concurrent = concurrent
        self.max_workers = max_workers
        self.timeout = timeout
        self.max_version = version.parse(max_version) if max_version else None

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

    def upgrade_package(self, package: Dict, max_retries: int = 3) -> Tuple[str, bool, str]:
        """
        Upgrade a single package to its latest version.
        
        Returns:
            Tuple of (package_name, success, message)
        """
        package_name = package['name']
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                start_time = time.time()
                current_version = version.parse(package['version'])
                latest_version = version.parse(package['latest_version'])
                
                # Check if the max_version is specified
                if self.max_version and latest_version > self.max_version:
                    return (package_name, False, f"Latest version {latest_version} exceeds maximum allowed version {self.max_version}")
                
                # Check the version gap
                if latest_version.major - current_version.major > 1:
                    return (package_name, False, "Major version gap too large - manual upgrade recommended")
                
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", package_name],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=self.timeout
                )
                duration = time.time() - start_time
                return (package_name, True, f"Upgraded in {duration:.1f}s")
                
            except subprocess.TimeoutExpired:
                return (package_name, False, f"Upgrade timed out after {self.timeout}s")
            except subprocess.CalledProcessError as e:
                retry_count += 1
                if retry_count == max_retries:
                    return (package_name, False, f"Failed after {max_retries} retries: {str(e)}")
                time.sleep(2 ** retry_count)  # Exponential backoff

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
    parser.add_argument("--max-version", "-m", type=str, help="Maximum version to upgrade to (e.g. 2.0.0)")
    parser.add_argument("--log", "-l", help="Path to log file")
    parser.add_argument("--report", "-r", help="Path to save upgrade report")
    return parser.parse_args()

def setup_logging(log_path: str = None):
    """Setup logging configuration"""
    if log_path:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

def generate_report(successful: List[str], failed: List[Tuple[str, str]], 
                   total_time: float, report_path: str):
    """Generate and save upgrade report"""
    report = [
        "=== Pip Upgrade Report ===",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total time: {total_time:.1f}s\n",
        f"Successfully upgraded ({len(successful)}):",
        *[f"  • {pkg}" for pkg in successful],
        f"\nFailed upgrades ({len(failed)}):",
        *[f"  • {pkg}: {error}" for pkg, error in failed]
    ]
    
    with open(report_path, 'w') as f:
        f.write('\n'.join(report))

def main():
    """Main function to upgrade all outdated packages."""
    args = parse_args()
    
    # Setup logging if specified
    setup_logging(args.log)
    
    upgrader = PipUpgrader(
        skip_packages=args.skip,
        concurrent=not args.no_concurrent,
        max_workers=args.workers,
        timeout=300,
        max_version=args.max_version
    )

    logging.info("Checking for outdated packages...")
    outdated = upgrader.get_outdated_packages()
    
    if not outdated:
        logging.info("✨ All packages are up to date!")
        return
    
    logging.info(f"\n📦 Found {len(outdated)} outdated package(s):")
    for pkg in outdated:
        logging.info(f"  • {pkg['name']}: {pkg['version']} → {pkg['latest_version']}")
    
    logging.info("\n🚀 Starting upgrade process...")
    start_time = time.time()
    successful, failed = upgrader.upgrade_all_packages(outdated)
    total_time = time.time() - start_time

    # Generate report if path specified
    if args.report:
        generate_report(successful, failed, total_time, args.report)
        logging.info(f"\n📝 Report saved to: {args.report}")

    # Print summary
    logging.info(f"\n📊 Upgrade Summary (completed in {total_time:.1f}s):")
    logging.info(f"✓ Successfully upgraded: {len(successful)} package(s)")
    if successful:
        logging.info("  Successfully upgraded packages:")
        for pkg in successful:
            logging.info(f"  • {pkg}")

    if failed:
        logging.info(f"\n✗ Failed to upgrade: {len(failed)} package(s)")
        logging.info("  Failed packages:")
        for pkg, error in failed:
            logging.info(f"  • {pkg}: {error}")

if __name__ == "__main__":
    main() 