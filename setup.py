from setuptools import setup

VERSION = "0.1.0"

requirements = [
    "numpy",
    "tox==4.*",
    "pylint_exit",
    "pylint",
    "mypy",
    "pytest",
    "pytest-cov",
]

with open("requirements.txt", "w", encoding="utf-8") as f:
    requirements = f.writelines(r + "\n" for r in requirements)

setup(
    name="finance_macros",
    version=VERSION,
    packages=["finance_macros"],
    install_requires=requirements,
)
