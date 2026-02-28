from setuptools import setup, find_packages

setup(
    name="gviz-platform",
    version="1.0.0",
    description="Graph Visualizer Platform – core graph engine and plugin manager",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "gviz-api",
    ],
)
