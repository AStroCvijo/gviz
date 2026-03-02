from setuptools import find_packages, setup


setup(
    name="gviz-simple-visualizer",
    version="1.0.0",
    description="Graph Visualizer - simple visualizer plugin",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "gviz-api",
    ],
    entry_points={
        "gviz.visualizer": [
            "simple-visualizer = simple_visualizer.plugin:SimpleVisualizerPlugin",
        ],
    },
)
