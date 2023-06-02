from setuptools import setup


setup(
    name="oaemapi",
    version=open("app/version", "r").read(),
    description="Obstruction Adaptive Elevation Mask API (OAEM-API)",
    author="Gereon Tombrink",
    author_email="tombrink@igg.uni-bonn.de",
    url="https://github.com/gereon-t",
    license="MIT",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    keywords=["sky obstruction", "elevation mask", "obstruction adaptive", "OAEM", "OAEM-API", "OAEM API", "GNSS"],
    packages={"": "oaemapi"},
    package_data={"oaemapi": ["version", "LICENSE"]},
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "anyio>=3.7.0",
        "black>=23.3.0",
        "certifi>=2023.5.7",
        "charset-normalizer>=3.1.0",
        "click>=8.1.3",
        "contourpy>=1.0.7",
        "cycler>=0.11.0",
        "dnspython>=2.3.0",
        "email-validator>=2.0.0.post2",
        "fastapi>=0.95.2",
        "fonttools>=4.39.4",
        "h11>=0.14.0",
        "httpcore>=0.17.2",
        "httptools>=0.5.0",
        "httpx>=0.24.1",
        "idna>=3.4",
        "itsdangerous>=2.1.2",
        "Jinja2>=3.1.2",
        "kiwisolver>=1.4.4",
        "MarkupSafe>=2.1.2",
        "matplotlib>=3.7.1",
        "mypy-extensions>=1.0.0",
        "numpy>=1.24.3",
        "orjson>=3.8.14",
        "packaging>=23.1",
        "pandas>=2.0.2",
        "pathspec>=0.11.1",
        "Pillow>=9.5.0",
        "platformdirs>=3.5.1",
        "plotly>=5.14.1",
        "pointset>=0.1.5",
        "pydantic>=1.10.8",
        "pyparsing>=3.0.9",
        "pyproj>=3.5.0",
        "python-dateutil>=2.8.2",
        "python-dotenv>=1.0.0",
        "python-multipart>=0.0.6",
        "pytz>=2023.3",
        "PyYAML>=6.0",
        "requests>=2.31.0",
        "scipy>=1.10.1",
        "six>=1.16.0",
        "sniffio>=1.3.0",
        "starlette>=0.27.0",
        "tenacity>=8.2.2",
        "typing_extensions>=4.6.2",
        "tzdata>=2023.3",
        "ujson>=5.7.0",
        "urllib3>=2.0.2",
        "uvicorn>=0.22.0",
        "watchfiles>=0.19.0",
        "websockets>=11.0.3",
        "xmltodict>=0.13.0",
    ],
    entry_points={
        "console_scripts": [
            "oaemapi = app.__main__:main",
        ],
    },
)
