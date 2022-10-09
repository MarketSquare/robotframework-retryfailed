from setuptools import setup
from setuptools import find_packages
import re
from pathlib import Path

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open(Path("src", "RetryFaild", "__init__.py"), encoding="utf-8") as f:
    VERSION = re.search('\n__version__ = "(.*)"', f.read()).group(1)

setup(
    name="robotframework-retryfailed",
    version=VERSION,
    author="René Rohner(Snooz82)",
    author_email="snooz@posteo.de",
    description="A listener to automatically retry tests or tasks based on flags.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MarketSquare/robotframework-retryfailed",
    package_dir={"": "src"},
    packages=find_packages("src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Testing :: Acceptance",
        "Framework :: Robot Framework",
    ],
    install_requires=["robotframework >= 4.1"],
    python_requires=">=3.8.0",
)
