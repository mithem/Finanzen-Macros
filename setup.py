from setuptools import setup

VERSION = "0.1.0"

requirements = [
"numpy",
"tox==3"
]

with open("requirements.txt", "w") as f:
    requirements = f.writelines(r + "\n" for r in requirements)

setup(
    name="finance_macros",
    version=VERSION,
    packages=["finance_macros"],
    install_requires=requirements,)
