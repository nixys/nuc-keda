# Development Dependencies

This document describes the local tools needed to develop, document, and test the `nuc-keda` Helm chart.

The repository is designed around a small set of entry points:

- `make lint`
- `make docs`
- `make test-unit`
- `make test-compat`
- `make test-smoke`
- `make test-e2e`

## Dependency Matrix

| Tool | Why it is needed | Required for |
|------|------------------|--------------|
| `git` | repository operations and reading tagged `values.yaml` in compatibility checks | development, `make test-compat` |
| `helm` | linting, templating, install/upgrade flows, `helm-unittest` plugin host | all workflows |
| `helm-unittest` | chart unit test plugin | `make test-unit` |
| `python3` | smoke-test runner | `make test-smoke`, `make test-smoke-fast` |
| `PyYAML` | smoke-test Python dependency | `make test-smoke`, `make test-smoke-fast` |
| `kubeconform` | schema validation in smoke tests and CI parity checks | `example-kubeconform`, optional local validation |
| `pre-commit` | local git hook manager for auto-regenerating `README.md` on commit | documentation workflow |
| `helm-docs` | README values-table generator | `make docs`, pre-commit hook |
| `docker` | `kind` runtime and fallback runtime for `helm-docs` wrapper | `make test-e2e`, optional `make docs` |
| `kubectl` | cluster verification in e2e tests | `make test-e2e` |
| `kind` | disposable local Kubernetes cluster for e2e | `make test-e2e` |

## Repository Defaults

If you want local behavior close to the repository defaults, use these versions:

- `kubeconform`: `v0.6.7` in CI
- `kindest/node`: `v1.35.0` in `tests/e2e/test-e2e.sh`
- `KUBE_VERSION`: `1.35.2` for `kubeconform`
- `KEDA_VERSION`: `2.18.2` in `tests/e2e/test-e2e.sh`

The chart itself is not tightly pinned to one local Helm binary version, but CI currently uses `alpine/helm:4`.

## macOS Setup

For macOS with Homebrew, the shortest local setup is:

```bash
brew install git helm kubectl kind kubeconform pre-commit python
brew install norwoodj/tap/helm-docs
pip3 install -r tests/smokes/requirements.txt
helm plugin install https://github.com/helm-unittest/helm-unittest.git
```

For Docker, install Docker Desktop or another compatible Docker runtime before running `make test-e2e`.

## Ubuntu or Debian Setup

Install the common base packages first:

```bash
sudo apt-get update
sudo apt-get install -y \
  git \
  curl \
  ca-certificates \
  gnupg \
  python3 \
  python3-pip
```

Install Helm from the official Helm apt repository:

```bash
sudo apt-get install curl gpg apt-transport-https --yes
curl -fsSL https://packages.buildkite.com/helm-linux/helm-debian/gpgkey \
  | gpg --dearmor \
  | sudo tee /usr/share/keyrings/helm.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/helm.gpg] https://packages.buildkite.com/helm-linux/helm-debian/any/ any main" \
  | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install -y helm
```

Install `kubectl` from the official Kubernetes package repository. The example below tracks the `v1.35` stream, which matches this repository's current defaults:

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
sudo mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.35/deb/Release.key \
  | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
sudo chmod 644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /' \
  | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo chmod 644 /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubectl
```

Install `kind` from the official release binaries:

```bash
[ "$(uname -m)" = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.31.0/kind-linux-amd64
[ "$(uname -m)" = aarch64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.31.0/kind-linux-arm64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

Install `kubeconform` with the same version used in CI. Change the archive suffix to `arm64` if needed:

```bash
curl -fsSL https://github.com/yannh/kubeconform/releases/download/v0.6.7/kubeconform-linux-amd64.tar.gz \
  | tar -xz kubeconform
sudo mv kubeconform /usr/local/bin/kubeconform
```

Install the Python dependency, the Helm unit-test plugin, and the git hook manager:

```bash
pip3 install -r tests/smokes/requirements.txt
pip3 install pre-commit
helm plugin install https://github.com/helm-unittest/helm-unittest.git
```

For `helm-docs`, either install the binary directly:

```bash
go install github.com/norwoodj/helm-docs/cmd/helm-docs@latest
```

or rely on the repository wrapper `scripts/helm-docs.sh`, which will use Docker if `helm-docs` is not present in `PATH`.

For Docker, install Docker Engine or Docker Desktop using the official Docker instructions for your distribution before running `make test-e2e`.

## Windows Notes

The repository's e2e and compatibility flows are shell-based. On Windows, prefer WSL2 with the Linux instructions above. If you work natively on Windows, install `helm`, `kubectl`, `kind`, Docker Desktop, Python, and `pre-commit` with the official Windows installers or package managers, and run the chart scripts from a POSIX-compatible shell.

## Post-Install Steps

After installing the tools, initialize the repository-specific hooks and plugins:

```bash
make hooks-install
pip3 install -r tests/smokes/requirements.txt
helm plugin list
pre-commit --version
```

If `helm-unittest` is not listed yet:

```bash
helm plugin install https://github.com/helm-unittest/helm-unittest.git
```

## Verification Commands

Use these commands to verify that the local toolchain is complete:

```bash
git --version
helm version
kubectl version --client
kind version
docker version
python3 --version
pre-commit --version
kubeconform -v
helm plugin list
make lint
make test-smoke-fast
```

Run the heavier checks only when their dependencies are available:

```bash
make test-unit
make test-compat
make test-smoke
make test-e2e
make docs
```

## Official References

- [Helm installation](https://helm.sh/docs/intro/install/)
- [kubectl installation](https://kubernetes.io/docs/tasks/tools/)
- [kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/)
- [pre-commit installation and usage](https://pre-commit.com/)
- [helm-docs](https://github.com/norwoodj/helm-docs)
- [helm-unittest](https://github.com/helm-unittest/helm-unittest)
- [kubeconform](https://github.com/yannh/kubeconform)
- [KEDA releases](https://github.com/kedacore/keda/releases)
- [Docker Engine and Docker Desktop](https://docs.docker.com/engine/)
