# pip-upgrade

Simple command line tool to upgrade all Python packages to the latest version.

## Install

```bash
pip install pip-upgrade
```

## Usage

Run the basic command:

```bash
pip-upgrade
```

Or use with options:

```bash
# Skip some packages when upgrading
pip-upgrade --skip package1 package2

# Disable concurrent upgrade
pip-upgrade --no-concurrent

# Specify the number of workers for concurrent upgrade
pip-upgrade --workers 3
```

## Features

- 🔄 Automatically detect outdated packages
- ⚡ Upgrade multiple packages concurrently (default)
- 🎯 Skip specific packages
- 📊 Display progress and summary details
- ⏱️ Track upgrade time
- 🛡️ Handle errors and dependencies safely
- 🎨 Command line interface with emoji

## Requirements

- Python 3.6 or higher
- pip

## Command line parameters

```
--skip, -s         List of packages to skip when upgrading
--no-concurrent    Disable concurrent upgrade
--workers, -w      Number of workers for concurrent upgrade (default: 5)
```

## License

This project is licensed under the MIT License - see the LICENSE file for more details. 