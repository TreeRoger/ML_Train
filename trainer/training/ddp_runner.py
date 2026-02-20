"""
Simulated multi-GPU / distributed training via PyTorch DDP.
Run with: torchrun --nproc_per_node=N -m training.ddp_runner --job-id X --config '{}'
Or locally: python -m training.ddp_runner --job-id X --config '{}' --world-size 2
"""

import argparse
import json
import logging
import os

import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

from .main import get_model, publish_metrics, REDIS_URL
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup(rank: int, world_size: int):
    os.environ["MASTER_ADDR"] = os.environ.get("MASTER_ADDR", "localhost")
    os.environ["MASTER_PORT"] = os.environ.get("MASTER_PORT", "29500")
    dist.init_process_group("gloo", rank=rank, world_size=world_size)


def cleanup():
    dist.destroy_process_group()


def run_worker(rank: int, world_size: int, job_id: str, config: dict):
    setup(rank, world_size)

    import torch.nn as nn
    from torch.utils.data.distributed import DistributedSampler

    model_cfg = config.get("model_config", {})
    train_cfg = config.get("training_config", {})
    architecture = model_cfg.get("architecture", "resnet18")
    num_classes = model_cfg.get("num_classes", 10)
    epochs = train_cfg.get("epochs", 3)
    batch_size = train_cfg.get("batch_size", 32)
    lr = train_cfg.get("learning_rate", 0.001)
    dataset = train_cfg.get("dataset", "cifar10")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = get_model(architecture, num_classes).to(device)
    model = DDP(model)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    from torchvision import datasets, transforms
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])
    train_ds = datasets.CIFAR10(root="/tmp/data", train=True, download=True, transform=transform)
    sampler = DistributedSampler(train_ds, num_replicas=world_size, rank=rank)
    loader = torch.utils.data.DataLoader(train_ds, batch_size=batch_size, sampler=sampler, num_workers=0)

    r = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None
    global_step = 0

    for epoch in range(epochs):
        sampler.set_epoch(epoch)
        model.train()
        total_loss, correct, total = 0.0, 0, 0
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
            global_step += 1
            if rank == 0 and r and batch_idx % 10 == 0:
                publish_metrics(r, job_id, global_step, float(epoch), {
                    "loss": total_loss / (batch_idx + 1),
                    "accuracy": correct / total,
                })
        if rank == 0:
            logger.info(f"Epoch {epoch+1}/{epochs} rank={rank} loss={total_loss/len(loader):.4f} acc={correct/total:.4f}")

    cleanup()
    if r:
        r.close()


def run_distributed(job_id: str, config: dict, world_size: int):
    """Spawn multiple processes for simulated DDP training."""
    torch.multiprocessing.spawn(
        run_worker,
        args=(world_size, job_id, config),
        nprocs=world_size,
        join=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--world-size", type=int, default=None)
    args = parser.parse_args()

    config = json.loads(args.config)
    world_size = args.world_size or config.get("training_config", {}).get("world_size", 1)

    if world_size <= 1:
        from .main import run_training
        run_training(config, args.job_id)
        return

    run_distributed(args.job_id, config, world_size)


if __name__ == "__main__":
    main()
