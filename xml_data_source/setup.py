from setuptools import setup, find_packages

setup(
    name="gviz-xml-datasource",
    version="1.0.0",
    description="Graph Visualizer – XML data source plugin",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "gviz-api",
        "gviz-platform",
    ],
    entry_points={
        "gviz.data_source": [
            "xml-data-source = xml_data_source.plugin:XMLDataSourcePlugin",
        ],
    },
)
