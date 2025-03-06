from setuptools import setup, find_packages

setup(
    name="finance_tracker",
    version="0.1",
    description="A financial tracking desktop application",
    author="Your Name",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "PyQt6>=6.4.0",
        "pyobjc-framework-LocalAuthentication>=9.2",
        "keyring>=23.0.0",
        "SQLAlchemy>=2.0.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0"
    ]
)