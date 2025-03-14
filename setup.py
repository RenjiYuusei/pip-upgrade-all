from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pip-upgrade-all",
    version="0.4.0",
    packages=find_packages(),
    install_requires=[
        "packaging",
        "colorama",
    ],
    entry_points={
        "console_scripts": [
            "pip-upgrade-all=pip_upgrade.main:main",
        ],
    },
    author="Yuusei",
    author_email="daoluc.yy@gmail.com",
    description="A tool to upgrade all outdated Python packages to their latest versions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RenjiYuusei/pip-upgrade-all",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
) 
