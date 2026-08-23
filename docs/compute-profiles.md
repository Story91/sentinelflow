# Compute profiles: CPU, GPU, TPU

The local reference path is CPU-only and intentionally small. Compute selection is a deployment decision, not a model requirement.

| Profile | Suitable workload | Configuration | Cost/safety note |
|---|---|---|---|
| CPU | feature engineering, tabular baseline, API serving | default Docker/Kubernetes resources | default profile for local development |
| GPU | PyTorch/TensorFlow experiments, larger batches | infra/kubernetes/overlays/compute/gpu-patch.yaml and a CUDA image | request a real GPU resource; benchmark before adopting |
| TPU | TensorFlow/JAX large dense training on GCP | Vertex AI custom job with TPU-compatible image and accelerator config | cloud-only optional lab; no fake local TPU claim |

The interview point is to explain the trade-off: throughput and training time versus startup cost, memory transfer, scheduling complexity, reproducibility, and utilization. Serving a small tabular model on a GPU would usually be wasteful.

