"""Copyright 2022-  René Rohner

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License."""

from setuptools import setup
from setuptools import find_packages
import re
from pathlib import Path

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open(Path("src", "RetryFailed", "__init__.py"), encoding="utf-8") as f:
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
