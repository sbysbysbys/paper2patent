"""Academic → Patent terminology mapping.

Provides Chinese terminology conversion for writing patent-style prose.
"""

# Academic phrases → Patent phrases (Chinese)
ACADEMIC_TO_PATENT = {
    # Hedging → definitive
    "可能": "可以",
    "通常": "",
    "一般来说": "",
    "大致": "",
    "约": "为",
    "接近": "",
    "左右": "",
    "似乎": "",
    "或许": "",

    # Self-reference
    "我们的方法": "本申请的方法",
    "我们提出": "本申请提供",
    "我们的模型": "本申请的模型",
    "本文": "本申请",
    "本研究": "本申请",
    "我们": "本申请",
    "our method": "the present application",
    "we propose": "the present application provides",
    "our": "the",

    # Experimental → structural
    "实验结果表明": "",
    "在数据集X上达到": "",
    "比基线高": "",
    "优于": "",
    "accuracy": "",
    "F1 score": "",
    "BLEU score": "",

    # Vague → precise
    "等等": "",  # forbidden in claims
    "诸如此类": "",
    "最好是": "优选地",
    "可以理解": "应当理解",

    # Paper → patent structure terms
    "related work": "背景技术",
    "introduction": "技术领域",
    "method": "具体实施方式",
    "experiment": "",
    "conclusion": "",
    "discussion": "",

    # Common academic verbs → patent verbs
    "提取": "获取",
    "计算": "确定",
    "使用": "利用",
    "显示": "指示",
    "表明": "指示",
    "预测": "确定",
}


# Patent boilerplate phrases (CN)
PATENT_BOILERPLATE = {
    "technical_field_opening": "本发明涉及{field}技术领域，具体涉及一种{title}的方法和装置。",
    "background_problem": "目前，{problem_description}。",
    "background_limitation": "然而，现有技术中存在以下问题：{limitations}。",
    "invention_purpose": "本发明旨在解决{problem}的问题。",
    "invention_summary": "本发明提供一种{title}方法，包括以下步骤：{steps}。",
    "beneficial_effects": "本发明的有益效果包括：{effects}。",
    "drawing_brief": "图{num}是{description}。",
    "embodiment_title": "实施例{num}",
    "embodiment_opening": "下面结合附图{fig_num}对本发明实施例{emb_num}进行详细描述。",
    "step_template": "步骤S{num}：通过{actor}对{input_data}进行{operation}，得到{output_data}。",
    "claim_method_independent": "一种{subject}方法，其特征在于，包括：",
    "claim_system_independent": "一种{subject}装置，其特征在于，包括：",
    "claim_dependent_single": "根据权利要求{ref}所述的{category}，其特征在于，{limitation}。",
    "claim_dependent_multi": "根据权利要求{refs}任一项所述的{category}，其特征在于，{limitation}。",
}


# English → Chinese patent terms for common ML concepts
ML_PATENT_TERMS = {
    "neural network": "神经网络",
    "deep learning": "深度学习",
    "transformer": "变换器网络",
    "attention mechanism": "注意力机制",
    "encoder": "编码器",
    "decoder": "解码器",
    "embedding": "嵌入层",
    "token": "词元",
    "layer": "层",
    "training": "训练",
    "inference": "推理",
    "loss function": "损失函数",
    "optimizer": "优化器",
    "gradient": "梯度",
    "backpropagation": "反向传播",
    "convolution": "卷积",
    "pooling": "池化",
    "activation function": "激活函数",
    "dropout": "随机失活层",
    "batch normalization": "批归一化层",
    "residual connection": "残差连接",
    "feed-forward": "前馈",
    "multi-head attention": "多头注意力",
    "self-attention": "自注意力",
    "cross-attention": "交叉注意力",
    "positional encoding": "位置编码",
    "classifier": "分类器",
    "regressor": "回归器",
    "feature extractor": "特征提取器",
    "generator": "生成器",
    "discriminator": "判别器",
    "processor": "处理器",
    "memory": "存储器",
    "sensor": "传感器",
    "camera": "摄像头",
    "LiDAR": "激光雷达",
    "controller": "控制器",

    # ── Learned from 109 real CN AI/ML patents ──
    "knowledge distillation": "知识蒸馏",
    "contrastive learning": "对比学习",
    "self-supervised learning": "自监督学习",
    "meta-learning": "元学习",
    "few-shot learning": "少样本学习",
    "zero-shot learning": "零样本学习",
    "reinforcement learning": "强化学习",
    "federated learning": "联邦学习",
    "graph neural network": "图神经网络",
    "spiking neural network": "脉冲神经网络",
    "neural architecture search": "神经架构搜索",
    "diffusion model": "扩散模型",
    "generative adversarial network": "生成对抗网络",
    "variational autoencoder": "变分自编码器",
    "mixture of experts": "混合专家网络",
    "multi-modal": "多模态",
    "cross-modal": "跨模态",
    "pre-trained model": "预训练模型",
    "fine-tuning": "微调",
    "quantization": "量化",
    "pruning": "剪枝",
    "model compression": "模型压缩",
    "edge deployment": "边缘部署",
    "collaborative inference": "协同推理",
    "knowledge graph": "知识图谱",
    "semantic segmentation": "语义分割",
    "object detection": "目标检测",
    "instance segmentation": "实例分割",
    "scene understanding": "场景理解",
    "trajectory prediction": "轨迹预测",
    "motion planning": "运动规划",
    "sensor fusion": "传感器融合",
    "time series forecasting": "时序预测",
    "anomaly detection": "异常检测",
    "intrusion detection": "入侵检测",
    "adversarial attack": "对抗攻击",
    "defense mechanism": "防御机制",
    "explainable AI": "可解释人工智能",
}

# ── Learned from 109 real CN AI/ML patents: patent-specific boilerplate ──
LEARNED_BOILERPLATE = {
    "abstract_opening": "本发明公开了一种{title}，{core_idea}。",
    "tech_field": "本发明涉及{field}技术领域，具体涉及一种{title}。",
    "background_problem": "随着{domain}技术的快速发展，{current_situation}。然而，现有技术中存在以下不足：{limitations}。",
    "invention_purpose": "本发明旨在解决{problem}，提供一种{title}。",
    "tech_solution": "为实现上述目的，本发明采用如下技术方案：",
    "beneficial_effects_header": "与现有技术相比，本发明具有以下有益效果：",
    "beneficial_effect_item": "{index}. {description}。",
    "brief_description_drawings": "图{num}是本发明实施例提供的{description}的{type}示意图。",
    "embodiment_heading": "实施例{num}",
    "embodiment_body": "本实施例提供一种{title}的具体实现方式。",
    "step_description": "步骤S{num}：{description}。",
    "closing": "以上所述仅为本发明的优选实施例而已，并不用于限制本发明。对于本领域技术人员来说，本发明可以有各种更改和变化。凡在本发明的精神和原则之内，所作的任何修改、等同替换、改进等，均应包含在本发明的保护范围之内。",
    "electronic_device_claim": "一种电子设备，包括：一个或多个处理器；存储装置，用于存储一个或多个程序；当所述一个或多个程序被所述一个或多个处理器执行时，使得所述一个或多个处理器实现如权利要求{claim_range}中任一所述的方法。",
    "storage_medium_claim": "一种计算机可读存储介质，其上存储有计算机程序，所述计算机程序被处理器执行时实现如权利要求{claim_range}中任一所述的方法。",
}

# ── Learned transition phrases (from 109 patents) ──
LEARNED_TRANSITIONS = {
    "in_some_embodiments": "在一些实施例中",
    "in_one_embodiment": "在一个实施例中",
    "exemplarily": "示例性地",
    "optionally": "可选地",
    "preferably": "优选地",
    "specifically": "具体地",
    "further": "进一步地",
    "it_should_be_understood": "应当理解",
    "it_should_be_noted": "需要说明的是",
    "those_skilled_in_art": "本领域技术人员",
    "obviously": "显然",
    "without_departing_from": "在不脱离",
    "in_combination_with_drawings": "结合附图",
    "detailed_description_below": "下面结合附图对本发明作进一步详细描述",
}

# ── Patent section headings (both 【】 and plain formats) ──
PATENT_SECTION_HEADINGS = {
    "cn_bracketed": ["【技术领域】", "【背景技术】", "【发明内容】", "【附图说明】", "【具体实施方式】"],
    "cn_plain": ["技术领域", "背景技术", "发明内容", "技术方案", "有益效果", "附图说明", "具体实施方式"],
    "cn_sub": ["技术问题", "技术方案", "有益效果", "实施例"],
}


def translate_term(english: str) -> str:
    """Translate an English ML term to Chinese patent terminology."""
    return ML_PATENT_TERMS.get(english.lower(), english)


def academic_to_patent_phrase(text: str) -> str:
    """Replace academic phrases with patent-appropriate alternatives."""
    result = text
    for acad, patent in ACADEMIC_TO_PATENT.items():
        if acad in result:
            result = result.replace(acad, patent)
    return result


def boilerplate(key: str, **kwargs) -> str:
    """Get a patent boilerplate phrase with variable substitution."""
    template = PATENT_BOILERPLATE.get(key, "")
    if template and kwargs:
        return template.format(**kwargs)
    return template
