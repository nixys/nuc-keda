# Contributing Guidelines

Contributions are welcome via GitHub pull requests. This document outlines the process to help get your contribution accepted.

## Sign off Your Work

The Developer Certificate of Origin (DCO) is a lightweight way for contributors to certify that they wrote or otherwise have the right to submit the code they are contributing to the project.
Here is the full text of the [DCO](http://developercertificate.org/).
Contributors must sign-off that they adhere to these requirements by adding a `Signed-off-by` line to commit messages.

```text
This is my commit message

Signed-off-by: Random J Developer <random@developer.example.org>
```

See `git help commit`:

```text
-s, --signoff
    Add Signed-off-by line by the committer at the end of the commit log
    message. The meaning of a signoff depends on the project, but it typically
    certifies that committer has the rights to submit this work under the same
    license and agrees to a Developer Certificate of Origin (see
    http://developercertificate.org/ for more information).
```

## How to Contribute

1. Fork this repository, develop, and test your changes
1. Remember to sign off your commits as described above
1. Submit a pull request

Keep each pull request scoped to one logical chart change so the rendered manifests, tests, and docs can be reviewed together.

### Technical Requirements

* Must pass [DCO check](#sign-off-your-work)
* Must follow [Charts best practices](https://helm.sh/docs/topics/chart_best_practices/)
* Must pass the repository CI checks for linting, unit tests, smoke tests, render checks, and schema validation
* Must update generated documentation when the values contract changes
* Any change to a chart should follow the repository versioning policy described below

When values or chart metadata change, refresh the README through the `helm-docs` hook before submitting the pull request.

### Immutability

Chart releases must be immutable. Any published chart change that affects templates, defaults, schema, or public documentation should be versioned deliberately.

### Versioning

The chart `version` should follow [semver](https://semver.org/). Any breaking (backwards incompatible) change to the values contract or rendered manifests should:

1. Bump the MAJOR version
2. In the README, under a section called "Upgrading", describe the manual steps necessary to upgrade to the new (specified) MAJOR version

### Generate README

The chart README is generated from [docs/README.md.gotmpl](README.md.gotmpl) and [values.yaml](../values.yaml) with [`norwoodj/helm-docs`](https://github.com/norwoodj/helm-docs).

Install the local git hook once:

```shell
pre-commit install
pre-commit install-hooks
```

Regenerate the README on demand:

```shell
pre-commit run helm-docs --all-files
```

Or use the local wrapper:

```shell
make docs
```

The hook uses `norwoodj/helm-docs` through `scripts/helm-docs.sh`: it prefers a local `helm-docs` binary and falls back to the official Docker image `jnorwood/helm-docs:v1.14.2`.

### Community Requirements

This project is released with a [Contributor Covenant](https://www.contributor-covenant.org).
By participating in this project you agree to abide by its terms.
See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).
