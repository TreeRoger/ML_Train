"""
Training entrypoint - runs inside K8s Job container.
Supports single-process and multi-process (DDP) simulation.
Pushes metrics to Redis for dashboard.
"""

import argparse
import json
import logging
import os
from typing import Any

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
import redis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
METRICS_CHANNEL = "ml_train:metrics"


def get_model(architecture: str, num_classes: int) -> nn.Module:
    if architecture == "resnet18":
        model = models.resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    elif architecture == "resnet34":
        model = models.resnet34(weights=None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    else:
        model = models.resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def get_dataloaders(dataset: str, batch_size: int, world_size: int = 1, rank: int = 0):
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])
    if dataset == "cifar10":
        train_ds = datasets.CIFAR10(root="/tmp/data", train=True, download=True, transform=transform)
    else:
        train_ds = datasets.CIFAR10(root="/tmp/data", train=True, download=True, transform=transform)
    # Simple shard for multi-process simulation
    total = len(train_ds)
    per_worker = total // world_size
    start = rank * per_worker
    end = start + per_worker if rank < world_size - 1 else total
    subset = torch.utils.data.Subset(train_ds, range(start, end))
    loader = DataLoader(subset, batch_size=batch_size, shuffle=True, num_workers=0)
    return loader


def publish_metrics(r: redis.Redis, job_id: str, step: int, epoch: float, metrics: dict[str, float]):
    payload = {"job_id": job_id, "step": step, "epoch": epoch, **metrics}
    r.publish(METRICS_CHANNEL, json.dumps(payload))


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    epoch: int,
    job_id: str,
    redis_client: redis.Redis | None,
    world_size: int,
    rank: int,
) -> dict[str, float]:
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    step = 0
    for batch_idx, (data, target) in enumerate(loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        out = model(data)
        loss = criterion(out, target)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        pred = out.argmax(dim=1)
        correct += pred.eq(target).sum().item()
        total += target.size(0)
        step += 1
        if redis_client and step % 10 == 0:
            avg_loss = total_loss / step
            acc = correct / total
            publish_metrics(redis_client, job_id, epoch * len(loader) + step, float(epoch), {
                "loss": avg_loss,
                "accuracy": acc,
            })
    avg_loss = total_loss / max(step, 1)
    acc = correct / total
    return {"loss": avg_loss, "accuracy": acc}


def run_training(config: dict[str, Any], job_id: str):
    model_cfg = config.get("model_config", {})
    train_cfg = config.get("training_config", {})
    architecture = model_cfg.get("architecture", "resnet18")
    num_classes = model_cfg.get("num_classes", 10)
    epochs = train_cfg.get("epochs", 3)
    batch_size = train_cfg.get("batch_size", 32)
    lr = train_cfg.get("learning_rate", 0.001)
    world_size = train_cfg.get("world_size", 1)
    dataset = train_cfg.get("dataset", "cifar10")

    if world_size > 1:
        from . import ddp_runner
        ddp_runner.run_distributed(job_id, config, world_size)
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}, world_size={world_size}")

    model = get_model(architecture, num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    loader = get_dataloaders(dataset, batch_size, world_size, rank=0)
    r = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

    for epoch in range(epochs):
        metrics = train_one_epoch(
            model, loader, criterion, optimizer, device, epoch, job_id, r, world_size, 0
        )
        logger.info(f"Epoch {epoch + 1}/{epochs} - loss: {metrics['loss']:.4f} acc: {metrics['accuracy']:.4f}")
        if r:
            publish_metrics(r, job_id, (epoch + 1) * len(loader), float(epoch + 1), metrics)

    if r:
        r.close()
    logger.info("Training complete.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--config", required=True, help="JSON config")
    parser.add_argument("--epochs", type=int, default=None)
    args = parser.parse_args()

    config = json.loads(args.config)
    if args.epochs is not None:
        config.setdefault("training_config", {})["epochs"] = args.epochs

    run_training(config, args.job_id)


if __name__ == "__main__":
    main()
