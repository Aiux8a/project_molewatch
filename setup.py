from setuptools import find_packages, setup

with open("requirements.txt") as f:
    content = f.readlines()
requirements = [x.strip() for x in content if "git+" not in x]

setup(
    name="molewatch_app",
    version="0.0.1",
    description="MoleWatch Skin Lesion Detection API",
    packages=find_packages(),
    install_requires=requirements,
)
