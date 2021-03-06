import setuptools
from distutils.util import convert_path

ns = {}
ver_path = convert_path("casper/version.py")
with open(ver_path) as ver_file:
    exec(ver_file.read(), ns)
__version__ = ns["__version__"]


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aws-terraform-casper",
    version=__version__,
    author="Obaro Odiete",
    author_email="mybytesni@gmail.com",
    description="A tool for detecting resources running on your AWS cloud "
    "environment but not provisioned through Terraform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/edeas123/aws-terraform-casper",
    packages=setuptools.find_packages(exclude=("tests", "docs")),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
    ],
    install_requires=["boto3>=1.10.41", "docopt>=0.6.2"],
    python_requires=">=3.6",
    entry_points={"console_scripts": ["casper=casper.main:cli"],},
)
