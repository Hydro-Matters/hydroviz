import os
from setuptools import setup

setup(
    name = "swotdawgviz",
    version = "0.0.1",
    author = "Kevin Larnier",
    author_email = "kevin.larnier@csgroup.eu",
    description = ("Visualisation library for the SWOT Discharge Algorithm Working Group"),
    license = "GNU",
    url = "https://github.com/klarnier/swotdawgviz",
    packages=['swotdawgviz', 'swotdawgviz.io', 'swotdawgviz.maps', 'swotdawgviz.plots'],
)
