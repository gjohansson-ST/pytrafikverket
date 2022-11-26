"""Setup for pytrafikverket."""

from setuptools import setup

setup(
    name="pytrafikverket",
    version="0.2.2",
    description="Retreive values from public API at the Swedish Transport Administration (Trafikverket).",
    url="https://github.com/endor-force/pytrafikverket",
    author="Peter Andersson, Jonas Karlsson",
    license="MIT",
    install_requires=["aiohttp", "async-timeout", "lxml"],
    packages=["pytrafikverket"],
    zip_safe=True,
    entry_point={
        "console_scripts": ["pytrafikverket=pytrafikverket.pytrafikverket:main"]
    },
)
