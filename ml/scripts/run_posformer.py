"""Phase-1 PosFormer inference harness (plain torch, no Lightning Trainer).

Usage (from ml/):
  .venv\\Scripts\\python.exe scripts\\run_posformer.py --ckpt checkpoints/posformer-best.ckpt
      --renders data/renders/test --labels data/renders/test/labels.tsv
      --polarity b --limit 30 --out experiments/posformer_run1.json

What it does:
  1. Installs pl_compat shim, imports the UNMODIFIED PosFormer model code from a
     scratch checkout (POSFORMER_CODE env or default temp path).
  2. Builds PosFormer with the repo's config.yaml model hyperparams, loads the
     released best.ckpt (keys: LitPosFormer 'state_dict', 'model.*' prefix stripped).
  3. Preprocesses each render EXACTLY like the repo eval path: repo's own
     ScaleToLimitRange (H 16..256, W 16..1024) + torchvision ToTensor, zero-pad +
     boolean pad-mask (same convention as collate_fn: 1 = pad).
  4. Runs the repo's own bidirectional beam_search (beam 10, max_len 200,
     alpha 1.0, no early stop, T 1.0 — config.yaml values) under torch.no_grad().
  5. Writes predictions + per-sample latency to JSON. No training, no fine-tune.

Device: CPU (torch 2.14.1+cpu). Deterministic greedy-free beam search; model.eval().
"""
import argparse
import json
import os
import sys
import time

import torch
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pl_compat  # noqa: E402

pl_compat.install()

POSFORMER_CODE = os.environ.get(
    "POSFORMER_CODE",
    r"C:\Users\Swarnim\AppData\Local\Temp\opencode\PosFormer-code",
)
sys.path.insert(0, POSFORMER_CODE)

from Pos_Former.datamodule import vocab  # noqa: E402
from Pos_Former.datamodule.transforms import ScaleToLimitRange  # noqa: E402
from Pos_Former.model.posformer import PosFormer  # noqa: E402
from torchvision.transforms import ToTensor  # noqa: E402

MODEL_KWARGS = dict(d_model=256, growth_rate=24, num_layers=16, nhead=8,
                    num_decoder_layers=3, dim_feedforward=1024, dropout=0.3,
                    dc=32, cross_coverage=True, self_coverage=True)
BEAM = dict(beam_size=10, max_len=200, alpha=1.0,
            early_stopping=False, temperature=1.0)

_scaler = ScaleToLimitRange(w_lo=16, w_hi=1024, h_lo=16, h_hi=256)
_to_tensor = ToTensor()


def load_model(ckpt_path):
    print(f"loading checkpoint: {ckpt_path}", flush=True)
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    sd = ckpt.get("state_dict", ckpt)
    stripped = {}
    for k, v in sd.items():
        if k.startswith("model."):
            stripped[k[len("model."):]] = v
    print(f"ckpt keys: {len(sd)} total, {len(stripped)} under 'model.'", flush=True)
    model = PosFormer(**MODEL_KWARGS)
    missing, unexpected = model.load_state_dict(stripped, strict=False)
    print(f"load_state_dict: missing={len(missing)} unexpected={len(unexpected)}",
          flush=True)
    for k in list(missing)[:10]:
        print(f"  missing: {k}", flush=True)
    for k in list(unexpected)[:10]:
        print(f"  unexpected: {k}", flush=True)
    model.eval()
    return model


def preprocess(png_path):
    import numpy as np
    img = Image.open(png_path).convert("L")
    arr = _scaler(__import__("numpy").asarray(img))
    t = _to_tensor(arr)  # [1,H,W] float in [0,1]
    _, h, w = t.shape
    mask = torch.zeros(1, h, w, dtype=torch.bool)  # collate_fn convention: 0 = pixel
    return t.unsqueeze(0), mask


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--random-weights", action="store_true",
                    help="skip checkpoint; smoke-test pipeline with random init")
    ap.add_argument("--renders", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--polarity", default="b", choices=["w", "b"])
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pairs = []
    with open(args.labels, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line:
                sid, gt = line.split("\t", 1)
                pairs.append((sid, gt))
    pairs = pairs[:args.limit]
    print(f"samples: {len(pairs)}, polarity: {args.polarity}", flush=True)

    if args.random_weights or not args.ckpt:
        print("SMOKE MODE: random weights (no checkpoint)", flush=True)
        model = PosFormer(**MODEL_KWARGS)
        model.eval()
        ckpt_used = None
    else:
        model = load_model(args.ckpt)
        ckpt_used = args.ckpt
    results = []
    t_all = time.time()
    with torch.no_grad():
        for sid, gt in pairs:
            png = os.path.join(args.renders, f"{sid}_{args.polarity}.png")
            img, mask = preprocess(png)
            t0 = time.time()
            hyps = model.beam_search(img, mask, **BEAM)
            dt = time.time() - t0
            pred = vocab.indices2label(hyps[0].seq)
            results.append({"id": sid, "gt": gt, "pred": pred,
                            "score": float(hyps[0].score), "latency_s": round(dt, 3)})
            print(f"[{sid}] {dt:.1f}s pred={pred[:120]}", flush=True)
    print(f"total {time.time()-t_all:.1f}s for {len(results)} samples", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"ckpt": ckpt_used, "polarity": args.polarity,
                   "beam": BEAM, "results": results}, f, indent=1)
    print(f"wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
