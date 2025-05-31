from setuptools import setup, find_packages

setup(
    name="esgis_chatbot",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # Les dépendances principales seront gérées par requirements.txt
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "esgis-webhook=utils.webhook_cli:main",
        ],
    },
)
