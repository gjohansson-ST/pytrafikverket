"""Setup for pytrafikverket."""

from setuptools import setup

setup(
    name="pytrafikverket",
    version="0.1.6.1",
    description="api for trafikverket in sweden",
    url="https://github.com/AnderssonPeter/pytrafikverket",
    author="Peter Andersson",
    license="MIT",
    install_requires=["aiohttp", "async-timeout", "lxml"],
    packages=["pytrafikverket"],
    zip_safe=True,
    entry_point={
        "console_scripts": ["pytrafikverket=pytrafikverket.pytrafikverket:main"]
    },
)
