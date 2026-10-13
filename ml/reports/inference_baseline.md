# Inference baseline — PosFormer best.ckpt x MathWriting excerpt

Samples: 30 (MathWriting excerpt test/, ≤50-rule compliant). Renders: white-on-black PNG from InkML (polarity calibrated). Device: CPU. Beam: 10/max_len 200/alpha 1.0/T 1.0 (repo config).

## Aggregate (cross-dataset: CROHME-trained model on MathWriting renders)

- Strict token exact-match rate: 0/30 = 0.000
- Mean canonical CER: 0.912 (median 0.838)
- Samples whose GT contains out-of-vocab tokens: 19/30 (exact match impossible for these by construction)
- Latency: mean 29.2s, min 5.9s, max 88.0s per image (CPU, incl. beam search)

## Per-sample

| id | GT (normalizedLabel) | prediction | exact | CER | s | OOV |
|---|---|---|---|---|---|---|
| 000a4e8ca49c5a1c | `(x-y)/sqrt(2)` | `X - y / 5 q ^ { \prime } + ( 2 )` | no | 0.769 | 17.814 | - |
| 001083e26028da36 | `\nabla I=(I_{x},I_{y})` | `\frac { I } { I } = [ X ] { \frac { 1 } { I , I } |` | no | 1.0 | 32.909 | \nabla |
| 0017bb5822bcba69 | `P=P(C(Z))` | `| I | I | <sos> | I |` | no | 1.444 | 7.885 | Z |
| 002ae6d5dd4173e4 | `x_{1}-x_{2}+x_{0}=0` | `X _ { 1 } - X _ { 2 } + X _ { 0 } = X` | no | 0.308 | 29.046 | - |
| 00386113d577085b | `\langle a_{0},a_{1},...\rangle\in R^{\omega}` | `| a _ { a } , a _ { 1 } , | t | \leq | t |` | no | 0.719 | 28.512 | \langle,\omega,\rangle |
| 003ca9082c7047d3 | `\partial_{i}f=\frac{\partial f}{\partial\xi^{i}}:=\frac{\partial\overline{f}}{\partial\xi^{i}}` | `\sum \limits _ { i } I = \frac { 0 f } { d y ^ { 2 } } = \frac { 7 } { 2 z ^ { 1 } }` | no | 0.791 | 57.327 | :,\overline,\partial,\xi |
| 004c9413be3ff1be | `\langle A\rangle_{\psi}=||A\psi||^{2}` | `| t | \leq | t | \leq | t | \leq | t |` | no | 0.786 | 21.892 | \langle,\psi,\rangle |
| 004fc8d3f626f1d9 | `\delta_{j,j_{1}}\delta_{m,m_{1}}` | `\lim \limits _ { i } ^ { \int \limits _ { 1 } ^ { \prime } x } | x _ { 1 } \frac { 1 } { 1 }` | no | 1.455 | 45.603 | \delta |
| 0052b8e13b5f4a36 | `w(\neg\theta)=F_{\neg}(w(\theta))` | `H ( I - I ) = I ( \theta )` | no | 0.63 | 19.132 | \neg |
| 00692074bbc0f678 | `t\longrightarrow F(t,t_{0},x)` | `\lim \limits _ { 1 } ^ { \prime } \int \limits _ { 1 } \tan ( x )` | no | 1.08 | 25.255 | \longrightarrow |
| 006badbfc63bbd21 | `p=(p_{x},p_{y},p_{z})` | `| x - | x | , | x | \cdot | x |` | no | 1.067 | 18.568 | - |
| 0082d4aa943b9f8c | `|\frac{d^{2}y}{dx^{2}}|\approx\frac{1}{R}` | `| d ^ { 2 } \frac { y } { 1 x ^ { 2 } } | = \frac { 1 } { R }` | no | 0.5 | 29.66 | \approx |
| 0083f66ddd05c46c | `m_{i,j}=x^{i}\cdot x^{j}` | `\lim \limits _ { i j } = x ^ { i } - x ^ { j }` | no | 0.812 | 19.366 | - |
| 0090db2a639b5c98 | `S_{ijk}\rightarrow S_{ij}(\omega_{k})` | `\sum \limits _ { i , L \geq \int \limits _ { \prime } ( w _ { k } )` | no | 0.964 | 37.936 | \omega |
| 00915f0ffe17930e | `(g^{a}modp,g,p)` | `| a ^ { G } | \sin | x | , y , f |` | no | 1.0 | 26.556 | - |
| 009d124a50399bba | `J_{i}=\sum_{j}L_{ij}\frac{\partial F_{j}}{\partial x_{j}}` | `\int \limits _ { i } = \sum \limits _ { j } L _ { i j } \frac { f _ { i } } { X _ { i } }` | no | 0.838 | 61.131 | J,\partial |
| 009fb93aab47d6f5 | `\{f_{X}(\cdot;\theta)|\theta\in\Theta\}` | `\sum \limits _ { X } | t | , \theta | \leq | t | \leq | t |` | no | 0.893 | 36.474 | ;,\Theta,\\ |
| 00ad7566b9f1d872 | `\dot{x}(t)=f(x(t))` | `| x | x | x | t | \int | x | \leq | x |` | no | 1.2 | 19.804 | \dot |
| 00ba90fe7f71d8c6 | `\Omega((logn)/n^{2})` | `\{ ( \lim \limits _ { N } l ^ { 2 } )` | no | 0.824 | 24.398 | \Omega |
| 00c46c9b07b39bb7 | `l_{n}=kl_{n}\cdot\frac{b_{n}}{b_{a}}\cdot\frac{s_{n}}{s_{a}}` | `y _ { n } = | < \frac { b _ { n } } { b _ { a } } \frac { b _ { a } } { \int \limits _ { a } }` | no | 0.611 | 87.991 | - |
| 00d4fc6636cbf2d9 | `\tilde{g}_{n}=[\begin{matrix}g_{n}\\ \gamma_{n}\end{matrix}]` | `\alpha _ { n } = | x _ { n } | y _ { n } |` | no | 0.78 | 20.379 | \\,\begin,\end,\tilde |
| 00db5331b85f4d47 | `N=|V|` | `| I | I | I |` | no | 1.0 | 5.886 | - |
| 00eaf4f2d3d20bb1 | `B=ln(-b)` | `| x | - | x | - | x |` | no | 1.25 | 15.315 | - |
| 00fcddfee1ebfee6 | `2sin(x/2)` | `\sum \limits _ { \sin C } | x | \sin |` | no | 1.889 | 14.526 | - |
| 00fee560e6c9af79 | `\sqrt{1-\omega^{2}r_{0}^{2}}` | `\sqrt { 1 - L ) ^ { 2 } r _ { \gamma } r ^ { 2 }` | no | 0.611 | 26.503 | \omega |
| 010d0f9e951a7a44 | `x_{i}^{\prime}\equiv\frac{1}{1+e^{-\frac{x_{i}-\mu_{i}}{\sigma_{i}}}}` | `X _ { i } = \frac { 1 } { 1 } e ^ { 1 } \frac { - y _ { i - u _ { i } } { 1 } }` | no | 0.558 | 54.563 | \equiv |
| 010d4fea2361f01f | `Inj(M_{i})<\epsilon(n)` | `| \int \limits _ { i } l _ { L } ) C \sum ( M )` | no | 1.0 | 25.757 | \epsilon |
| 0111fa141bb73b48 | `-a^{n}u[-n-1]` | `- a ^ { n } - \sqrt [ 1 ] - 1 - I` | no | 0.818 | 19.457 | - |
| 0114e881d8b22bbb | `(\Lambda(A):A\in B_{b}(S))` | `| t | \leq | t | \leq | - | t | \leq | x | ) |` | no | 1.143 | 32.695 | :,\Lambda |
| 011f1f41eb55b661 | `(\frac{lnN}{N})\rightarrow0` | `| \frac { \sin N } { N } | \geq 0` | no | 0.619 | 14.899 | - |

## Analysis (added 2026-10-10)

- In-vocab-only subset (11/30 samples whose GT uses only the 113 CROHME tokens):
  exact 0/11, mean CER 0.922 — same as full set, so the vocab gap is NOT the main
  driver; the render-style domain gap dominates.
- Best cases show layout recognition works: `x_{1}-x_{2}+x_{0}=0` -> CER 0.308
  (only case + final digit wrong); 2nd-derivative fraction -> CER 0.500 with
  `\frac` structure correct; nested `\frac{1}{1+e^{...}}` -> CER 0.558.
- Recurring error patterns: lowercase->uppercase confusion (x->X, present in
  4+ samples); over-prediction of `|` (thin verticals: parens, bars, `1` all
  collapse to `|`); runaway `\lim\limits`/`\leq` loops on complex inputs;
  one `<sos>` token leaked mid-sequence (`0017bb5822bcba69`).
- CROHME vocab lacks Z D J K O Q U W entirely (verified in dictionary.txt) plus
  `\nabla \langle \rangle \partial \omega \psi \delta \ldots` — MathWriting's
  244-symbol coverage exceeds it. Any future fine-tune must extend the vocab.
- CPU latency scales with output length (5.9s for 3-token outputs, ~88s for
  long ones); GPU inference + batching will be needed for interactive use.

## Caveats

- Cross-dataset: checkpoint trained on CROHME renders; test images are MathWriting inks rendered 1:1 with PIL (stroke 4px), not organizer BMPs. Expect a domain gap vs CROHME-test numbers.
- Tokenizer mapping MathWriting->CROHME tokens is an approximation (organizer caption conventions unverifiable offline); strict exact-match is a lower bound, CER is the primary signal.
- 30 phone-photo-free samples: photo gap (perspective/lighting/blur) NOT measured — needs authorized phone photos (future work).
