#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
SCRIPT_DIR="${ROOT_DIR}/tests/e2e"
CLUSTER_CREATED=false
CLUSTER_NAME="${CLUSTER_NAME:-$(mktemp -u "nuc-keda-e2e-XXXXXXXXXX" | tr "[:upper:]" "[:lower:]")}"
K8S_VERSION="${K8S_VERSION:-v1.35.0}"
KEDA_VERSION="${KEDA_VERSION:-2.18.2}"
KEDA_CRD_BASE_URL="https://raw.githubusercontent.com/kedacore/keda/v${KEDA_VERSION}/config/crd/bases"
E2E_NAMESPACE="nuc-keda-e2e"
RELEASE_NAME="nuc-keda-e2e"
VALUES_FILE="tests/e2e/values/install.values.yaml"

RED='\033[0;31m'
YELLOW='\033[0;33m'
RESET='\033[0m'

log_error() { echo -e "${RED}Error:${RESET} $1" >&2; }
log_info() { echo -e "$1"; }
log_warn() { echo -e "${YELLOW}Warning:${RESET} $1" >&2; }

show_help() {
  echo "Usage: $(basename "$0") [helm upgrade/install options]"
  echo ""
  echo "Create a kind cluster, install KEDA CRDs, and run Helm install/upgrade against the root chart."
  echo "Unknown arguments are passed through to 'helm upgrade --install'."
  echo ""
  echo "Environment overrides:"
  echo "  CLUSTER_NAME          Kind cluster name"
  echo "  K8S_VERSION           kindest/node tag"
  echo "  KEDA_VERSION          KEDA release used for CRD bootstrap"
  echo ""
}

verify_prerequisites() {
  for bin in docker kind kubectl helm; do
    if ! command -v "${bin}" >/dev/null 2>&1; then
      log_error "${bin} is not installed"
      exit 1
    fi
  done
}

cleanup() {
  local exit_code=$?

  if [ "${exit_code}" -ne 0 ] && [ "${CLUSTER_CREATED}" = true ]; then
    dump_cluster_state || true
  fi

  log_info "Cleaning up resources"

  if [ "${CLUSTER_CREATED}" = true ]; then
    log_info "Removing kind cluster ${CLUSTER_NAME}"
    if kind get clusters | grep -q "${CLUSTER_NAME}"; then
      kind delete cluster --name="${CLUSTER_NAME}"
    else
      log_warn "kind cluster ${CLUSTER_NAME} not found"
    fi
  fi

  exit "${exit_code}"
}

dump_cluster_state() {
  log_warn "Dumping KEDA resources from ${CLUSTER_NAME}"
  kubectl get clustertriggerauthentications.keda.sh || true
  kubectl get scaledobjects.keda.sh,scaledjobs.keda.sh,triggerauthentications.keda.sh -A || true
}

create_kind_cluster() {
  log_info "Creating kind cluster ${CLUSTER_NAME}"

  if kind get clusters | grep -q "${CLUSTER_NAME}"; then
    log_error "kind cluster ${CLUSTER_NAME} already exists"
    exit 1
  fi

  kind create cluster \
    --name="${CLUSTER_NAME}" \
    --config="${SCRIPT_DIR}/kind.yaml" \
    --image="kindest/node:${K8S_VERSION}" \
    --wait=60s

  CLUSTER_CREATED=true
  echo
}

install_keda_crds() {
  log_info "Installing KEDA CRDs from ${KEDA_VERSION}"

  for url in \
    "${KEDA_CRD_BASE_URL}/keda.sh_scaledobjects.yaml" \
    "${KEDA_CRD_BASE_URL}/keda.sh_scaledjobs.yaml" \
    "${KEDA_CRD_BASE_URL}/keda.sh_triggerauthentications.yaml" \
    "${KEDA_CRD_BASE_URL}/keda.sh_clustertriggerauthentications.yaml"; do
    kubectl apply --server-side -f "${url}"
  done

  for crd in \
    scaledobjects.keda.sh \
    scaledjobs.keda.sh \
    triggerauthentications.keda.sh \
    clustertriggerauthentications.keda.sh; do
    kubectl wait --for=condition=Established --timeout=120s "crd/${crd}"
  done

  echo
}

ensure_namespace() {
  log_info "Ensuring namespace ${E2E_NAMESPACE} exists"
  kubectl get namespace "${E2E_NAMESPACE}" >/dev/null 2>&1 || kubectl create namespace "${E2E_NAMESPACE}"
  echo
}

install_chart() {
  local helm_args=(
    upgrade
    --install
    "${RELEASE_NAME}"
    "${ROOT_DIR}"
    --namespace "${E2E_NAMESPACE}"
    -f "${ROOT_DIR}/${VALUES_FILE}"
    --wait
    --timeout 300s
  )

  if [ "$#" -gt 0 ]; then
    helm_args+=("$@")
  fi

  log_info "Building chart dependencies"
  helm dependency build "${ROOT_DIR}"
  echo

  log_info "Installing chart with Helm"
  helm "${helm_args[@]}"
  echo
}

verify_release_resources() {
  log_info "Verifying installed KEDA resources"
  kubectl get clustertriggerauthentication e2e-cluster-trigger-auth
  kubectl -n "${E2E_NAMESPACE}" get scaledobject e2e-orders-worker
  kubectl -n "${E2E_NAMESPACE}" get scaledjob e2e-reports-generator
  kubectl -n "${E2E_NAMESPACE}" get triggerauthentication e2e-trigger-auth
  echo
}

parse_args() {
  for arg in "$@"; do
    case "${arg}" in
      -h|--help)
        show_help
        exit 0
        ;;
    esac
  done
}

main() {
  parse_args "$@"
  verify_prerequisites

  trap cleanup EXIT

  create_kind_cluster
  install_keda_crds
  ensure_namespace
  install_chart "$@"
  verify_release_resources

  log_info "End-to-end checks completed successfully"
}

main "$@"
