from setuptools import setup, find_packages

setup(
    name="music_cli",
    version="0.0.1",
    description="A simple command-line music player",
    long_description=open('README.md').read(),
    author="Klka",
    author_email="klka@duck.com",
    url="https://github.com/kamalkoranga/music_cli.git",
    packages=find_packages(),
    install_requires=[
        "yt-dlp",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "music_cli=MUSIC_CLI.music_cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
