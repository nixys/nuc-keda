# NUC KEDA

Helm chart for rendering KEDA custom resources from declarative values.

The chart does not install KEDA itself or its CRDs. It only renders KEDA resources that are already supported by the target cluster.

## Quick Start

Add the Nixys chart repository:

```bash
helm repo add nixys https://registry.nixys.io/chartrepo/public
# or
helm repo add nixys https://registry.nixys.ru/chartrepo/public
```

Install the chart:

```bash
helm install nuc-keda . \
  --namespace keda \
  --create-namespace \
  -f values.yaml.example
```

Install the local README generator hook:

```bash
pre-commit install
pre-commit install-hooks
```

## Supported Resources

The chart can render these KEDA kinds:

- `ScaledObject`
- `ScaledJob`
- `TriggerAuthentication`
- `ClusterTriggerAuthentication`

## Values Model

Each top-level map in [values.yaml](values.yaml) maps resource names to one resource kind:

- `scaledObjects`
- `scaledJobs`
- `triggerAuthentications`
- `clusterTriggerAuthentications`

Every map entry uses the same generic contract:

| Field | Required | Description |
|-------|----------|-------------|
| map key | yes | Resource name used for `metadata.name`. |
| `namespace` | no | Namespace for namespaced resources. Defaults to the Helm release namespace. Ignored for cluster-scoped resources. |
| `labels` | no | Labels merged on top of built-in chart labels and `commonLabels`. |
| `annotations` | no | Annotations merged on top of `commonAnnotations`. |
| `apiVersion` | no | Per-resource API version override. |
| `spec` | no | Raw resource spec rendered as-is. |
| `status` | no | Optional raw status block. Usually not managed through Helm in production. |

In a higher-precedence values file, set a map entry to `null` to suppress a default resource from a lower-precedence values file.

Global controls:

- `enabled`
- `global` (accepted for umbrella-chart compatibility and ignored by this chart)
- `nameOverride`
- `commonLabels`
- `commonAnnotations`
- `apiVersions.*`

The value contract is validated by [values.schema.json](values.schema.json).

## Helm Values

This section is generated from [values.yaml](values.yaml) by `helm-docs`. Edit [values.yaml](values.yaml) comments or [docs/README.md.gotmpl](docs/README.md.gotmpl), then run `pre-commit run helm-docs --all-files` or `make docs` if you need to refresh it outside a commit.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| apiVersions.clusterTriggerAuthentication | string | `"keda.sh/v1alpha1"` | Default apiVersion for ClusterTriggerAuthentication resources. |
| apiVersions.scaledJob | string | `"keda.sh/v1alpha1"` | Default apiVersion for ScaledJob resources. |
| apiVersions.scaledObject | string | `"keda.sh/v1alpha1"` | Default apiVersion for ScaledObject resources. |
| apiVersions.triggerAuthentication | string | `"keda.sh/v1alpha1"` | Default apiVersion for TriggerAuthentication resources. |
| clusterTriggerAuthentications | object | {} | ClusterTriggerAuthentication resources keyed by resource name. |
| clusterTriggerAuthentications.__helm_docs_example__.namespace | string | "" | Namespace for namespaced resources. Ignored for cluster-scoped kinds. |
| commonAnnotations | object | `{}` | Extra annotations applied to every rendered resource. |
| commonLabels | object | `{}` | Extra labels applied to every rendered resource. |
| enabled | bool | `true` | Enable nuc-keda chart rendering. |
| global | object | `{}` | Compatibility values inherited from umbrella charts. Accepted but ignored by this chart. |
| nameOverride | string | `""` | Override the default chart label name if needed. |
| scaledJobs | object | {} | ScaledJob resources keyed by resource name. |
| scaledJobs.__helm_docs_example__.namespace | string | release namespace | Namespace for namespaced resources. Defaults to the Helm release namespace. |
| scaledObjects | object | {} | ScaledObject resources keyed by resource name. |
| scaledObjects.__helm_docs_example__.annotations | object | `{}` | Resource-specific annotations. |
| scaledObjects.__helm_docs_example__.apiVersion | string | chart default for this kind | Per-resource apiVersion override. |
| scaledObjects.__helm_docs_example__.labels | object | `{}` | Resource-specific labels. |
| scaledObjects.__helm_docs_example__.namespace | string | release namespace | Namespace for namespaced resources. Defaults to the Helm release namespace. |
| scaledObjects.__helm_docs_example__.spec | object | `{}` | Resource spec rendered as-is. |
| scaledObjects.__helm_docs_example__.status | object | `{}` | Optional resource status rendered as-is. |
| triggerAuthentications | object | {} | TriggerAuthentication resources keyed by resource name. |
| triggerAuthentications.__helm_docs_example__.namespace | string | release namespace | Namespace for namespaced resources. Defaults to the Helm release namespace. |

## Included Values Files

- [values.yaml](values.yaml): minimal defaults that render no resources.
- [values.yaml.example](values.yaml.example): complete example covering every supported resource type.

Use [values.yaml.example](values.yaml.example) as a starting point and remove the resource-name keys you do not need.

## Testing

The repository uses three test layers:

- `tests/units/` for `helm-unittest` suites and backward compatibility checks
- `tests/e2e/` for local kind-based Helm install checks against real KEDA CRDs
- `tests/smokes/` for render and schema smoke scenarios

Representative local commands:

```bash
helm lint . -f values.yaml.example
helm template nuc-keda . -f values.yaml.example
helm unittest -f 'tests/units/*_test.yaml' .
sh tests/units/backward_compatibility_test.sh
python3 tests/smokes/run/smoke.py --scenario example-render
make test-e2e
```

Detailed test documentation is available in [docs/TESTS.MD](docs/TESTS.MD).

Local setup instructions for the development and test toolchain are available in [docs/DEPENDENCY.md](docs/DEPENDENCY.md).

The `e2e` layer is intentionally kept out of GitLab CI and is expected to be run locally through [Makefile](Makefile) or directly via `tests/e2e/test-e2e.sh`.

## Notes

- Keep the chart API versions aligned with the KEDA CRDs installed in the cluster.
- `ClusterTriggerAuthentication` is cluster-scoped; all other supported resources are namespaced.
- Prefer managing `spec` through Helm and let controllers own `status`.

## Repository Layout

| Path | Purpose |
|------|---------|
| [Chart.yaml](Chart.yaml) | Chart metadata. |
| [values.yaml](values.yaml) | Minimal default values and `helm-docs` source comments. |
| [docs/README.md.gotmpl](docs/README.md.gotmpl) | Template used by `helm-docs` to build `README.md`. |
| [.pre-commit-config.yaml](.pre-commit-config.yaml) | Local hooks, including automatic `helm-docs` generation on commit. |
| [values.yaml.example](values.yaml.example) | Full example configuration. |
| [values.schema.json](values.schema.json) | JSON schema for chart values. |
| [templates/](templates) | One template per supported KEDA kind plus shared helpers. |
| [tests/units/](tests/units) | Compact Helm unit suites and backward compatibility checks. |
| [tests/e2e/](tests/e2e) | kind-based end-to-end installation checks. |
| [tests/smokes/](tests/smokes) | Smoke scenarios for render and schema validation. |
| [docs/DEPENDENCY.md](docs/DEPENDENCY.md) | Local dependency installation guide for development and tests. |
| [docs/TESTS.MD](docs/TESTS.MD) | Detailed testing documentation. |
