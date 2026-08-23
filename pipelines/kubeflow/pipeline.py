"""Kubeflow Pipelines definition using the same production CLI as local runs."""

from kfp import dsl
from kfp.dsl import Dataset, Model

TRAINING_IMAGE = "ghcr.io/example/sentinelflow-api:0.1.0"


@dsl.container_component
def validate_component(input_data: dsl.Input[Dataset]) -> dsl.ContainerSpec:
    return dsl.ContainerSpec(
        image=TRAINING_IMAGE,
        command=["python", "-m", "sentinelflow.cli"],
        args=["inspect", "--data", input_data.path, "--require-labels"],
    )


@dsl.container_component
def train_component(
    validated_data: dsl.Input[Dataset],
    model_registry: dsl.Output[Model],
) -> dsl.ContainerSpec:
    return dsl.ContainerSpec(
        image=TRAINING_IMAGE,
        command=["python", "-m", "sentinelflow.cli"],
        args=[
            "train",
            "--data",
            validated_data.path,
            "--registry",
            model_registry.path,
        ],
    )


@dsl.pipeline(name="sentinelflow-training")
def training_pipeline(input_data: dsl.Input[Dataset]) -> None:
    validation = validate_component(input_data=input_data)
    training = train_component(validated_data=input_data)
    training.after(validation)
