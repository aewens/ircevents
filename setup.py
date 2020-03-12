import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
with open("VERSION", "r") as version_file:
    version = version_file.read().strip()
with open("requirements.txt", "r") as requirements_file:
    install_requires = requirements_file.read().splitlines()

setuptools.setup(
    name="ircevents",
    version=version,
    author="aewens",
    author_email="email@aewens.com",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aewens/ircevents",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Communications :: Chat :: Internet Relay Chat"
    ],
    python_requires='>=3.6',
    install_requires=install_requires
)
