from setuptools import find_packages, setup


setup(
    name="gviz-block-visualizer",
    version="1.0.0",
    description="Graph Visualizer - block visualizer plugin",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "gviz-api",
    ],
    entry_points={
        "gviz.visualizer": [
            "block-visualizer = block_visualizer.plugin:BlockVisualizerPlugin",
        ],
    },
)
