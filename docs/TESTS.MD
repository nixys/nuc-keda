# Tests

This chart uses three complementary automated test layers:

- `tests/units/` for fast `helm-unittest` suites and backward-compatibility checks
- `tests/e2e/` for kind-based chart installation against real KEDA CRDs
- `tests/smokes/` for smoke scenarios that exercise full render flows

GitLab CI runs linting, unit tests, smoke tests, backward compatibility rendering, full example rendering, and `kubeconform`. The e2e layer is kept local because it has heavier infrastructure requirements and depends on Docker, kind, and outbound network access.

## Unit Tests

Unit tests live under `tests/units/`.

They are intentionally compact and focus on chart-owned behavior rather than repeating full KEDA payloads field by field.

## Unit Test Layout

```text
tests/units/
├── backward_compatibility_test.sh
├── example_resources_test.yaml
├── rendering_contract_test.yaml
└── values/
    └── rendering_contract.values.yaml
```

## Covered Unit Checks

The unit layer currently covers:

1. `rendering_contract_test.yaml`
   Verifies the generic rendering helper behavior used by all resource templates:
   - `nameOverride`
   - merged labels and annotations
   - namespace fallback for namespaced resources
   - omitted namespace for cluster-scoped `ClusterTriggerAuthentication`
   - global and per-resource `apiVersion` overrides

2. `example_resources_test.yaml`
   Uses `values.yaml.example` as a representative fixture and checks that:
   - all expected documents are rendered
   - each supported kind has a stable smoke-level assertion
   - the example stays aligned with the chart contract

3. `backward_compatibility_test.sh`
   Renders the current chart with `values.yaml` from previous stable git tags and verifies that:
   - old values files still pass `helm lint`
   - old values files still render with `helm template`
   - missing previous major, minor, or patch tags are treated as skip conditions rather than hard failures

## Running Unit Tests

Run all Helm unit suites:

```bash
helm unittest -f 'tests/units/*_test.yaml' .
```

Run the backward-compatibility script:

```bash
sh tests/units/backward_compatibility_test.sh
```

Notes:

- value file paths inside the unit suites are resolved relative to `tests/units/`
- the backward-compatibility script requires git tags to be available locally

## E2E Tests

End-to-end tests live under `tests/e2e/`.

This layer uses a shell runner around `kind` and Helm to validate that the chart can be installed into a real cluster with KEDA CRDs present.

## E2E Layout

```text
tests/e2e/
├── kind.yaml
├── test-e2e.sh
└── values/
    └── install.values.yaml
```

## What the E2E Runner Does

`tests/e2e/test-e2e.sh` performs the following steps:

1. Starts a disposable kind cluster from `tests/e2e/kind.yaml`.
2. Installs the KEDA CRDs from a pinned upstream release.
3. Runs `helm upgrade --install` against the chart root with `tests/e2e/values/install.values.yaml`.
4. Verifies the installed `ScaledObject`, `ScaledJob`, `TriggerAuthentication`, and `ClusterTriggerAuthentication` objects with `kubectl get`.
5. Cleans up the kind cluster on exit.

## Running E2E Tests

Run the default end-to-end flow:

```bash
bash tests/e2e/test-e2e.sh
```

Pass additional arguments through to `helm upgrade --install`:

```bash
bash tests/e2e/test-e2e.sh --debug
```

The repository also includes a local convenience [Makefile](../Makefile) for these flows:

```bash
make test-e2e
make test-e2e-debug
make test-e2e-help
```

To pass extra arguments to the shell runner through `make`, use `E2E_ARGS`:

```bash
make test-e2e E2E_ARGS="--debug"
```

## E2E Prerequisites

- `kubectl`
- `helm`
- outbound access to fetch the KEDA CRDs

For local disposable-cluster runs only:

- `docker`
- `kind`

Optional environment overrides:

- `CLUSTER_NAME`
- `K8S_VERSION`
- `KEDA_VERSION`

## Smoke Tests

This chart includes smoke tests under `tests/smokes/`.

The structure is intentionally split into small reusable layers:

- `run/` contains the entry point
- `scenarios/` orchestrate complete smoke flows
- `steps/` contain reusable operations
- `fixtures/` contain dedicated smoke-test values files

## Directory Layout

```text
tests/smokes/
├── helpers/
│   └── argparser.py
├── fixtures/
│   ├── invalid-list-contract.values.yaml
│   └── rendering-contract.values.yaml
├── run/
│   └── smoke.py
├── scenarios/
│   └── smoke.py
├── steps/
│   ├── chart.py
│   ├── helm.py
│   ├── kubeconform.py
│   ├── render.py
│   └── system.py
└── requirements.txt
```

## Covered Scenarios

The smoke suite currently covers:

1. `default-empty`
   Verifies that the chart renders no manifests with default values.

2. `schema-invalid-list-contract`
   Verifies that `values.schema.json` is active and rejects the old list-based contract for top-level resource collections.

3. `rendering-contract`
   Verifies chart-owned behavior rather than CRD payload content:
   - `nameOverride`
   - merged labels and annotations
   - namespace fallback for namespaced resources
   - cluster-scoped `ClusterTriggerAuthentication`
   - global and per-resource `apiVersion` override behavior

4. `example-render`
   Renders `values.yaml.example` and verifies that all supported resource kinds are produced from the example configuration.

5. `example-kubeconform`
   Renders `values.yaml.example` and validates the result with `kubeconform` using the same KEDA CRD schema location as CI.

## Prerequisites

- `python3`
- `helm`
- `kubeconform` for the `example-kubeconform` scenario
- `PyYAML`

Install Python dependency:

```bash
pip3 install -r tests/smokes/requirements.txt
```

## How the Suite Works

The smoke runner does not execute Helm directly in the repository root.

Instead it stages a temporary clean copy of the chart that includes only:

- `Chart.yaml`
- `values.yaml`
- `values.yaml.example`
- `values.schema.json`
- `templates/`

This keeps smoke tests isolated from unrelated files in the repository root and makes Helm execution deterministic.

## Running All Smoke Tests

From the repository root:

```bash
python3 tests/smokes/run/smoke.py
```

Equivalent `Makefile` targets:

```bash
make test-smoke
make test-smoke-fast
```

## Running Individual Scenarios

Run only one scenario:

```bash
python3 tests/smokes/run/smoke.py --scenario rendering-contract
```

Run multiple scenarios:

```bash
python3 tests/smokes/run/smoke.py \
  --scenario default-empty \
  --scenario example-render
```
