from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

TESTS_REQUIRE = [
    "selenium~=3.141",
    "pylint",
    "mock",
    "black",
    "bandit==1.7.1",  # Version locked due to python 3.6 dependancey
    "pytest-xdist",
]

setup(
    name="webviz_4d",
    description="webviz-4d",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="Equinor",
    packages=find_packages(exclude=["tests"]),
    entry_points={
        "webviz_config_plugins": [
            "SurfaceViewer4D = webviz_4d.plugins:SurfaceViewer4D",
        ]
    },
    install_requires=[
        "webviz-config>=0.6.3",
        "xtgeo~=2.21,
        "pillow~=10.4",
        "webviz-subsurface-components==0.4.15",
    ],
    tests_require=TESTS_REQUIRE,
    extras_require={"tests": TESTS_REQUIRE},
    setup_requires=["setuptools_scm~=3.2"],
    use_scm_version=True,
    zip_safe=False,
    classifiers=[
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    project_urls={
        "Source": "https://github.com/equinor/webviz-4d",
        "Tracker": "https://github.com/equinor/webviz-4d/issues",
    },
)
