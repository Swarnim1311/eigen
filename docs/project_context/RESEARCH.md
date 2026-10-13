# RESEARCH — Handwritten-math recognition pipeline

**Researched:** `2026-10-09` (web + official repos/docs/papers).
**Claim labels:** Verified = confirmed in cited source; Estimate = judgement/inference;
Unverified = could not confirm. No benchmarks, licenses, or links fabricated.

## 1. Candidate models (image → LaTeX)

### A1. BTTR — Bidirectionally Trained Transformer (baseline of the family)

- Repo: https://github.com/Green-Wood/BTTR (archived 2026-02, MIT license) — Verified
- Paper: https://arxiv.org/abs/2105.02412 (ICDAR 2021) — Verified
- Arch: DenseNet encoder + 3-layer Transformer decoder, L2R+R2L training; grayscale
  image → LaTeX — Verified
- Weights: `pretrained-2014.ckpt` (74 MB) on release page
  https://github.com/Green-Wood/BTTR/releases/tag/v2.0 — Verified (page observed;
  byte-level re-download NOT performed per Phase 0 no-download rule)
- Weight license: none stated — Verified (absence); treat as all-rights-reserved until
  authors confirm — Estimate
- Deps: conda py3.7, torch 1.7, pytorch-lightning (ancient; expect CUDA-12 breakage) — Verified
- Suitability RTX 4050 6 GB: inference trivial; single-GPU fine-tune feasible — Estimate
- Limits: archived, weakest accuracy of family, old stack — Verified

### A2. CoMER — Coverage Modeling (ECCV 2022)

- Repo: https://github.com/Green-Wood/CoMER (archived; NO license file → treat as
  unlicensed/all-rights-reserved) — Verified
- Paper: https://arxiv.org/abs/2207.04410 — Verified
- Arch: BTTR + Attention Refinement (coverage); image → LaTeX — Verified
- Weights: in-git checkpoint
  `lightning_logs/version_0/checkpoints/epoch=151-step=57151-val_ExpRate=0.6365.ckpt`
  (49.6 MB, plain git blob) — Verified
- Deps: py3.7, torch 1.8.1, lightning 1.4.9 — Verified
- Notes: most reproducible eval toolchain (`eval_all.sh`, symLG) but license blocks
  product use — Estimate

### A3. PosFormer — Position Forest Transformer (ECCV 2024, NOT IJCAI/AAAI)

- Repo: https://github.com/SJTU-DeepVisionLab/PosFormer (active, 85 stars) — Verified
- Paper: https://arxiv.org/abs/2407.07764 — Verified
- Arch: CoMER + position-forest joint task + attention correction; forest heads
  training-only (no added inference latency claimed) — Verified
- Weights: in-git `lightning_logs/version_0/checkpoints/best.ckpt` (74.9 MB) — Verified
- Code license: README claims academic-research-only + 2-clause BSD, but NO LICENSE
  file in tree → ambiguous/restrictive, treat as non-commercial — Verified (texts observed)
- Weight license: none stated — Verified (absence)
- Deps: same legacy stack (py3.7/torch1.8.1) — Verified; data via CoMER `data.zip`,
  ModelScope M2E, Google-Drive MNE — Verified as listed, reachability Unverified
- GPU: single A800 ~25h / RTX 3090 OK per README → RTX 4050 fine-tune plausible at
  small batch — Verified claim / Estimate mapping
- Verdict: **RECOMMENDED INITIAL CANDIDATE** (newest maintained, in-git weights,
  nested-structure handling), pending license clearance — Estimate

### A4. TAMER — Tree-Aware Transformer (AAAI 2025)

- Repo: https://github.com/qingzhenduyu/TAMER (37 stars; NO license file) — Verified
- Paper: https://arxiv.org/abs/2408.08578 — Verified
- Arch: DenseNet + Transformer + coverage + Tree-Aware Module + tree-score beam
  search; image → LaTeX — Verified
- Weights: in-git CROHME ckpt (`version_0/...val_ExpRate=0.6113`) + HME100K ckpts;
  `version_2` (CROHME w/ fusion) folder EMPTY — Verified
- Deps/training: legacy stack; CROHME ~8–9h on 4×2080Ti — Verified (README)
- Verdict: strong alternate, but smaller community + missing ckpt + unlicensed → not
  first pick — Estimate

### A5. CAN / DWAP (reference baselines only)

- CAN: https://github.com/LBH1024/CAN (MIT code, 387 stars), paper
  https://arxiv.org/abs/2207.11463; NO documented checkpoint; README cites ~32 GB VRAM
  at batch 8 — Verified; paper numbers Unverified here
- WAP: https://github.com/JianshuZhang/WAP (RNN/GRU + coverage attention, predecessor) —
  Verified; use as citation only — Estimate

## 2. Encoder-decoder fine-tuning landscape (B)

All A1–A4 are DenseNet-encoder + Transformer-decoder image→LaTeX models with standard
Lightning checkpoints → fine-tuning is realistic on RTX 4050 at batch 4–8 + fp16 +
grad-accumulation (all need dependency modernization first) — Estimate. Strategy:
reproducible inference → baseline metrics → fine-tune only if justified. No training
from scratch.

## 3. pix2tex / LaTeX-OCR (comparison candidate C)

- Repo: https://github.com/lukas-blecher/LaTeX-OCR (16.6k stars) — Verified
- Docs: https://pix2tex.readthedocs.io/en/latest/ — Verified
- Arch: ViT encoder w/ ResNet backbone + Transformer decoder + learned image-resizer —
  Verified (README)
- Code license: MIT (`LICENSE`, Copyright 2021 Lukas Blecher) — Verified
- Weights: auto-download + https://github.com/lukas-blecher/LaTeX-OCR/releases
  (`weights.pth` ~100 MB + `image_resizer.pth` 19.4 MB) — Verified
- Weight license: **CC BY-NC-SA** (release notes: trained on arXiv data) — Verified
- Input: rendered/clean equation screenshots; author warns wild images imperfect —
  Verified; handwritten support only via training notebook mixing CROHME —
  Verified (https://github.com/lukas-blecher/LaTeX-OCR colab notebook)
- Reported rendered-set numbers (BLEU 0.88 / edit-dist 0.10) are PRINTED-only, do not
  apply to handwriting — Verified (README Performance table)
- Verdict: good rendered-screenshot reference + demo in hours; NOT an HMER solution
  (no perspective/lighting/detection pipeline, NC weights) — Estimate

## 4. Restricted baseline (D) — for simple expressions

- D1 (primary): https://github.com/luopeixiang/im2latex — CNN encoder + LSTM decoder +
  attention, MIT license — Verified; old pins (torch 1.2) need modernizing — Verified;
  rendered-trained (no handwriting robustness out-of-box) — Estimate
- D2 (secondary): CRNN+CTC https://github.com/meijieru/crnn.pytorch (MIT, port of
  https://github.com/bgshih/crnn) — Verified; needs `warp_ctc`→`torch.nn.CTCLoss`
  modernization — Verified/Estimate; linear symbol strings only (no fractions/2-D) —
  Estimate
- Purpose: reliable simple-case fallback (`digits + -*/=()^`) + ablation reference on
  6 GB GPU — Estimate

## 5. Datasets

### CROHME (2014/2016/2019)

- Official distribution (TC11): https://tc11.cvc.uab.es/datasets/CROHME-2014_2,
  https://tc11.cvc.uab.es/datasets/ICFHR-CROHME-2016_1,
  https://tc11.cvc.uab.es/datasets/ICDAR2019-CROHME-TDF_1 — Verified
- Native format ONLINE strokes (InkML + symbol segmentation + MathML); offline
  greyscale images are auto-rendered derivatives (default 1000×1000+pad), NOT phone
  photos — Verified (RIT https://www.cs.rit.edu/~crohme2019/dataANDtools.html)
- Splits: train 8,836 (2016) / 9,993 (2019); tests 986 (2014) / 1,147 (2016) / 1,199
  (2019) — Verified (competition papers); bundles 68–364 MB — Verified
- Annotation: MathML official GT; LaTeX explicitly NOT official GT — Verified
- License: **CC BY-NC-SA 3.0**, research-only non-commercial
  (https://www.isical.ac.in/~crohme/CROHME_data.html) — Verified
- Use: clean pretrain + standard benchmark after stroke→image rendering; NOT a
  phone-photo distribution — Estimate

### MathWriting (Google, 2024; paper v2 2025-03-29)

- Code/docs: https://github.com/google-research/google-research/tree/master/mathwriting
  — Verified; paper https://arxiv.org/abs/2404.10690 — Verified
- Data (GCS, InkML-only, rasterize with provided code):
  https://storage.googleapis.com/mathwriting_data/mathwriting-2024.tgz (2.9 GB) +
  excerpt `mathwriting-2024-excerpt.tgz` (1.5 MB) — Verified
- Splits: train 229,864 / valid 15,674 / test 7,644 human inks + 396,014 synthetic +
  6,423 symbols; 244 symbols; normalizedLabel = training GT; no stroke-level
  segmentation — Verified (archive_readme.md + paper)
- License: **data CC BY-NC-SA 4.0** (NOT CC-BY, NOT Apache); **code Apache-2.0**;
  repo-root "CC BY 4.0" banner does NOT apply to MathWriting — Verified
- HF mirrors (deepcopy/andito) are UNOFFICIAL conveniences — Verified as mirrors
- Use: primary train pool (26× CROHME), CROHME as external benchmark — Estimate

## 6. Comparison matrix (suitability for Eigen on RTX 4050 6 GB)

| Criterion | PosFormer ⭐ initial | TAMER | CoMER | BTTR (fallback) | pix2tex (compare) |
|---|---|---|---|---|---|
| Handwriting-native | yes | yes | yes | yes | no (renders) |
| Weights available | yes (in-git) | partial | yes (in-git) | yes (release) | yes (auto) |
| Code license | academic-only claim, unclear | none | none | MIT | MIT |
| Weight license | unstated | unstated | unstated | unstated | CC BY-NC-SA |
| 6 GB inference | yes | yes | yes | yes | yes |
| Fine-tune feasible | yes | yes | yes | yes | possible |
| Maintenance | active | small/new | archived | archived | active |

Paper-claimed ExpRates (BTTR ~54–57, CoMER ~58–64val, TAMER ~60–62, PosFormer gains
+1–2) are PAPER figures, NOT re-verified here — Unverified, do not cite as our results.

## 7. Recommendation

- **Initial: PosFormer** — newest maintained HMER transformer, in-git `best.ckpt`,
  nested-structure handling; first action = license clarification + reproducible
  inference on ≤50 CROHME renders + 5 phone photos.
- **Fallback: BTTR** — only permissive-code (MIT) option with released weights; accept
  lower accuracy + archived stack.
- **Comparison: pix2tex** for rendered-input sanity checks (respect NC weights).
- **Baseline: im2latex (MIT) / CRNN+CTC (MIT)** for constrained simple expressions.
- **Data: MathWriting-train, CROHME-eval**, identical rasterization + heavy augmentation;
  both datasets NC → commercial deployment needs permissive data + legal review.

## 8. Outstanding questions (need hands-on testing)

1. PosFormer/BTTR authors' weight redistribution terms — STILL Unverified (no reply
   sought; contact needs user authorization). Blocks commercial use, not research eval.
2. Legacy stack (torch 1.7/1.8, lightning 1.4.9, py3.7) vs CUDA 12 / py3.11 — RESOLVED
   for inference: plain-torch harness + minimal shim runs released weights on
   torch 2.14 CPU with ZERO changes to model code (see §9). Training/fine-tune path
   still unverified.
3. Actual ExpRate/CER of shortlisted ckpts — PARTIALLY resolved: 30-sample
   cross-dataset baseline recorded (0/30 exact, CER 0.912, §9). CROHME-test numbers
   still need official data access.
4. M2E/MNE extra data links reachability — Unverified (not pursued; not needed).
5. Smallest augmentation set closing the render→photo gap on 6 GB — Unverified
   (no authorized phone photos yet).

## 9. Phase 1 verification (2026-10-09 → 2026-10-10, this machine)

Provenance (HEAD/GET, no download): PosFormer `best.ckpt` 200 / 78,508,976 B;
BTTR `pretrained-2014.ckpt` 200 / 77,545,147 B; PosFormer `LICENSE` raw 404 (still
absent); BTTR `LICENSE` = MIT text (1078 B, unfilled [year]/[fullname] placeholders);
MathWriting excerpt 200 / 1,620,634 B; CoMER `data.zip` 200 / 30,894,119 B (NOT used —
unofficial re-host, murky provenance); TC11 site unreachable from here (connection
failure) + account wall → official CROHME access = user-action blocker.

License answers (four questions):
- Code use: BTTR MIT Verified; PosFormer academic-only README claim, no LICENSE file
  → usable for research, ambiguous otherwise (Unresolved for product).
- Checkpoint use: NO weight license stated for PosFormer, BTTR, CoMER, TAMER
  (Verified absences) → local research eval OK under stated code terms; any
  redistribution/commercial use UNRESOLVED.
- Dataset use: MathWriting excerpt CC BY-NC-SA 4.0 → local noncommercial eval
  permitted with attribution (this report); training-for-product NOT permitted.
  CROHME CC BY-NC-SA 3.0 research-only (not downloaded — no access).
- Commercial distribution: NOT cleared for any candidate (Unresolved).

Genuine inference (released `best.ckpt`, sha256 `943d3d28…818360ab71`, epoch 206):
unmodified PosFormer code + repo preprocessing (ScaleToLimitRange + ToTensor) +
repo bidirectional beam search, CPU torch 2.14.1, `model.eval()`, no_grad.
30 MathWriting-excerpt renders (white-on-black, polarity calibrated: black-bg
3.5 s coherent vs white-bg 712 s runaway). Results: exact 0/30, mean CER 0.912
(median 0.838), in-vocab-11 subset CER 0.922, latency mean 29.2 s (5.9–88.0 s).
Best: `x_{1}-x_{2}+x_{0}=0` CER 0.308; fraction layouts repeatedly correct
(`\frac` structure right, symbols wrong). Error modes: x→X case flips,
`|` over-prediction, `\lim\limits` runaways, one `<sos>` leak. Verdict: weights +
pipeline genuinely run; accuracy gap is render-style domain mismatch, not a broken
model. Full table: `ml/reports/inference_baseline.md`; predictions:
`ml/experiments/posformer_run1.json`.

Fallback comparison (BTTR, not executed — primary succeeded): would need the same
legacy-stack treatment for an older, weaker, archived model + another 77.5 MB
download; no evidence it beats PosFormer cross-dataset. Cheapest next accuracy
lever is CROHME-style rendering + small fine-tune, not switching to BTTR.
pix2tex comparison and phone-photo gap: untouched (no authorized photos).
