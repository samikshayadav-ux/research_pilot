"""
Demo data for ResearchPilot AI.
5 landmark NLP/ML papers for a rich, populated demo experience.
"""

DEMO_PAPERS = [
    {
        "paper_id":    "demo_001",
        "filename":    "attention_is_all_you_need.pdf",
        "title":       "Attention Is All You Need",
        "authors":     ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"],
        "year":        "2017",
        "page_count":  15,
        "abstract":    "We propose the Transformer, a novel neural network architecture based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelisable and requiring significantly less time to train.",
        "topics":      ["neural machine translation", "sequence-to-sequence", "attention mechanism", "natural language processing"],
        "methods":     ["transformer", "self-attention", "multi-head attention", "positional encoding"],
        "datasets":    ["WMT 2014 English-German", "WMT 2014 English-French", "English Constituency"],
        "metrics":     ["BLEU", "Perplexity"],
        "key_findings": [
            "The Transformer achieves 28.4 BLEU on WMT 2014 English-German, outperforming all previously published ensembles.",
            "Training the big Transformer model took 3.5 days on 8 P100 GPUs — far less than recurrent baselines.",
            "Self-attention layers are faster than recurrent layers when the sequence length is shorter than the representation dimensionality.",
        ],
        "limitations": [
            "Quadratic complexity with respect to sequence length limits applicability to very long sequences.",
            "Lacks inherent sequential inductive bias that RNNs provide.",
        ],
        "demo": True,
    },
    {
        "paper_id":    "demo_002",
        "filename":    "bert_pretraining.pdf",
        "title":       "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "authors":     ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"],
        "year":        "2018",
        "page_count":  16,
        "abstract":    "We introduce BERT, a new language representation model designed to pre-train deep bidirectional representations from unlabelled text by jointly conditioning on both left and right context. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks.",
        "topics":      ["language model pre-training", "transfer learning", "natural language understanding", "contextual embeddings"],
        "methods":     ["transformer", "masked language modeling", "next sentence prediction", "fine-tuning", "bert"],
        "datasets":    ["BooksCorpus", "English Wikipedia", "GLUE", "SQuAD", "MultiNLI"],
        "metrics":     ["Accuracy", "F1", "EM"],
        "key_findings": [
            "BERT achieves 80.5% on GLUE, outperforming the previous state-of-the-art by 7.7%.",
            "Fine-tuned BERT on SQuAD 1.1 achieves 93.2% F1 score, surpassing human performance.",
            "Bidirectional pre-training is crucial; unidirectional models are significantly worse.",
        ],
        "limitations": [
            "Pre-training is computationally expensive requiring large GPU clusters.",
            "Masked language model creates a mismatch between pre-training and fine-tuning.",
            "Maximum sequence length of 512 tokens limits processing of long documents.",
        ],
        "demo": True,
    },
    {
        "paper_id":    "demo_003",
        "filename":    "rag_knowledge_intensive.pdf",
        "title":       "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "authors":     ["Patrick Lewis", "Ethan Perez", "Aleksandra Piktus", "Fabio Petroni"],
        "year":        "2020",
        "page_count":  14,
        "abstract":    "Large pre-trained language models have been shown to store factual knowledge in their parameters, but their ability to access and manipulate knowledge is still limited. We propose RAG, a general-purpose fine-tuning recipe for retrieval-augmented generation combining parametric and non-parametric memory for language generation.",
        "topics":      ["retrieval-augmented generation", "open-domain question answering", "knowledge-intensive NLP", "generative models"],
        "methods":     ["rag", "dense passage retrieval", "transformer", "bert", "seq2seq"],
        "datasets":    ["Natural Questions", "TriviaQA", "MS-MARCO", "FEVER", "Jeopardy"],
        "metrics":     ["Exact Match", "BLEU", "ROUGE"],
        "key_findings": [
            "RAG outperforms parametric seq2seq models on open-domain QA benchmarks.",
            "RAG-Sequence model achieves new state-of-the-art on three open-domain QA tasks.",
            "Generated answers are more specific, diverse, and factual than seq2seq baselines.",
        ],
        "limitations": [
            "Retrieval corpus must be updated to reflect new knowledge.",
            "Index construction is expensive and requires significant storage.",
            "Prone to hallucination when retrieved documents are noisy or irrelevant.",
        ],
        "demo": True,
    },
    {
        "paper_id":    "demo_004",
        "filename":    "gpt3_language_models.pdf",
        "title":       "Language Models are Few-Shot Learners",
        "authors":     ["Tom B. Brown", "Benjamin Mann", "Nick Ryder", "Melanie Subbiah", "Jared Kaplan"],
        "year":        "2020",
        "page_count":  75,
        "abstract":    "We train GPT-3, an autoregressive language model with 175 billion parameters, and test its performance in the few-shot setting. GPT-3 achieves strong performance on many NLP datasets, including translation, question-answering, and cloze tasks, without any gradient updates or fine-tuning.",
        "topics":      ["large language models", "few-shot learning", "in-context learning", "natural language generation"],
        "methods":     ["transformer", "autoregressive language modeling", "few-shot prompting", "in-context learning", "gpt"],
        "datasets":    ["SuperGLUE", "TriviaQA", "WebText", "CommonCrawl", "BooksCorpus"],
        "metrics":     ["Accuracy", "F1", "BLEU", "Perplexity"],
        "key_findings": [
            "GPT-3 with 175B parameters achieves strong few-shot results without fine-tuning, matching fine-tuned BERT on many tasks.",
            "In-context learning emerges at scale: performance improves sharply as model size increases from 125M to 175B parameters.",
            "GPT-3 achieves 71.2% on TriviaQA in few-shot setting, surpassing previous fine-tuned state-of-the-art.",
        ],
        "limitations": [
            "Extremely high computational cost of training and inference.",
            "In-context learning is sensitive to prompt format and example selection.",
            "Model can generate confident but factually incorrect text (hallucination).",
            "Limited interpretability — it is unclear what the model has 'learned'.",
        ],
        "demo": True,
    },
    {
        "paper_id":    "demo_005",
        "filename":    "llama2_open_foundation.pdf",
        "title":       "Llama 2: Open Foundation and Fine-Tuned Chat Models",
        "authors":     ["Hugo Touvron", "Louis Martin", "Kevin Stone", "Peter Albert", "Amjad Almahairi"],
        "year":        "2023",
        "page_count":  77,
        "abstract":    "We develop and release Llama 2, a collection of pretrained and fine-tuned large language models ranging from 7B to 70B parameters. Llama 2-Chat models are optimised for dialogue use cases and outperform open-source chat models on most benchmarks, while also being safer according to human evaluation.",
        "topics":      ["large language models", "instruction tuning", "RLHF", "open-source AI", "chat models"],
        "methods":     ["transformer", "rlhf", "supervised fine-tuning", "constitutional ai", "grouped query attention"],
        "datasets":    ["CommonCrawl", "C4", "GitHub", "Wikipedia", "Books", "ArXiv", "StackExchange"],
        "metrics":     ["Accuracy", "Win Rate", "Safety Score", "Helpfulness"],
        "key_findings": [
            "Llama 2-Chat 70B outperforms most open-source chat models and is competitive with closed-source models on human evaluation.",
            "RLHF with iterative reward model training significantly improves safety and helpfulness alignment.",
            "Ghost attention technique helps maintain context across multi-turn conversations.",
        ],
        "limitations": [
            "Still lags behind GPT-4 on complex reasoning benchmarks.",
            "English-centric training data limits multilingual performance.",
            "RLHF alignment can introduce sycophancy and over-refusal behaviours.",
        ],
        "demo": True,
    },
]

DEMO_CHUNKS = {
    "demo_001": [
        {"chunk_id": "demo_001_0", "paper_id": "demo_001", "page": 1, "text": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.", "score": 0.95},
        {"chunk_id": "demo_001_1", "paper_id": "demo_001", "page": 3, "text": "The Transformer follows an encoder-decoder structure using stacked self-attention and point-wise, fully connected layers for both the encoder and decoder. Multi-head attention allows the model to jointly attend to information from different representation subspaces at different positions. Positional encodings are added to the input embeddings at the bottoms of the encoder and decoder stacks.", "score": 0.90},
        {"chunk_id": "demo_001_2", "paper_id": "demo_001", "page": 8, "text": "On the WMT 2014 English-to-German translation task, the big transformer model outperforms the best previously reported models including ensembles by more than 2.0 BLEU, establishing a new state-of-the-art BLEU score of 28.4. The model was trained on 8 NVIDIA P100 GPUs for 3.5 days.", "score": 0.85},
    ],
    "demo_002": [
        {"chunk_id": "demo_002_0", "paper_id": "demo_002", "page": 1, "text": "BERT is designed to pre-train deep bidirectional representations from unlabelled text by jointly conditioning on both left and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks without substantial task-specific architecture modifications.", "score": 0.95},
        {"chunk_id": "demo_002_1", "paper_id": "demo_002", "page": 4, "text": "We use two steps in our framework: pre-training and fine-tuning. During pre-training, the model is trained on unlabelled data over different pre-training tasks. For fine-tuning, the BERT model is first initialized with the pre-trained parameters, and all of the parameters are fine-tuned using labelled data from the downstream tasks. Each downstream task has separate fine-tuned models.", "score": 0.90},
        {"chunk_id": "demo_002_2", "paper_id": "demo_002", "page": 10, "text": "BERT obtains new state-of-the-art results on eleven natural language processing tasks, including pushing the GLUE score to 80.5% (7.7% point absolute improvement), MultiNLI accuracy to 86.7% (4.6% absolute improvement), SQuAD v1.1 question answering Test F1 to 93.2 (1.5 point absolute improvement) over the previous best system.", "score": 0.88},
    ],
    "demo_003": [
        {"chunk_id": "demo_003_0", "paper_id": "demo_003", "page": 1, "text": "We propose RAG models where the parametric memory is a pre-trained seq2seq model and the non-parametric memory is a dense vector index of Wikipedia, accessed with a pre-trained neural retriever. We compare two RAG formulations, one which conditions on the same retrieved passages across the whole generated sequence (RAG-Sequence), and another which can use different passages per token (RAG-Token).", "score": 0.95},
        {"chunk_id": "demo_003_1", "paper_id": "demo_003", "page": 5, "text": "For open-domain QA, RAG outperforms parametric seq2seq models even when those models are provided with gold knowledge documents. On Natural Questions, RAG achieves 44.5 Exact Match score compared to 38.6 for the strongest parametric baseline, an improvement of 5.9 points.", "score": 0.92},
        {"chunk_id": "demo_003_2", "paper_id": "demo_003", "page": 9, "text": "RAG models generate answers that are more factual, specific, and diverse. Human evaluation confirms that RAG generates hallucination-free answers more often than seq2seq models, and produces text with higher factual correctness ratings on both NQ and MS-MARCO.", "score": 0.87},
    ],
    "demo_004": [
        {"chunk_id": "demo_004_0", "paper_id": "demo_004", "page": 1, "text": "We present GPT-3, an autoregressive language model with 175 billion parameters, 10x more than any previous non-sparse language model. We test GPT-3 in the few-shot setting, and for all tasks, GPT-3 is applied without any gradient updates or fine-tuning, with tasks and few-shot demonstrations specified purely via text interaction.", "score": 0.95},
        {"chunk_id": "demo_004_1", "paper_id": "demo_004", "page": 12, "text": "For in-context learning, each task is specified via a natural language description and a small number of examples. We find that GPT-3 can perform well with just a few examples (few-shot), a single example (one-shot), or even no examples at all (zero-shot). Performance scales strongly with model size.", "score": 0.92},
        {"chunk_id": "demo_004_2", "paper_id": "demo_004", "page": 30, "text": "GPT-3 achieves 71.2% on TriviaQA in the few-shot setting, surpassing the previous state-of-the-art. On SuperGLUE, GPT-3 few-shot scores 71.8, approaching but not matching fine-tuned BERT-Large. GPT-3 can generate coherent long-form text nearly indistinguishable from human writing.", "score": 0.88},
    ],
    "demo_005": [
        {"chunk_id": "demo_005_0", "paper_id": "demo_005", "page": 1, "text": "We release Llama 2, a family of pretrained and fine-tuned LLMs at scales of 7B, 13B, and 70B parameters. Llama 2-Chat models are optimised for dialogue. We describe our approach to fine-tuning and safety improvements, and share novel observations about the emergence of tool usage and temporal organisation in chat models trained with RLHF.", "score": 0.95},
        {"chunk_id": "demo_005_1", "paper_id": "demo_005", "page": 8, "text": "Our RLHF approach uses iterative reward model training based on human preference data. Safety is improved through both supervised safety fine-tuning data and RLHF red-teaming. Ghost attention (GAtt) is introduced to help the model maintain instruction context across multiple dialogue turns.", "score": 0.90},
        {"chunk_id": "demo_005_2", "paper_id": "demo_005", "page": 40, "text": "Llama 2-Chat 70B outperforms all open-source chat models on the majority of human evaluation benchmarks and is close to ChatGPT. However, it still lags behind GPT-4 on complex reasoning. The model achieves strong safety scores while maintaining high helpfulness ratings in human evaluation.", "score": 0.86},
    ],
}

DEMO_GAPS = {
    "common_limitations": [
        "Computational cost of large-scale pre-training limits accessibility to well-resourced labs",
        "Maximum sequence length constraints (512–8K tokens) hinder long-document processing",
        "Hallucination persists in generative models even with retrieval augmentation (RAG)",
        "Prompt sensitivity: small phrasing changes cause large performance swings in LLMs",
        "Fine-tuning data requirements remain substantial for specialised domains",
    ],
    "underexplored_areas": [
        "Cross-lingual and multilingual generalisation of attention mechanisms",
        "RAG applied to real-time scientific literature and patent databases",
        "Continual learning without catastrophic forgetting in large-scale LLMs",
        "Edge deployment of large transformer models on resource-constrained hardware",
    ],
    "missing_comparisons": [
        "Direct comparison of RAG vs. instruction-tuned LLMs (GPT-3/4) on open-domain QA",
        "Sparse / linear attention variants vs. standard self-attention on long documents",
        "RLHF alignment strategies: PPO vs. DPO vs. Constitutional AI side-by-side",
        "BERT encoder-only vs. GPT decoder-only on understanding tasks",
    ],
    "dataset_gaps": [
        "Evaluation on domain-specific corpora (medical, legal, scientific) is largely absent",
        "Multilingual benchmarks beyond English-German / French translation are underrepresented",
        "Long-document benchmarks (>10K tokens) absent from standard model evaluations",
        "Low-resource language datasets not systematically included in training or eval",
    ],
    "evaluation_gaps": [
        "Human evaluation of factual correctness rarely reported consistently across papers",
        "Latency and throughput (tokens/sec) benchmarks missing from most papers",
        "Robustness to adversarial and out-of-distribution inputs not evaluated",
        "Carbon footprint and energy consumption rarely disclosed",
    ],
    "methodological_gaps": [
        "Interpretability of learned attention patterns remains poorly understood",
        "Uncertainty quantification in generative outputs not addressed systematically",
        "Privacy implications of memorising training data not studied at scale",
        "Theoretical understanding of in-context learning is still limited",
    ],
    "future_directions": [
        "Combining sparse retrieval with dense neural retrieval for better efficiency and accuracy",
        "Efficient long-context transformers using linear or sliding-window attention mechanisms",
        "Domain-adaptive pre-training for scientific and biomedical literature using RAG",
        "Reducing hallucination through grounded decoding with enforced citation verification",
    ],
}

DEMO_COMPARISON = {
    "problem_statement": {
        "demo_001": "Sequence-to-sequence transduction (machine translation) using solely attention — removing recurrence and convolutions",
        "demo_002": "Learning deep bidirectional contextual representations for general-purpose NLP via fine-tuning",
        "demo_003": "Augmenting parametric LM knowledge with non-parametric retrieval for knowledge-intensive QA",
        "demo_004": "Achieving strong NLP task performance via few-shot prompting with very large language models",
        "demo_005": "Open, safe, and helpful large-scale chat models trained with RLHF and safety alignment",
    },
    "methodology": {
        "demo_001": "Encoder-decoder Transformer with multi-head self-attention and position-wise feed-forward layers",
        "demo_002": "Bidirectional Transformer pre-trained with Masked LM + Next Sentence Prediction objectives",
        "demo_003": "Seq2seq generator (BART) + DPR retriever over dense Wikipedia index; RAG-Token / RAG-Sequence",
        "demo_004": "Autoregressive language modelling at 175B scale; in-context few-shot prompting at inference",
        "demo_005": "Supervised fine-tuning + RLHF with iterative reward models; Ghost Attention for multi-turn",
    },
    "model_architecture": {
        "demo_001": "6-layer enc-dec Transformer, 512-dim, 8 heads (base); 1024-dim, 16 heads (big)",
        "demo_002": "12-layer bidirectional Transformer (BERT-Base, 110M); 24-layer (BERT-Large, 340M)",
        "demo_003": "BART-large generator (400M) + BERT-based DPR retriever; FAISS index over Wikipedia",
        "demo_004": "96-layer decoder-only Transformer, 12288-dim, 96 heads; 175B parameters total",
        "demo_005": "Grouped-query attention decoder-only Transformer: 7B / 13B / 70B parameter variants",
    },
    "datasets": {
        "demo_001": "WMT 2014 EN-DE, WMT 2014 EN-FR, English Constituency Parsing",
        "demo_002": "BooksCorpus + English Wikipedia (pre-train); GLUE, SQuAD, MultiNLI (fine-tune)",
        "demo_003": "Natural Questions, TriviaQA, WebQuestions, MS-MARCO, FEVER",
        "demo_004": "CommonCrawl, WebText2, Books, Wikipedia, SuperGLUE, TriviaQA",
        "demo_005": "CommonCrawl, C4, GitHub, Wikipedia, Books, ArXiv, StackExchange (2T tokens)",
    },
    "metrics": {
        "demo_001": "BLEU score (translation)",
        "demo_002": "Accuracy, F1 score, Exact Match",
        "demo_003": "Exact Match, BLEU, ROUGE-L",
        "demo_004": "Accuracy, F1, BLEU, Perplexity",
        "demo_005": "Win Rate (human eval), Safety Score, Helpfulness Score",
    },
    "key_results": {
        "demo_001": "28.4 BLEU on EN-DE (new SOTA); 3.5 days training on 8 P100s vs. weeks for RNNs",
        "demo_002": "80.5% GLUE (+7.7%); 93.2 F1 SQuAD (surpasses human performance)",
        "demo_003": "44.5 EM on NQ (+5.9 over parametric seq2seq); more factual, diverse outputs",
        "demo_004": "71.2% TriviaQA (few-shot SOTA); in-context learning emerges at scale",
        "demo_005": "Llama 2-Chat 70B competitive with ChatGPT; strong safety + helpfulness balance",
    },
    "limitations": {
        "demo_001": "O(n²) attention complexity; no sequential inductive bias; limited to translation tasks",
        "demo_002": "Expensive pre-training; 512-token limit; pre-train / fine-tune input distribution mismatch",
        "demo_003": "Static retrieval corpus; expensive FAISS index; retrieval noise causes hallucination",
        "demo_004": "Extremely high inference cost; prompt sensitivity; factual hallucinations; opaque reasoning",
        "demo_005": "Still lags GPT-4 on reasoning; English-centric; RLHF can introduce sycophancy",
    },
    "future_work": {
        "demo_001": "Extending to other modalities; local restricted attention; task-agnostic architecture",
        "demo_002": "Larger models (RoBERTa, ALBERT); domain-adaptive pre-training; reducing compute",
        "demo_003": "Streaming / updatable index; hybrid sparse-dense retrieval; domain-specific RAG",
        "demo_004": "Instruction tuning (InstructGPT); RLHF alignment; tool use; multimodal extensions",
        "demo_005": "Code and tool use at scale; multilingual alignment; long-context improvements",
    },
}

DEMO_REVIEW = """## 1. Introduction

This literature review surveys five landmark papers that define the modern large language model (LLM) landscape: **Attention Is All You Need** [Vaswani et al., 2017], **BERT** [Devlin et al., 2018], **RAG** [Lewis et al., 2020], **GPT-3** [Brown et al., 2020], and **Llama 2** [Touvron et al., 2023]. Together they trace a progression from foundational attention-based architectures, through bidirectional pre-training and retrieval augmentation, to scaled few-shot learners and RLHF-aligned chat assistants — forming the backbone of contemporary AI research and industry deployment.

## 2. Existing Approaches

**[Attention Is All You Need]** introduced the Transformer architecture, replacing recurrence with self-attention and enabling massive parallelisation. Achieving 28.4 BLEU on WMT EN-DE, it established the foundational building block for virtually all subsequent language models.

**[BERT]** extended the Transformer to bidirectional pre-training using Masked LM and Next Sentence Prediction. Pre-trained on BooksCorpus and Wikipedia, BERT achieved state-of-the-art on 11 NLP benchmarks including 80.5% GLUE and 93.2 F1 on SQuAD, demonstrating the power of generalised representations fine-tuned for downstream tasks.

**[RAG]** addressed parametric knowledge limitations by combining a BART seq2seq generator with a DPR retriever over a Wikipedia FAISS index. RAG outperforms purely parametric models on open-domain QA (44.5 EM on Natural Questions) and produces more factual, traceable outputs.

**[Language Models are Few-Shot Learners (GPT-3)]** demonstrated that scaling autoregressive language models to 175B parameters enables strong few-shot performance across dozens of NLP tasks without any gradient updates, purely through in-context prompting.

**[Llama 2]** released open-weight models from 7B to 70B parameters optimised for dialogue via supervised fine-tuning and RLHF, making capable chat LLMs accessible to the research community while addressing safety and alignment concerns.

## 3. Comparison of Approaches

All five papers share the Transformer as their architectural foundation, yet diverge in objective and paradigm. Vaswani et al. target translation (encoder-decoder); Devlin et al. target understanding (encoder-only, fine-tuning); Lewis et al. combine retrieval with generation; Brown et al. scale decoder-only models for zero/few-shot prompting; Touvron et al. align decoder-only models with human preferences via RLHF. A critical differentiator is the role of external knowledge: BERT and GPT-3 rely solely on parametric (weight-encoded) knowledge, whereas RAG explicitly accesses non-parametric retrieval memory. Llama 2 extends GPT-style models with alignment techniques absent from earlier work.

## 4. Key Findings

The Transformer proved that attention alone suffices for high-quality sequence transduction. BERT demonstrated that bidirectional pre-training substantially outperforms unidirectional pre-training for understanding tasks. RAG showed that non-parametric retrieval complements parametric knowledge, reducing hallucination. GPT-3 revealed emergent few-shot capabilities at scale, suggesting that model size is a key driver of general-purpose NLP capability. Llama 2 established that open models can approach closed commercial models in helpfulness while maintaining safety, lowering barriers for academic research.

## 5. Limitations

Common limitations include: (1) **computational cost** — training and inference at scale require prohibitive GPU resources; (2) **sequence length constraints** — BERT's 512-token limit and Transformer quadratic complexity restrict long-document use; (3) **hallucination** — even RAG is susceptible when retrieved documents are noisy; (4) **prompt sensitivity** — GPT-3's few-shot performance is fragile with respect to prompt wording; (5) **alignment gaps** — Llama 2-Chat still lags GPT-4 on complex reasoning despite RLHF.

## 6. Research Gaps

Notable gaps include: (1) multilingual and cross-lingual evaluation beyond EN-DE/FR; (2) domain-specific evaluation (medical, legal, scientific corpora); (3) long-document processing without truncation; (4) continual knowledge updating without full retraining; (5) rigorous, consistent human evaluation of factual correctness; (6) carbon footprint and efficiency reporting.

## 7. Future Directions

Promising avenues include: (1) linear-complexity attention for long-document tasks; (2) streaming, updatable retrieval indices for time-sensitive knowledge; (3) hybrid sparse-dense retrieval combined with RLHF-aligned generation; (4) grounded decoding with citation enforcement to reduce hallucination; (5) lightweight edge-deployable model variants; (6) multilingual alignment and low-resource language support.

*[Demo mode — connect IBM watsonx credentials for AI-generated reviews tailored to your own uploaded papers.]*
"""
