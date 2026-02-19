from setuptools import setup

setup(
    name="ntn",
    version="0.1.0",
    py_modules=["ntn"],
    install_requires=[
        "notion-client>=2.2.1",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "ntn=ntn:main",
        ],
    },
    python_requires=">=3.9",
)
