from setuptools import setup, find_packages

setup(
    name="bitmask_filtering",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
    ],
    python_requires=">=3.7",
) 