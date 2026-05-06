from setuptools import setup, find_packages
from pathlib import Path

DESCRIPTION = 'Open-source interface for processing recreation-grade side scan sonar datasets and reproducibly mapping benthic habitat'
LONG_DESCRIPTION = Path('README.md').read_text()

exec(open('pingmapper/version.py').read())

setup(
    name="pingmapper",
    version=__version__,
    author="Cameron Bodine, Daniel Buscombe",
    author_email="bodine.cs@gmail.email",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    data_files=[("pingmapper_config", ["pingmapper/default_params.json"])],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Scientific/Engineering :: Oceanography",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Hydrology"
        ],
    keywords=[
        "pingmapper",
        "sonar",
        "ecology",
        "remotesensing",
        "sidescan",
        "sidescan-sonar",
        "aquatic",
        "humminbird",
        "lowrance",
        "gis",
        "oceanography",
        "limnology",],
    python_requires=">=3.6",
    install_requires=['pinginstaller', 'pingwizard', 'pingverter'],
    project_urls={
        "Issues": "https://github.com/CameronBodine/PINGMapper/issues",
        "GitHub":"https://github.com/CameronBodine/PINGMapper",
        "Homepage":"https://cameronbodine.github.io/PINGMapper/",
    },
)