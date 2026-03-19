# Agent Guide

This file is the reference baseline for Helm chart repositories that follow a single-chart layout with layered tests under `tests/units`, `tests/e2e`, and `tests/smokes`.

Adapt names, chart-specific commands, and controller details to the target project, but keep the structure, discipline, and decision rules consistent unless the repository clearly uses another pattern.

## Repository Shape

Prefer a single root chart with this baseline structure:

```text
.
├── Chart.yaml
├── values.yaml
├── values.schema.json
├── values.yaml.example
├── templates/
├── tests/
│   ├── units/
│   ├── e2e/
│   └── smokes/
└── docs/
```

Keep documentation and automation aligned with the actual tree. If a directory or workflow is removed, update both the docs and CI in the same change.

## Repository Standard

Treat this repository as a template for similar chart repositories:

- one chart at the repository root
- one clear values contract
- one example values file that exercises the full supported surface
- one helper layer for shared template behavior
- one documented test pyramid with fast checks in CI and heavier checks local-first

Do not introduce parallel structures that solve the same problem twice. Avoid duplicate examples, duplicate test fixtures with overlapping intent, or multiple competing local entry points.

## Documentation Rules

- Keep one root `README.md` as the primary entry point.
- Keep `README.md` generated from `docs/README.md.gotmpl` via `helm-docs` and `pre-commit`.
- Keep test-layer details in `docs/TESTS.MD`.
- Keep repository-wide contribution and maintenance guidance in `docs/AGENTS.md`.
- Use relative repository links in Markdown, not workstation-specific absolute paths.
- Prefer describing the current repository state over aspirational tooling that is not actually wired in.
- If a workflow is local-only, state that explicitly.
- Document operational constraints, not just happy paths. If CI cannot run Docker, say so. If a resource kind depends on experimental APIs, say so.
- When changing versions, commands, or supported resources, update docs in the same change as code and CI.
- When changing chart values, update the `# --` comments in `values.yaml` so the generated Helm values table stays useful.

## Chart Design Expectations

- Keep templates thin and deterministic.
- Centralize shared rendering logic in `templates/_helpers.tpl` when repetition appears.
- Prefer generic resource contracts when the chart is intended to pass through raw Kubernetes or CRD specs.
- Validate the values contract with `values.schema.json` when possible.
- Avoid managing `status` in production workflows unless the chart is explicitly intended for fixtures or synthetic manifests.
- Prefer additive values design over bespoke toggles. If the same rendering contract can support multiple resource kinds, reuse it.
- Keep defaults minimal and safe. The base `values.yaml` should render nothing unless the repository has a strong reason to ship opinionated resources.
- Keep `values.yaml.example` comprehensive enough to exercise every supported kind at least once.

## Versioning Rules

- Pin Kubernetes-dependent tooling deliberately.
- Treat Kubernetes API validation version, local cluster image version, and CRD bundle version as separate concerns.
- Do not assume the latest Kubernetes patch has a matching `kindest/node` image.
- Do not assume the latest KEDA release changes CRD schemas or served versions in a backwards-compatible way.
- When bumping versions, verify real upstream availability before editing the repository.
- Preserve the expected format for each tool:
  - `kubeconform`: `1.x.y`
  - `kindest/node`: `v1.x.y`
  - GitHub release tags: usually `v...`

Record version bumps in the repository only where they are true defaults. Avoid scattering version literals across docs, scripts, and CI unless each copy is actually required.

## KEDA Rules

For KEDA chart repositories, keep these assumptions explicit:

- chart rendering support and cluster installability are different concerns
- resource support depends on the installed CRD bundle and operator, not only on the chart
- cluster-scoped and namespaced resources must be handled explicitly in examples, tests, and docs
- per-kind `apiVersion` overrides are part of the public contract, not a workaround to hide

When testing against a pinned KEDA bundle:

- verify which kinds are actually served
- verify which API versions are served for those kinds
- keep e2e fixtures aligned with the installed CRDs, even if chart defaults target newer APIs
- explain any intentional mismatch between chart defaults and e2e fixture overrides

## Test Layers

### Unit Tests

Use `helm-unittest` for chart-owned rendering behavior:

- helper behavior
- defaulting
- label and annotation merges
- namespace handling
- API version overrides
- representative manifests from example values

Keep unit suites compact. Do not mirror large CRD payloads field by field unless the chart itself transforms them.

### Smoke Tests

Use smoke tests for render-path validation without a live cluster:

- default empty render
- schema enforcement from `values.schema.json`
- representative example rendering
- optional `kubeconform` validation

Prefer small reusable helpers around `helm`, file staging, and manifest assertions.

### E2E Tests

Use `kind`-based or cluster-backed e2e tests only when they validate something that unit and smoke tests cannot:

- installation into a real API server
- CRD presence and compatibility
- end-to-end Helm install or upgrade flows

If e2e requires Docker, kind, or privileged runners, it is acceptable to keep it local-only and expose it through a `Makefile`.

Prefer direct `helm upgrade --install` in e2e runners unless `chart-testing` provides a concrete benefit that is proven in this repository. Do not keep extra orchestration layers that fail independently of the chart under test.

## CI Guidance

CI should cover the lightweight checks by default:

- lint
- unit tests
- smoke tests
- backward compatibility rendering
- manifest rendering
- schema validation

Add e2e to CI only when the target runner environment actually supports it. Avoid documenting e2e CI jobs that cannot run on the repository's real runners.

For GitLab CI specifically:

- do not require `docker:dind` or privileged runners unless the repository explicitly targets such runners
- prefer Alpine-based jobs with explicit package installation over opaque custom CI images unless reuse is substantial
- keep CI stages small and legible; each job should map to one testing concern
- keep artifact passing minimal and intentional

## Makefile Guidance

If the repository ships a `Makefile`, use it as a thin local wrapper around existing scripts, not as a second source of truth.

Good targets:

- `make hooks-install`
- `make docs`
- `make lint`
- `make test-unit`
- `make test-compat`
- `make test-smoke`
- `make test-smoke-fast`
- `make test-e2e`
- `make test-e2e-debug`
- `make test-e2e-help`

Keep target names predictable and scoped to the workflows that already exist in the repository.

## Change Discipline

When making repository-wide changes, prefer this order:

1. fix or simplify the implementation
2. align tests and fixtures
3. align CI defaults
4. align documentation
5. run a compact verification pass

Do not leave the repository in a state where the code is correct but docs still describe removed tooling, or CI still points at stale commands.

## Cleanup Rules

- Remove generated files such as `__pycache__`, `*.pyc`, temporary renders, and unused local tooling configs.
- Delete outdated docs instead of leaving duplicates.
- If a config file is not referenced by CI, scripts, or documented local workflows, treat it as a removal candidate.
- After cleanup, run a final pass over Markdown so the repository reads as one coherent system.
- Prefer deleting stale abstractions over preserving them for hypothetical future reuse.

## Final Verification

Before finishing a change in a similar repository, prefer to run a compact validation set such as:

```bash
git diff --check
helm lint . -f values.yaml.example
helm template <release> . -f values.yaml.example
bash -n tests/e2e/test-e2e.sh
sh -n tests/units/backward_compatibility_test.sh
python3 -m py_compile tests/smokes/helpers/argparser.py tests/smokes/run/smoke.py tests/smokes/scenarios/smoke.py tests/smokes/steps/*.py
```

Add or swap commands to match the actual repository toolchain, but keep the idea: syntax, renderability, and documentation must all agree by the end of the change.

For version or test-runner changes, add these review questions before considering the work complete:

- Is every pinned upstream version real and currently available?
- Does local e2e still reflect what the runner environment can actually execute?
- Do docs describe the implemented workflow rather than an older or aspirational one?
- Are CI and local commands using the same underlying scripts where practical?
