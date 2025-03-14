import subprocess
import sys
import json
import argparse
import os
import time
import logging
from typing import List, Dict, Tuple, Optional, Set, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from packaging import version
from colorama import Fore, Style, init

# Initialize colorama
init()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("pip-upgrade-all")

class PipUpgrader:
    def __init__(self, max_workers: int = 10, timeout: int = 300, 
                 include: Optional[List[str]] = None, exclude: Optional[List[str]] = None,
                 interactive: bool = False, pip_executable: Optional[str] = None,
                 venv: Optional[str] = None, batch_mode: bool = False,
                 continue_on_error: bool = False, log_file: Optional[str] = None):
        self.max_workers = max_workers
        self.timeout = timeout
        self.include = set(include) if include else None
        self.exclude = set(exclude) if exclude else set()
        self.interactive = interactive
        self.batch_mode = batch_mode
        self.continue_on_error = continue_on_error
        
        # Set up file logging if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logger.addHandler(file_handler)
        
        # Set pip executable
        if pip_executable:
            self.pip_cmd = pip_executable
        elif venv:
            # Use pip from the specified virtual environment
            if sys.platform == "win32":
                self.pip_cmd = os.path.join(venv, "Scripts", "pip.exe")
            else:
                self.pip_cmd = os.path.join(venv, "bin", "pip")
        else:
            # Use the current Python's pip
            self.pip_cmd = [sys.executable, "-m", "pip"]

    def get_outdated_packages(self) -> List[Dict]:
        try:
            pip_cmd = self.pip_cmd if isinstance(self.pip_cmd, list) else [self.pip_cmd]
            result = subprocess.run(
                pip_cmd + ["list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                check=True
            )
            outdated = json.loads(result.stdout)
            
            # Filter packages if include/exclude lists are provided
            filtered_outdated = []
            for pkg in outdated:
                if self.include is not None and pkg['name'] not in self.include:
                    continue
                if pkg['name'] in self.exclude:
                    continue
                filtered_outdated.append(pkg)
                
            return filtered_outdated
        except subprocess.SubprocessError as e:
            message = f"Error when checking outdated packages: {str(e)}"
            logger.error(message)
            print(f"{Fore.RED}🚫 {message}{Style.RESET_ALL}")
            return []
        except json.JSONDecodeError:
            message = "Error parsing pip output"
            logger.error(message)
            print(f"{Fore.RED}🚫 {message}{Style.RESET_ALL}")
            return []

    def upgrade_package(self, package: Dict) -> Tuple[str, bool, str]:
        package_name = package['name']
        old_version = package['version']
        new_version = package['latest_version']
        result = None
        
        # If interactive mode is enabled, ask for confirmation
        if self.interactive:
            response = input(f"\nUpgrade {Fore.CYAN}{package_name}{Style.RESET_ALL} from {Fore.YELLOW}{old_version}{Style.RESET_ALL} to {Fore.GREEN}{new_version}{Style.RESET_ALL}? (Y/n): ").strip().lower()
            if response and response != 'y':
                return (package_name, False, "Skipped by user")
        
        try:
            pip_cmd = self.pip_cmd if isinstance(self.pip_cmd, list) else [self.pip_cmd]
            result = subprocess.run(
                pip_cmd + ["install", "--upgrade", package_name],
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout
            )
            logger.info(f"Successfully upgraded {package_name} from {old_version} to {new_version}")
            return (package_name, True, f"Upgraded from {old_version} to {new_version}")
        except subprocess.TimeoutExpired as e:
            message = f"Timed out after {self.timeout} seconds"
            logger.error(f"{package_name}: {message}")
            return (package_name, False, message)
        except subprocess.SubprocessError as e:
            # Safe access to result.stderr
            error_msg = result.stderr if result and hasattr(result, 'stderr') else str(e)
            message = f"Error: {error_msg}"
            logger.error(f"{package_name}: {message}")
            return (package_name, False, message)
        except Exception as e:
            message = f"Unexpected error: {str(e)}"
            logger.error(f"{package_name}: {message}")
            return (package_name, False, message)

    def batch_upgrade_packages(self, packages: List[Dict]) -> List[Tuple[str, bool, str]]:
        """Upgrade multiple packages in a single pip command for faster execution"""
        if not packages:
            return []
        
        # Extract package names
        package_names = [pkg['name'] for pkg in packages]
        name_to_version = {pkg['name']: (pkg['version'], pkg['latest_version']) for pkg in packages}
        
        # Build command
        pip_cmd = self.pip_cmd if isinstance(self.pip_cmd, list) else [self.pip_cmd]
        cmd = pip_cmd + ["install", "--upgrade"] + package_names
        
        results = []
        try:
            print(f"{Fore.BLUE}⚡ Batch upgrading {len(packages)} packages...{Style.RESET_ALL}")
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout * 2  # Longer timeout for batch
            )
            duration = time.time() - start_time
            
            # All packages succeeded
            for pkg_name in package_names:
                old_ver, new_ver = name_to_version[pkg_name]
                results.append((pkg_name, True, f"Upgraded from {old_ver} to {new_ver}"))
                
            print(f"{Fore.GREEN}✓ Batch upgrade completed in {duration:.1f} seconds{Style.RESET_ALL}")
            return results
            
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, Exception) as e:
            # If batch failed, log the error
            error_msg = result.stderr if 'result' in locals() and hasattr(result, 'stderr') else str(e)
            logger.error(f"Batch upgrade failed: {error_msg}")
            print(f"{Fore.RED}✗ Batch upgrade failed. Falling back to individual upgrades...{Style.RESET_ALL}")
            
            # Return empty list to signal fallback to individual upgrades
            return []

    def export_package_list(self, outdated: List[Dict], filename: str) -> None:
        """Export list of outdated packages to a file"""
        try:
            with open(filename, 'w') as f:
                json.dump(outdated, f, indent=2)
            print(f"{Fore.GREEN}✓ Package list exported to {filename}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to export package list: {str(e)}{Style.RESET_ALL}")

    def import_package_list(self, filename: str) -> List[Dict]:
        """Import list of packages from a file"""
        try:
            with open(filename, 'r') as f:
                packages = json.load(f)
            print(f"{Fore.GREEN}✓ Package list imported from {filename}{Style.RESET_ALL}")
            return packages
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to import package list: {str(e)}{Style.RESET_ALL}")
            return []

    def upgrade_all_packages(self, outdated: List[Dict], dry_run: bool = False) -> None:
        if not outdated:
            print(f"{Fore.GREEN}✨ All packages are up to date!{Style.RESET_ALL}")
            return
            
        print(f"\n{Fore.BLUE}📦 Found {len(outdated)} packages to upgrade:{Style.RESET_ALL}")
        for pkg in outdated:
            print(f"  • {Fore.CYAN}{pkg['name']}{Style.RESET_ALL}: {Fore.YELLOW}{pkg['version']}{Style.RESET_ALL} → {Fore.GREEN}{pkg['latest_version']}{Style.RESET_ALL}")
        
        if dry_run:
            print(f"\n{Fore.GREEN}🏁 Dry run completed. No packages were upgraded.{Style.RESET_ALL}")
            return
        
        # If interactive mode is enabled and there are many packages, ask for general confirmation
        if self.interactive and len(outdated) > 5:
            response = input(f"\n{Fore.YELLOW}Are you sure you want to upgrade {len(outdated)} packages? (Y/n): {Style.RESET_ALL}").strip().lower()
            if response and response != 'y':
                print(f"{Fore.YELLOW}⏸️ Upgrade process cancelled by user.{Style.RESET_ALL}")
                return
        
        # Batch mode for faster upgrades if enabled and not in interactive mode
        batch_results = []
        if self.batch_mode and not self.interactive:
            start_time = time.time()
            batch_results = self.batch_upgrade_packages(outdated)
            
            # If batch upgrade was successful, we're done
            if batch_results:
                successful = sum(1 for _, success, _ in batch_results if success)
                failed = len(batch_results) - successful
                
                print(f"\n{Fore.BLUE}📊 Batch Summary:{Style.RESET_ALL}")
                print(f"  • {Fore.GREEN}Succeeded: {successful}{Style.RESET_ALL}")
                print(f"  • {Fore.RED}Failed: {failed}{Style.RESET_ALL}")
                print(f"  • {Fore.BLUE}Total time: {time.time() - start_time:.1f} seconds{Style.RESET_ALL}")
                
                return
        
        # If batch mode failed or not enabled, fall back to individual upgrades
        print(f"\n{Fore.BLUE}🚀 Upgrading {len(outdated)} packages with {self.max_workers} workers...{Style.RESET_ALL}")
        successful = 0
        failed = 0
        skipped = 0
        
        # Start timer for performance measurement
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # If interactive mode is enabled, process packages sequentially
            if self.interactive:
                for i, pkg in enumerate(outdated):
                    name, success, message = self.upgrade_package(pkg)
                    progress = f"[{i+1}/{len(outdated)}]"
                    
                    if success:
                        successful += 1
                        print(f"{Fore.GREEN}✓ {progress} {name}: {message}{Style.RESET_ALL}")
                    elif "Skipped by user" in message:
                        skipped += 1
                        print(f"{Fore.YELLOW}⏭️ {progress} {name}: {message}{Style.RESET_ALL}")
                    else:
                        failed += 1
                        print(f"{Fore.RED}✗ {progress} {name}: {message}{Style.RESET_ALL}")
                        
                        # Stop on first error unless continue_on_error is True
                        if not self.continue_on_error:
                            print(f"{Fore.YELLOW}⚠️ Stopping due to error. Use --continue-on-error to ignore failures.{Style.RESET_ALL}")
                            break
            else:
                # Process packages concurrently in non-interactive mode
                futures = {}
                
                # Submit all packages for upgrade
                for pkg in outdated:
                    future = executor.submit(self.upgrade_package, pkg)
                    futures[future] = pkg
                
                # Process results as they complete
                for i, future in enumerate(as_completed(futures)):
                    try:
                        name, success, message = future.result()
                        progress = f"[{i+1}/{len(outdated)}]"
                        
                        if success:
                            successful += 1
                            print(f"{Fore.GREEN}✓ {progress} {name}: {message}{Style.RESET_ALL}")
                        else:
                            failed += 1
                            print(f"{Fore.RED}✗ {progress} {name}: {message}{Style.RESET_ALL}")
                            
                    except Exception as e:
                        # This is a safety net for any unexpected errors in the thread
                        pkg = futures[future]
                        failed += 1
                        error_msg = f"Thread execution error: {str(e)}"
                        print(f"{Fore.RED}✗ [{i+1}/{len(outdated)}] {pkg['name']}: {error_msg}{Style.RESET_ALL}")
                        logger.error(f"{pkg['name']}: {error_msg}")
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Print summary with timing information
        print(f"\n{Fore.BLUE}📊 Summary:{Style.RESET_ALL}")
        print(f"  • {Fore.GREEN}Succeeded: {successful}{Style.RESET_ALL}")
        if skipped > 0:
            print(f"  • {Fore.YELLOW}Skipped: {skipped}{Style.RESET_ALL}")
        print(f"  • {Fore.RED}Failed: {failed}{Style.RESET_ALL}")
        print(f"  • {Fore.BLUE}Total time: {elapsed_time:.1f} seconds{Style.RESET_ALL}")

def parse_args():
    parser = argparse.ArgumentParser(description="Upgrade all outdated Python packages to the latest version.")
    
    # Basic options
    parser.add_argument("--dry-run", action="store_true", help="Only show outdated packages without upgrading")
    parser.add_argument("-i", "--interactive", action="store_true", help="Ask for confirmation before upgrading each package")
    
    # Package selection options
    package_group = parser.add_argument_group("Package Selection")
    package_group.add_argument("--include", nargs="+", help="Only upgrade specified packages")
    package_group.add_argument("--exclude", nargs="+", help="Skip upgrading specified packages")
    package_group.add_argument("--import", dest="import_file", help="Import list of packages to upgrade from a file")
    package_group.add_argument("--export", help="Export list of outdated packages to a file")
    
    # Performance options
    perf_group = parser.add_argument_group("Performance Options")
    perf_group.add_argument("--max-workers", type=int, default=10, help="Maximum number of concurrent upgrades (default: 10)")
    perf_group.add_argument("--timeout", type=int, default=300, help="Timeout in seconds for each package upgrade (default: 300)")
    perf_group.add_argument("--batch", action="store_true", help="Use batch mode to upgrade all packages in a single command (faster)")
    perf_group.add_argument("--continue-on-error", action="store_true", help="Continue upgrading packages even if some fail")
    
    # Environment options
    env_group = parser.add_argument_group("Environment Options")
    env_group.add_argument("--pip", help="Path to pip executable to use")
    env_group.add_argument("--venv", help="Path to virtual environment to use")
    
    # Logging options
    log_group = parser.add_argument_group("Logging Options") 
    log_group.add_argument("--log", help="Log file to save output")
    
    # Quick profiles (combined options)
    profile_group = parser.add_argument_group("Quick Profiles")
    profile_group.add_argument("--quick", action="store_true", help="Quick mode: batch upgrade with continue-on-error")
    profile_group.add_argument("--safe", action="store_true", help="Safe mode: interactive with low concurrency")
    
    args = parser.parse_args()
    
    # Apply profiles if specified
    if args.quick:
        args.batch = True
        args.continue_on_error = True
        args.max_workers = 20
    elif args.safe:
        args.interactive = True
        args.max_workers = 1
        args.continue_on_error = False
    
    return args

def main():
    args = parse_args()
    
    # Apply command line arguments
    upgrader = PipUpgrader(
        max_workers=args.max_workers,
        timeout=args.timeout,
        include=args.include,
        exclude=args.exclude,
        interactive=args.interactive,
        pip_executable=args.pip,
        venv=args.venv,
        batch_mode=args.batch,
        continue_on_error=args.continue_on_error,
        log_file=args.log
    )
    
    # Import package list if specified
    if args.import_file:
        outdated = upgrader.import_package_list(args.import_file)
    else:
        outdated = upgrader.get_outdated_packages()
    
    # Export package list if specified
    if args.export:
        upgrader.export_package_list(outdated, args.export)
        if args.dry_run:
            return
    
    # Upgrade all packages
    try:
        upgrader.upgrade_all_packages(outdated, dry_run=args.dry_run)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⏹️ Process interrupted by user.{Style.RESET_ALL}")
    
    if not args.dry_run:
        print(f"\n{Fore.GREEN}✨ Upgrade process completed!{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 