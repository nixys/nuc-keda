from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from tests.smokes.steps import chart, helm, kubeconform, render, system


@dataclass
class SmokeContext:
    repo_root: Path
    workdir: Path
    chart_dir: Path
    render_dir: Path
    release_name: str
    namespace: str
    kube_version: str
    kubeconform_bin: str
    schema_location: str
    skip_kinds: str

    @property
    def example_values(self) -> Path:
        return self.repo_root / "values.yaml.example"

    @property
    def rendering_contract_values(self) -> Path:
        return self.repo_root / "tests" / "smokes" / "fixtures" / "rendering-contract.values.yaml"

    @property
    def invalid_list_contract_values(self) -> Path:
        return self.repo_root / "tests" / "smokes" / "fixtures" / "invalid-list-contract.values.yaml"


def check_default_empty(context: SmokeContext) -> None:
    helm.lint(context.chart_dir, workdir=context.workdir)
    output_path = context.render_dir / "default-empty.yaml"
    helm.template(
        context.chart_dir,
        release_name=context.release_name,
        namespace=context.namespace,
        output_path=output_path,
        workdir=context.workdir,
    )
    documents = render.load_documents(output_path)
    render.assert_doc_count(documents, 0)


def check_schema_invalid_list_contract(context: SmokeContext) -> None:
    result = helm.lint(
        context.chart_dir,
        values_file=context.invalid_list_contract_values,
        workdir=context.workdir,
        check=False,
    )
    if result.returncode == 0:
        raise system.TestFailure(
            "helm lint unexpectedly succeeded for invalid list-based values"
        )

    combined_output = f"{result.stdout}\n{result.stderr}"
    if "scaledObjects" not in combined_output or "object" not in combined_output:
        raise system.TestFailure(
            "helm lint failed for invalid values, but the error does not mention the object-based map contract"
        )


def check_rendering_contract(context: SmokeContext) -> None:
    helm.lint(
        context.chart_dir,
        values_file=context.rendering_contract_values,
        workdir=context.workdir,
    )
    output_path = context.render_dir / "rendering-contract.yaml"
    helm.template(
        context.chart_dir,
        release_name=context.release_name,
        namespace=context.namespace,
        values_file=context.rendering_contract_values,
        output_path=output_path,
        workdir=context.workdir,
    )

    documents = render.load_documents(output_path)
    render.assert_doc_count(documents, 2)

    scaled_object = render.select_document(
        documents, kind="ScaledObject", name="merged-scaled-object"
    )
    render.assert_path(scaled_object, "apiVersion", "example.net/v1alpha1")
    render.assert_path(scaled_object, "metadata.namespace", context.namespace)
    render.assert_path(
        scaled_object,
        "metadata.labels[app.kubernetes.io/name]",
        "keda-platform",
    )
    render.assert_path(scaled_object, "metadata.labels.platform", "keda")
    render.assert_path(scaled_object, "metadata.labels.component", "scaled-object")
    render.assert_path(scaled_object, "metadata.labels.tier", "workers")
    render.assert_path(scaled_object, "metadata.annotations.team", "platform")
    render.assert_path(scaled_object, "metadata.annotations.note", "external")
    render.assert_path(scaled_object, "spec.scaleTargetRef.name", "worker-app")

    cluster_trigger_auth = render.select_document(
        documents, kind="ClusterTriggerAuthentication", name="shared-auth"
    )
    render.assert_path(cluster_trigger_auth, "apiVersion", "keda.sh/v1beta1")
    render.assert_path_missing(cluster_trigger_auth, "metadata.namespace")
    render.assert_path(
        cluster_trigger_auth,
        "metadata.labels[app.kubernetes.io/name]",
        "keda-platform",
    )
    render.assert_path(
        cluster_trigger_auth, "metadata.labels.component", "cluster-trigger-auth"
    )
    render.assert_path(cluster_trigger_auth, "metadata.annotations.team", "platform")
    render.assert_path(cluster_trigger_auth, "metadata.annotations.note", "shared")
    render.assert_path(
        cluster_trigger_auth, "spec.secretTargetRef[0].name", "shared-metrics-auth"
    )


def check_example_render(context: SmokeContext) -> None:
    helm.lint(
        context.chart_dir,
        values_file=context.example_values,
        workdir=context.workdir,
    )
    output_path = context.render_dir / "example-render.yaml"
    helm.template(
        context.chart_dir,
        release_name=context.release_name,
        namespace=context.namespace,
        values_file=context.example_values,
        output_path=output_path,
        workdir=context.workdir,
    )

    documents = render.load_documents(output_path)
    render.assert_doc_count(documents, 6)
    render.assert_kinds(
        documents,
        {
            "ScaledObject",
            "ScaledJob",
            "TriggerAuthentication",
            "ClusterTriggerAuthentication",
        },
    )

    cluster_trigger_auth = render.select_document(
        documents, kind="ClusterTriggerAuthentication", name="metrics-auth"
    )
    render.assert_path_missing(cluster_trigger_auth, "metadata.namespace")

    orders_worker = render.select_document(
        documents, kind="ScaledObject", name="orders-worker"
    )
    render.assert_path(orders_worker, "metadata.namespace", "workloads")
    render.assert_path(orders_worker, "spec.triggers[0].type", "rabbitmq")

    payments_worker = render.select_document(
        documents, kind="ScaledObject", name="payments-worker"
    )
    render.assert_path(
        payments_worker,
        "spec.triggers[0].authenticationRef.kind",
        "ClusterTriggerAuthentication",
    )

    scaled_job = render.select_document(
        documents, kind="ScaledJob", name="reports-generator"
    )
    render.assert_path(
        scaled_job,
        "spec.jobTargetRef.template.spec.containers[0].image",
        "ghcr.io/example/reports:1.2.3",
    )

    trigger_auth = render.select_document(
        documents, kind="TriggerAuthentication", name="rabbitmq-auth"
    )
    render.assert_path(trigger_auth, "spec.secretTargetRef[2].parameter", "password")


def check_example_kubeconform(context: SmokeContext) -> None:
    output_path = context.render_dir / "example-kubeconform.yaml"
    helm.template(
        context.chart_dir,
        release_name=context.release_name,
        namespace=context.namespace,
        values_file=context.example_values,
        output_path=output_path,
        workdir=context.workdir,
    )
    kubeconform.validate(
        manifest_path=output_path,
        kube_version=context.kube_version,
        kubeconform_bin=context.kubeconform_bin,
        schema_location=context.schema_location,
        skip_kinds=context.skip_kinds,
    )


SCENARIOS: list[tuple[str, Callable[[SmokeContext], None]]] = [
    ("default-empty", check_default_empty),
    ("schema-invalid-list-contract", check_schema_invalid_list_contract),
    ("rendering-contract", check_rendering_contract),
    ("example-render", check_example_render),
    ("example-kubeconform", check_example_kubeconform),
]


def run_smoke_suite(args) -> int:
    scenario_map = dict(SCENARIOS)
    requested = args.scenario or ["all"]
    if "all" in requested:
        selected = [name for name, _ in SCENARIOS]
    else:
        selected = requested

    repo_root = Path(args.chart_dir).resolve()
    workdir, chart_dir = chart.stage_chart(repo_root, args.workdir)
    context = SmokeContext(
        repo_root=repo_root,
        workdir=workdir,
        chart_dir=chart_dir,
        render_dir=workdir / "rendered",
        release_name=args.release_name,
        namespace=args.namespace,
        kube_version=args.kube_version,
        kubeconform_bin=args.kubeconform_bin,
        schema_location=args.schema_location,
        skip_kinds=args.skip_kinds,
    )
    context.render_dir.mkdir(parents=True, exist_ok=True)

    failures: list[tuple[str, str]] = []
    try:
        for name in selected:
            system.log(f"=== scenario: {name} ===")
            try:
                scenario_map[name](context)
            except Exception as exc:
                failures.append((name, str(exc)))
                system.log(f"FAILED: {name}: {exc}")
            else:
                system.log(f"PASSED: {name}")
    finally:
        if args.keep_workdir:
            system.log(f"workdir kept at {workdir}")
        else:
            chart.cleanup(workdir)

    if failures:
        system.log("=== summary: failures ===")
        for name, message in failures:
            system.log(f"- {name}: {message}")
        return 1

    system.log("=== summary: all smoke scenarios passed ===")
    return 0
