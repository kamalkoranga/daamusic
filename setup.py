from setuptools import setup, find_packages

setup(
    name="klkamusic_cli",
    version="0.1.2",
    description="A simple command-line music player for developers, that is built using yt-dlp and rich.",
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
            "klkamusic_cli=KLKAMUSIC_CLI.klkamusic_cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
