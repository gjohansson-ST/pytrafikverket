"""Setup for pytrafikverket."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="UTF-8") as fh:
    long_description = fh.read()

setup(
    name="pytrafikverket",
    version="0.3.9",
    description="Retreive values from public API at the Swedish Transport Administration (Trafikverket).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gjohansson-ST/pytrafikverket",
    author="Peter Andersson, Jonas Karlsson, G Johansson",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
    ],
    install_requires=["aiohttp", "lxml"],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    entry_point={
        "console_scripts": ["pytrafikverket=pytrafikverket.pytrafikverket:main"]
    },
    package_data={"pytrafikverket": ["py.typed"]},
)
