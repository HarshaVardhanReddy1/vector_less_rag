"""Demo: how a ~4000-token node with text, tables, and images is chunked."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.processing.node_chunker import _content_to_atoms, _split_into_chunks, chunk_nodes
from backend.utils.token_utils import count_tokens

# ---------------------------------------------------------------------------
# Build a realistic ~4000-token node
# ---------------------------------------------------------------------------

INTRO = """\
Neural networks have transformed machine learning over the past decade. \
Deep architectures with millions of parameters now achieve superhuman performance \
on image recognition, natural language processing, and game playing tasks. \
This section reviews the core architectural components that make this possible \
and discusses the trade-offs involved in choosing between them."""

PARA_2 = """\
The choice of activation function significantly impacts gradient flow during \
backpropagation. Early networks used sigmoid and tanh, both of which suffer \
from vanishing gradients in deep architectures. The rectified linear unit (ReLU) \
addressed this by providing a constant gradient of 1 for positive inputs, \
dramatically improving training speed. Variants such as Leaky ReLU, ELU, and \
GELU have further refined this property for specific use cases."""

TABLE_1 = """\
| Activation | Formula          | Range       | Vanishing Gradient | Common Use         |
|------------|------------------|-------------|--------------------|--------------------|
| Sigmoid    | 1/(1+e^-x)       | (0, 1)      | Yes                | Binary output      |
| Tanh       | (e^x-e^-x)/...   | (-1, 1)     | Yes                | RNN hidden state   |
| ReLU       | max(0, x)        | [0, ∞)      | No (positive)      | Hidden layers      |
| Leaky ReLU | max(0.01x, x)    | (-∞, ∞)    | No                 | Hidden layers      |
| ELU        | x if x>0 else... | (-α, ∞)    | No                 | Deep networks      |
| GELU       | x·Φ(x)           | (-∞, ∞)    | No                 | Transformers       |
| Softmax    | e^xi/Σe^xj       | (0, 1)      | Yes                | Multi-class output |"""

IMAGE_BLOCK = """\
<IMAGE_CONTEXT src='figures/activation_curves.png' type='chart'>
Line chart showing activation function output curves plotted against input values \
from -4 to 4. X-axis: input value. Y-axis: activation output. Six curves are shown: \
Sigmoid (S-shaped, range 0–1), Tanh (S-shaped, range -1 to 1), ReLU (flat at 0 for \
negatives, linear slope 1 for positives), Leaky ReLU (small negative slope -0.01 \
for negatives, slope 1 for positives), ELU (smooth negative saturation), GELU \
(smooth curve similar to ReLU with slight negative dip around -0.2).

**Caption:** Figure 3. Comparison of common activation functions across the input range [-4, 4].
</IMAGE_CONTEXT>"""

PARA_3 = """\
Batch normalisation introduced by Ioffe and Szegedy (2015) addresses the problem \
of internal covariate shift by normalising the inputs to each layer across the \
mini-batch. This stabilises training and allows the use of higher learning rates. \
Layer normalisation, applied across the feature dimension instead of the batch \
dimension, is preferred in sequence models such as Transformers where batch sizes \
are small or variable."""

PARA_4 = """\
Residual connections, introduced in ResNet, allow gradients to flow directly \
through skip connections bypassing one or more layers. This architectural choice \
enabled training of networks with hundreds of layers by mitigating the vanishing \
gradient problem. The identity shortcut requires no additional parameters and \
adds negligible computational cost."""

TABLE_2 = """\
| Architecture | Depth  | Skip Connections | Params (M) | Top-1 Acc (ImageNet) |
|--------------|--------|------------------|------------|----------------------|
| VGG-16       | 16     | None             | 138        | 71.5%                |
| Inception-v3 | 48     | Inception module | 27         | 78.8%                |
| ResNet-50    | 50     | Residual         | 25         | 76.1%                |
| ResNet-152   | 152    | Residual         | 60         | 78.3%                |
| DenseNet-201 | 201    | Dense            | 20         | 77.4%                |
| EfficientNet | 77     | MBConv+squeeze   | 66         | 84.4%                |"""

PARA_5 = """\
Attention mechanisms, first popularised in neural machine translation, have become \
the cornerstone of modern language models. The self-attention operation computes \
pairwise similarity scores between all positions in a sequence, enabling the model \
to capture long-range dependencies that recurrent architectures struggle with. \
Multi-head attention extends this by projecting queries, keys, and values into \
multiple subspaces, allowing the model to attend to information from different \
representation spaces simultaneously."""

PARA_6 = """\
The feed-forward sublayer in a Transformer block applies a two-layer MLP \
independently to each position. Despite its simplicity, this component accounts \
for the majority of a Transformer's parameters when the hidden dimension is large. \
Recent work on mixture-of-experts (MoE) architectures replaces this dense \
feed-forward layer with a sparse set of experts, routing each token to only a \
subset of them and dramatically increasing model capacity without proportional \
compute cost."""

# Assemble full content
CONTENT = "\n\n".join([
    INTRO, PARA_2, TABLE_1, IMAGE_BLOCK, PARA_3, PARA_4, TABLE_2, PARA_5, PARA_6
])

node = {
    "heading": "3.2 Neural Network Architectures",
    "page": 14,
    "content": CONTENT,
    "token_count": count_tokens(CONTENT),
}

# ---------------------------------------------------------------------------
# Run the chunker
# ---------------------------------------------------------------------------

MAX_TOKENS = 1000

print("=" * 70)
print("INPUT NODE")
print(f"  heading     : {node['heading']}")
print(f"  page        : {node['page']}")
print(f"  token_count : {node['token_count']}")
print()

atoms = _content_to_atoms(CONTENT)
print(f"ATOMS  ({len(atoms)} total)")
for i, atom in enumerate(atoms, 1):
    tokens = count_tokens(atom)
    kind = (
        "IMAGE_CONTEXT" if atom.startswith("<IMAGE_CONTEXT")
        else "TABLE      " if atom.strip().startswith("|")
        else "PARAGRAPH  "
    )
    preview = atom[:60].replace("\n", " ").strip()
    print(f"  [{i:02d}] {kind}  {tokens:>4} tok  \"{preview}…\"")

print()
chunks = _split_into_chunks(CONTENT, MAX_TOKENS)
print(f"CHUNKS  ({len(chunks)} total, max_tokens={MAX_TOKENS})")
for i, chunk in enumerate(chunks, 1):
    tokens = count_tokens(chunk)
    preview = chunk[:80].replace("\n", " ").strip()
    print(f"  [{i}] {tokens:>4} tok  \"{preview}…\"")

print()
result = chunk_nodes([node], max_tokens=MAX_TOKENS)
print(f"OUTPUT NODES  ({len(result)} total)")
for n in result:
    print(f"  heading : {n['heading']}")
    print(f"  page    : {n['page']}")
    print(f"  tokens  : {n['token_count']}")
    print()
