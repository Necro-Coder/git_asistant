from setuptools import setup, find_packages

setup(
    name="git-assistant",
    version="1.0.0",
    description="Asistente Git para consola",
    author="Rubén Núñez Cotano",
    author_email="",
    py_modules=["git_assistant_launcher"],
    install_requires=[
        "rich",
        "InquirerPy", 
        "pyyaml",
        "requests"
    ],
    entry_points={
        "console_scripts": [
            "git-assistant=git_assistant_launcher:main",
        ],
    },
    python_requires=">=3.7",
)