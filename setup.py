from setuptools import setup, find_packages

setup(
    name="survey123-assistant",
    version="1.0.0",
    packages=["xlsform_orm"],
    package_dir={"": "src"},
    install_requires=[
        "pandas",
        "pydantic",
        "pyyaml",
        "streamlit",
        "openai",
        "pillow>=10.2.0",
    ],
)
