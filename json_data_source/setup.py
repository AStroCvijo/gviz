from setuptools import setup, find_packages

setup(
    name="gviz-json-datasource",
    version="1.0.0",
    description="Graph Visualizer – JSON data source plugin",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "gviz-api",
        "gviz-platform",
    ],
    entry_points={
        # The platform discovers this plugin via the entry-point group
        # 'gviz.data_source'.  The key ('json-data-source') must match
        # what JSONDataSourcePlugin.get_name() returns.
        "gviz.data_source": [
            "json-data-source = json_data_source.plugin:JSONDataSourcePlugin",
        ],
    },
)
