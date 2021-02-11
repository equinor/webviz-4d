## webviz-4d

### Introduction

This repository contains a webviz-subsurface plugin decicated for visualization of 4D attribute maps, which can be used
together with other plugins in [webviz-config](https://github.com/equinor/webviz-config).

Made using [webviz-container-boilerplate](https://github.com/equinor/webviz-container-boilerplate)


### Installation

The easiest way of installing this local package is to run
```bash
pip install .
```

If you want to install test and linting dependencies, you can in addition run
```bash
pip install .[tests]
```

### Linting

You can do automatic linting of your code changes by running
```bash
black --check webviz_4d # Check code style
pylint webviz_4d # Check code quality
bandit -r webviz_4d  # Check Python security best practice
```

### Usage and documentation

For general usage, see the documentation on
[webviz-config](https://github.com/equinor/webviz-config).
