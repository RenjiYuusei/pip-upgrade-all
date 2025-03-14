# pip-upgrade-all  

Simple command line tool to upgrade all Python packages to the latest version.

## Install

```bash
pip install pip-upgrade-all
```

## Usage

Run the basic command:

```bash
pip-upgrade-all
```

### Command Line Options

```bash
pip-upgrade-all --help
```

#### Basic Options
```
  --dry-run             Only show outdated packages without upgrading
  -i, --interactive     Ask for confirmation before upgrading each package
```

#### Package Selection
```
  --include [INCLUDE ...]  Only upgrade specified packages
  --exclude [EXCLUDE ...]  Skip upgrading specified packages
  --import IMPORT_FILE     Import list of packages to upgrade from a file
  --export EXPORT          Export list of outdated packages to a file
```

#### Performance Options
```
  --max-workers MAX_WORKERS  Maximum number of concurrent upgrades (default: 10)
  --timeout TIMEOUT          Timeout in seconds for each package upgrade (default: 300)
  --batch                    Use batch mode to upgrade all packages in a single command (faster)
  --continue-on-error        Continue upgrading packages even if some fail
```

#### Environment Options
```
  --pip PIP             Path to pip executable to use
  --venv VENV           Path to virtual environment to use
```

#### Logging Options
```
  --log LOG             Log file to save output
```

#### Quick Profiles (Combined Options)
```
  --quick               Quick mode: batch upgrade with continue-on-error
  --safe                Safe mode: interactive with low concurrency
```

### Examples

Only show outdated packages without upgrading:
```bash
pip-upgrade-all --dry-run
```

Upgrade only specific packages:
```bash
pip-upgrade-all --include numpy pandas matplotlib
```

Skip upgrading certain packages:
```bash
pip-upgrade-all --exclude tensorflow torch
```

Increase concurrency to 20 workers:
```bash
pip-upgrade-all --max-workers 20
```

Interactive mode (ask for confirmation before each upgrade):
```bash
pip-upgrade-all -i
```

Export list of outdated packages to a file:
```bash
pip-upgrade-all --dry-run --export packages.json
```

Import and upgrade from a previously exported list:
```bash
pip-upgrade-all --import packages.json
```

Use a specific virtual environment:
```bash
pip-upgrade-all --venv /path/to/venv
```

Faster upgrades with batch mode:
```bash
pip-upgrade-all --batch
```

Quick mode (fastest upgrade with error handling):
```bash
pip-upgrade-all --quick
```

Safe mode (careful upgrades):
```bash
pip-upgrade-all --safe
```

Log errors to file:
```bash
pip-upgrade-all --log upgrade.log
```

## Features

- 🔄 Automatically detect outdated packages
- ⚡ Upgrade multiple packages concurrently (default)
- ⚡⚡ Batch mode for ultra-fast upgrades
- 📊 Progress tracking and detailed summary reports
- 🎯 Command line interface with emoji and colors
- 🔧 Flexible configuration options
- 🔍 Include/exclude specific packages
- 🌈 Colorized output for better readability
- 🔐 Interactive mode for controlled upgrades
- 💾 Export/import package lists
- 🧪 Virtual environment support
- 📝 Logging to file for troubleshooting
- ⏱️ Performance improvements and timing reports
- 🔨 Error handling and recovery
- 🔄 Continuous operation with continue-on-error option
- 🚀 Quick profiles for common use cases

## Requirements

- Python 3.10 or higher

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) for more details. 