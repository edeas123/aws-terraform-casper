import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aws-terraform-casper",
    version="0.2.0",
    author="Obaro Odiete",
    author_email="mybytesni@gmail.com",
    description="A tool for detecting resources running on your AWS cloud "
                "environment but not provisioned through Terraform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/edeas123/aws-terraform-casper",
    packages=setuptools.find_packages(exclude=('tests',)),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'boto3==1.10.41'
    ],
    python_requires='>=3.6',
)
