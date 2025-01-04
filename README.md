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

Or use with options:

```bash
# Skip some packages when upgrading
pip-upgrade-all --skip package1 package2

# Disable concurrent upgrade
pip-upgrade-all --no-concurrent

# Specify the number of workers for concurrent upgrade
pip-upgrade-all --workers 3

# Specify the maximum version to upgrade to
pip-upgrade-all --max-version 2.0.0

# Save upgrade report to a file
pip-upgrade-all --report report.txt

# Save logs to a file
pip-upgrade-all --log log.txt

# Upgrade all packages to the latest version
pip-upgrade-all --timeout 300 # Upgrade timeout in seconds

```

## Features

- 🔄 Automatically detect outdated packages
- ⚡ Upgrade multiple packages concurrently (default)
- 🎯 Skip specific packages
- 📊 Display progress and summary details
- 📝 Generate detailed upgrade reports
- 📋 Save logs to file
- 🛡️ Handle errors and dependencies safely
- 🎨 Command line interface with emoji

## Requirements

- Python 3.10 or higher
- pip

## Command line parameters

```
--skip, -s         List of packages to skip when upgrading
--no-concurrent    Disable concurrent upgrade
--workers, -w      Number of workers for concurrent upgrade (default: 5)
--max-version, -m  Maximum version to upgrade to (e.g. 2.0.0)
--log, -l          Path to log file
--report, -r       Path to save upgrade report
--timeout, -t      Upgrade timeout in seconds (default: 300)
```

## License

This project is licensed under the MIT License - see the LICENSE file for more details. 