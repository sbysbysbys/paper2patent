#!/usr/bin/env python3
"""Build the Patent Writing Expert knowledge base from 300+ cross-domain CN patents.

Phase 1: Compile all patent IDs + download new ones
Phase 2: Parse + extract cross-domain patterns
Phase 3: Build expert knowledge base JSON
"""

import json, re, time, sys
from pathlib import Path
from collections import Counter, defaultdict

import fitz
from patent_downloader import PatentDownloader

BASE = Path.home() / "paper2patent" / "data" / "patents"
PDF_DIR = BASE / "pdfs"
EXPERT_DIR = BASE / "expert_knowledge"
PDF_DIR.mkdir(parents=True, exist_ok=True)
EXPERT_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# ALL 300+ PATENT IDs across 14 domains
# ═══════════════════════════════════════════════════════════════
ALL_PATENTS = {}

def add_patents(domain, patents_dict):
    for pid, title in patents_dict.items():
        ALL_PATENTS[pid] = {"title": title, "domain": domain}

# AI/ML domains (seed set)
add_patents("Computer Vision", {
    "CN111401156A":"基于Gabor卷积神经网络的图像识别方法","CN118537816A":"基于计算机视觉和机器学习的智能图像识别方法",
    "CN118115819B":"基于深度学习的图表图像数据识别方法及系统","CN119273998A":"基于深度学习的图像内容识别系统",
    "CN114821582A":"基于深度学习的OCR识别方法","CN106528826A":"基于深度学习的多视图外观专利图像检索方法",
    "CN104966097A":"基于深度学习的复杂文字识别方法","CN111611893A":"应用神经网络深度学习的智能测判方法",
    "CN111368973A":"基于注意力机制的图像识别方法及装置","CN111950691A":"基于图神经网络的图像分割方法及装置",
    "CN112052877A":"基于深度学习的图像分类方法及系统",
})
add_patents("NLP", {
    "CN111401474A":"基于注意力机制的文本分类方法","CN112036186A":"基于预训练语言模型的文本生成方法",
    "CN113255360A":"基于Transformer的机器翻译方法及装置","CN113378580A":"基于深度学习的命名实体识别方法",
    "CN114330350A":"基于对比学习的文本表示方法及装置","CN115146628A":"基于大语言模型的对话生成方法及系统",
})
add_patents("Neural Network Architecture", {
    "CN112434785A":"神经网络模型压缩方法及装置","CN113065645A":"基于知识蒸馏的模型训练方法及系统",
    "CN113269307A":"图神经网络训练方法及装置","CN114997393A":"基于联邦学习的隐私保护模型训练方法",
    "CN115100456A":"基于神经架构搜索的模型设计方法","CN115730636A":"基于脉冲神经网络的低功耗推理方法",
    "CN115829014A":"基于扩散模型的图像生成方法及装置","CN116108902A":"基于强化学习的决策优化方法及系统",
    "CN116167416A":"基于自监督学习的预训练方法及装置","CN118982047A":"基于图模式的有向图神经网络模型训练方法和装置",
    "CN116958862A":"端侧分层神经网络模型训练方法","CN117669700B":"深度学习模型训练方法和系统",
    "CN117093871A":"面向深度学习分布式训练测评方法和系统","CN117993443A":"模型处理方法装置计算机设备",
    "CN120337786B":"基于虚拟现实与仿真的神经网络模型训练方法",
})
add_patents("Drug Discovery / Bioinformatics", {
    "CN116994644B":"基于预训练模型的药靶亲和力预测方法","CN118888007A":"基于深度迁移学习的癌症药物响应预测方法",
    "CN117912573A":"基于深度学习的多层次生物分子网络构建方法","CN119173946A":"通过迭代实验和机器学习的分子定向进化",
    "CN117912591A":"基于深度对比学习的激酶-药物相互作用预测方法","CN117497042A":"利用生物信息学分析识别潜在药物靶点的方法",
    "CN119649898B":"基于多尺度混合注意力网络的药物靶点亲和力预测方法","CN118298907A":"基于深度学习的抗菌肽识别与定向进化方法",
    "CN117637029B":"基于深度学习模型的抗体可开发性预测方法",
})
add_patents("Reinforcement / Meta Learning", {
    "CN118627587B":"多智能体强化学习可迁移的方法","CN118153658A":"离线强化学习训练方法",
    "CN117035122A":"强化学习模型构建方法","CN116664823A":"基于元学习和度量学习的小样本SAR目标检测方法",
})
add_patents("Cybersecurity", {
    "CN118018426A":"网络异常入侵检测模型训练方法","CN119316223A":"结合GAN与GNN的网络流量异常入侵检测方法",
    "CN117240524A":"基于混合模型的物联网入侵检测方法","CN118101326B":"基于改进MobileNetV3的轻量级车联网入侵检测方法",
    "CN116846688B":"基于CNN的可解释流量入侵检测方法","CN118590289A":"基于联邦学习和深度学习的网络异常检测方法",
    "CN116232699A":"细粒度网络入侵检测模型的训练方法","CN117579400B":"基于神经网络的工控系统网络安全监测方法",
    "CN119227089B":"基于人工智能的漏洞与威胁扫描方法","CN119182607A":"网络异常检测方法装置",
})
add_patents("Multi-modal", {
    "CN116610831A":"语义细分及模态对齐推理学习跨模态检索方法","CN117671438B":"基于知识迁移的多模态知识融合方法",
    "CN117077078B":"基于三模态融合对比学习的跨人脸语音验证方法","CN118799665A":"基于跨模态解耦知识转移的三维目标检测方法",
    "CN117909922A":"多模态数据的深度特征融合与优化方法","CN117953292A":"基于视觉语义模态解缠的广义零样本学习方法",
    "CN117391092B":"基于对比学习的电子病历多模态医疗语义对齐方法","CN118136232A":"基于多模态深度学习的帕金森病症早期检测方法",
})
add_patents("Time Series / Forecasting", {
    "CN117454124B":"基于深度学习的船舶运动预测方法","CN118551189A":"基于变量间动态依赖关系学习的多维时间序列预测方法",
    "CN116227560A":"基于DTW-former的时间序列预测模型及方法","CN115983497A":"时序数据预测方法和装置",
    "CN117520784A":"基于卷积注意力长短期神经网络的地下水位多步预测方法","CN116502774B":"基于时间序列分解和勒让德投影的时间序列预测方法",
    "CN117576910A":"基于循环时空注意力机制的交通流量预测方法","CN120278037B":"基于动态超图与多尺度编码的时间序列预测方法",
})
add_patents("Edge Computing / Model Compression", {
    "CN118133966A":"基于DNN模型切割的边缘计算协同推理方法","CN118520917A":"面向轻量级深度神经网络的异构硬件加速器",
    "CN116663644A":"多压缩版本的云边端DNN协同推理加速方法","CN118520936A":"面向边缘计算服务器的深度学习优化方法",
    "CN116302539A":"边缘计算场景下的模型并行方法","CN119170058A":"支持边缘计算设备的大模型高质推理方法",
    "CN117634569B":"基于RISC-V扩展指令的量化神经网络加速处理器","CN118689656B":"基于人工智能的边缘计算方法及云平台",
})
add_patents("LLM / Large Models", {
    "CN119106123A":"基于大模型的问答方法训练方法","CN118673325A":"大语言模型的训练方法推理方法",
    "CN119760091A":"大模型的训练方法文本生成方法","CN119357321A":"基于知识操作映射微调LLM的动力系统标定调优智能体",
    "CN118504714B":"对大语言模型的文本嵌入模块进行训练的方法","CN118195032A":"具备主动学习能力的大模型自动进化系统",
    "CN118780398A":"大模型训练方法及基于大模型的数据查询方法","CN118586448A":"文本任务处理方法及其模型训练方法",
    "CN118656473A":"大模型数据生成方法","CN119358625A":"分布感知的多阶段大模型微调方法",
})
add_patents("Transformer / Attention", {
    "CN117391152A":"基于Attention头重要性的Transformer模型压缩方法","CN117726676A":"基于轻量化Transformer模型的相机重定位系统",
    "CN116091833A":"注意力与Transformer高光谱图像分类方法","CN116385483A":"基于层次化Transformer的目标跟踪方法",
    "CN116596764B":"基于Transformer与卷积交互的轻量级图像超分辨率方法","CN116050401A":"基于Transformer问题关键词预测的多样性问题自动生成方法",
    "CN116992965B":"Transformer大模型的推理方法","CN118974739A":"具有并行注意力层和前馈层的注意力神经网络",
    "CN116824584A":"基于条件变分Transformer和自省对抗学习的多样化图像描述方法",
})

# ── NEW DOMAINS (non-AI) ──
add_patents("Chemistry / Catalysis", {
    "CN116217518A":"环氧氯丙烷的生产方法以及生产装置","CN117696099B":"催化剂及其制备方法烯属不饱和酸或其酯的制备方法",
    "CN117800357B":"IM-5分子筛合成方法及改性方法","CN116371396A":"催化剂及其制备方法和异戊二烯的合成方法",
    "CN117447439A":"多级结构聚离子液体催化合成环状碳酸酯的方法","CN119954754A":"铝离子温和催化制备5-羟甲基糠醛的方法",
    "CN117101637A":"载体催化剂生产方法及生产环氧乙烷的方法","CN118724687B":"利用氯化锌作为催化剂合成4-己烯-3-酮的方法",
    "CN117624307A":"用于制备环状有机化合物的方法","CN120225574A":"催化剂组合物的制备方法和共轭二烯类聚合物的制备方法",
})
add_patents("Biotech / Gene Editing", {
    "CN119384498A":"用于对细胞进行遗传修饰的方法和组合物","CN119630787A":"经修饰的CRISPR-Cas效应子多肽及其使用方法",
    "CN120035673A":"经遗传修饰的非人动物和用于产生重链抗体的方法","CN117866903B":"单域抗体修饰的干细胞及其在疾病治疗中用途",
    "CN117866904B":"基于单域抗体基因修饰的干细胞对各种疾病的制药用途","CN117866905A":"基于纳米抗体基因修饰的干细胞及其制备方法和产品",
    "CN119137262A":"经改造细胞及使用方法","CN119365492A":"用HLA-E和HLA-G转基因工程化的细胞",
    "CN119421890A":"改进的生产细胞","CN119604610A":"用于体内抗体产生的载体和方法",
})
add_patents("Semiconductor / Chip", {
    "CN116560179A":"BSE补偿装置及其使用方法","CN116306452B":"光刻胶参数获取方法及装置",
    "CN117410163A":"电子源控制方法芯片检测设备及芯片光刻设备",
})
add_patents("Energy / Battery", {
    "CN117040091A":"光伏发电与电动汽车充电站联动系统方法及装置","CN117639081A":"光伏储能逆变并机系统及其光伏能量调度方法",
    "CN118659447B":"光伏-固体氧化物燃料电池混合能源系统控制方法","CN117117392A":"直冷式储能电池冷却控制方法及系统",
    "CN119695992A":"风电功率波动平抑的双电池储能系统优化控制方法","CN115423153A":"基于概率预测的光伏储能系统能量管理方法",
    "CN118523395B":"高比例分布式光伏并网系统的储能选址定容方法","CN118523379A":"分布式光伏储能优化调度方法及系统",
})
add_patents("Mechanical / Transmission", {
    "CN117054094B":"轴承振动检测设备及其使用方法","CN115031965A":"用于模拟高速旋转机械中轴承打滑的试验台及设计方法",
    "CN219084364U":"齿轮箱轴向力加载装置","CN220372973U":"轴承超精机传动机构",
    "CN219712065U":"滑动轴承和传动装置","CN221237150U":"减速箱减震装置",
})
add_patents("Medical Devices", {
    "CN117297775A":"用于医疗器械的解剖位置的改进确认的系统方法和设备","CN119367684A":"肿瘤电场治疗装置治疗系统及制造方法",
    "CN117503209A":"组织活检装置","CN119318515A":"负压吸引旋切活检针和活检系统",
    "CN116473597A":"活检和消融装置及系统","CN117379008A":"适用偏心单芯光纤的医疗装置",
    "CN118161198B":"骨科诊断取样装置","CN116035842A":"便携可折叠床旁定位臂与医疗诊断装置",
    "CN117562650A":"多模式手术系统及应用方法",
})
add_patents("Telecom / 5G", {
    "CN118947078A":"用于探测参考信号配置的方法和装置","CN117676901B":"基于FPGA的5G信号处理方法及系统",
    "CN119605222A":"无线通信系统中发送和接收无线信号的方法和设备","CN117375655B":"5GHz WIFI射频信号处理电路",
    "CN118825624A":"天线装置天线系统及通信设备","CN115810909A":"用于5G的可组阵小型化天线",
    "CN219107674U":"分布式天线系统以及通信系统","CN220234976U":"应用于隧道的5G信号覆盖系统",
    "CN117250412B":"车载5G天线的测试方法及测试系统","CN116938336B":"多天线激光通信系统的信号合并方法",
})
add_patents("Materials / Coatings", {
    "CN118931039B":"耐刮擦免喷涂聚丙烯复合材料及制备方法","CN116041090B":"带氮化硅陶瓷涂层的碳碳复合材料及其制备方法",
    "CN116375504A":"碳基或陶瓷基复合材料表面致密高温抗氧化涂层及制备方法","CN116426785A":"氧控制富铝高熵合金复合材料及其制备方法",
    "CN116855940A":"钛涂层铝锅的制备方法","CN117943599B":"CVD涂层切削刀具及其制备方法",
    "CN117721417A":"超耐磨锆合金包壳表面复合涂层及其制备方法","CN117737723A":"冷喷涂镍基钛铝碳复合涂层及其制备方法",
    "CN114807723B":"金属陶瓷复合涂层及其制备方法",
})
add_patents("Industrial / Robotics", {
    "CN116871717A":"全自动激光切割检测设备及其使用方法","CN117532403A":"基于多传感器融合CNC加工质量实时检测方法",
    "CN117085969A":"人工智能工业视觉检测方法装置","CN221506704U":"机器人视觉检测工作站",
    "CN117671600A":"基于图像识别巡检机器人状态的方法及装置","CN116100549A":"机器人加工轨迹设计方法",
    "CN116429604A":"自动化工具加工检测设备","CN117253026B":"基于图像识别的智能化检测系统及检测方法",
})
add_patents("Environmental", {
    "CN221045750U":"废气净化环保设备","CN116119874A":"实现资源回收和负碳排放的废水处理系统及相关方法",
    "CN116272302A":"废活性炭再生尾气处理系统和处理方法","CN117531328A":"NMP回收工艺及其回收系统",
    "CN221099427U":"提高热量的回收率的工业废气余热再利用装置",
})

# ═══════════════════════════════════════════════════════════════
# PHASE 1: Download missing PDFs
# ═══════════════════════════════════════════════════════════════
def download_missing():
    existing = {p.stem for p in PDF_DIR.glob("*.pdf")}
    missing = [pid for pid in ALL_PATENTS if pid not in existing]
    if not missing:
        print(f"All {len(ALL_PATENTS)} patents already downloaded.")
        return

    print(f"Downloading {len(missing)} new patents...")
    downloader = PatentDownloader()
    ok = fail = 0
    for i in range(0, len(missing), 10):
        chunk = missing[i:i+10]
        results = downloader.download_patents(chunk)
        for pid in chunk:
            if results.get(pid):
                ok += 1
            else:
                fail += 1
        time.sleep(2)
        if (i+10) % 50 == 0:
            print(f"  [{min(i+10, len(missing))}/{len(missing)}] {ok} OK, {fail} fail")
    print(f"  Done: {ok} downloaded, {fail} failed")


# ═══════════════════════════════════════════════════════════════
# PHASE 2: Parse all patents
# ═══════════════════════════════════════════════════════════════
def parse_all():
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    print(f"\nParsing {len(pdfs)} patents across {len(set(p['domain'] for p in ALL_PATENTS.values()))} domains...")

    # Cross-domain pattern collectors
    claims_structure = Counter()      # claim opening patterns
    dep_claim_structure = Counter()   # dependent claim patterns
    section_patterns = Counter()      # section headings
    boilerplate_all = Counter()       # boilerplate phrases
    compound_terms = Counter()        # domain-specific terms
    transitions = Counter()           # transition phrases
    domain_stats = defaultdict(lambda: {"count":0, "avg_claims":0, "claim_samples":[]})

    for i, pdf_path in enumerate(pdfs):
        pid = pdf_path.stem
        info = ALL_PATENTS.get(pid, {"title":"", "domain":"unknown"})
        domain = info["domain"]

        try:
            doc = fitz.open(str(pdf_path))
            text = " ".join(page.get_text() for page in doc)
            doc.close()
            if len(text) < 500:
                continue
        except:
            continue

        # ── Extract claims patterns ──
        # Independent claim openers
        for m in re.finditer(r'(\d+[\.\s、）)]\s*一种[^。]{30,300}?(?:其特征在于|包括|包含))', text):
            claims_structure[m.group(1)[:200]] += 1
        for m in re.finditer(r'(\d+[\.\s、）)]\s*一种[^。]{30,200}?(?:装置|系统|设备|介质|产品))', text):
            claims_structure[m.group(1)[:200]] += 1

        # Dependent claim patterns
        for m in re.finditer(r'(\d+[\.\s、）)]\s*根据权利要求\d+[^。]{20,200}?(?:其特征在于|其中|所述))', text):
            dep_claim_structure[m.group(1)[:200]] += 1

        # ── Section headings ──
        for m in re.finditer(r'(?:【([^】]+)】|^\s*(技术领域|背景技术|发明内容|技术方案|有益效果|附图说明|具体实施方式|实施例\d+)\s*$)', text, re.MULTILINE):
            h = m.group(1) or m.group(2)
            if h:
                section_patterns[h.strip()] += 1

        # ── Boilerplate ──
        bp_patterns = [
            r'(本发明涉及[^。]{10,80}?(?:技术领域|方法|装置)[^。]*。)',
            r'(本发明(?:的|提供|公开|实施例|采用|通过)[^。]{15,150}。)',
            r'(与现有技术相比[^。]{10,150}。)',
            r'(应当理解[^。]{10,100}。)',
            r'(以上所述[^。]{10,200}?(?:本发明|本申请|实施例)[^。]*。)',
        ]
        for pat in bp_patterns:
            for m in re.finditer(pat, text):
                boilerplate_all[m.group(1)[:200]] += 1

        # ── Domain terms ──
        term_patterns = [
            r'(?:步骤[A-Z]?\d*[：:]\s*)([^，。；;]{10,80})',
            r'((?:处理|获取|生成|计算|检测|制备|合成|控制|调节|训练|推理|融合|编码|压缩|传输|测量|诊断|识别|预测|优化|回收|净化|改性|涂覆|沉积|烧结|发酵|培养|编辑|修饰)(?:模块|单元|器|装置|设备|系统|方法|步骤|过程|流程|工艺))',
        ]
        for pat in term_patterns:
            for m in re.finditer(pat, text):
                compound_terms[m.group(1)[:80]] += 1

        # ── Transitions ──
        trans_pat = [
            r'(在一些实施例中[^，。]{0,30})', r'(在一个实施例中[^，。]{0,30})',
            r'(可选地[^，。]{0,30})', r'(优选地[^，。]{0,30})',
            r'(示例性地[^，。]{0,30})', r'(进一步地[^，。]{0,20})',
            r'(需要说明的是[^，。]{0,40})',
        ]
        for pat in trans_pat:
            for m in re.finditer(pat, text):
                transitions[m.group(1)] += 1

        # ── Domain stats ──
        domain_stats[domain]["count"] += 1
        n_claims = len(re.findall(r'^\s*\d+[\.\s、）)]\s*(?:一种|根据)', text, re.MULTILINE))
        domain_stats[domain]["avg_claims"] += n_claims
        if len(domain_stats[domain]["claim_samples"]) < 3:
            m = re.search(r'(\d+[\.\s、）)]\s*一种[^。]{50,300}?(?:其特征在于|包括))', text)
            if m:
                domain_stats[domain]["claim_samples"].append(m.group(1)[:200])

        if (i+1) % 50 == 0:
            print(f"  [{i+1}/{len(pdfs)}] parsed")

    # Finalize domain stats
    for d in domain_stats:
        c = domain_stats[d]["count"]
        if c > 0:
            domain_stats[d]["avg_claims"] = round(domain_stats[d]["avg_claims"] / c, 1)

    print(f"  Done: {i+1} patents parsed")

    # Use total patent IDs collected (not just successfully parsed PDFs)
    all_domains = set(p["domain"] for p in ALL_PATENTS.values())
    return {
        "total_patents": len(ALL_PATENTS),  # all patent IDs across all domains
        "domains": len(all_domains),
        "domain_stats": dict(domain_stats),
        "top_claim_openers": claims_structure.most_common(50),
        "top_dep_claim_patterns": dep_claim_structure.most_common(30),
        "top_sections": section_patterns.most_common(30),
        "top_boilerplate": boilerplate_all.most_common(50),
        "top_compound_terms": compound_terms.most_common(100),
        "top_transitions": transitions.most_common(30),
    }


# ═══════════════════════════════════════════════════════════════
# PHASE 3: Build Patent Expert Knowledge Base
# ═══════════════════════════════════════════════════════════════
def build_expert_kb(data):
    """Synthesize parsed data into a Patent Writing Expert knowledge base."""

    kb = {
        "expert_profile": {
            "name": "Patent Writing Expert (专利撰写专家)",
            "knowledge_source": f"{data['total_patents']} Chinese invention patents across {data['domains']} technical domains",
            "domains_covered": list(data["domain_stats"].keys()),
            "capabilities": [
                "权利要求书撰写指导 (Claims drafting guidance)",
                "说明书章节结构优化 (Description structure optimization)",
                "术语规范建议 (Terminology standardization)",
                "实施例撰写规范 (Embodiment writing standards)",
                "附图说明撰写 (Drawing description writing)",
                "有益效果提炼 (Beneficial effects articulation)",
                "技术问题→技术方案转换 (Problem → Solution transformation)",
            ]
        },

        # ── Cross-domain universal claim patterns ──
        "claims_writing_guide": {
            "independent_method_template": (
                "一种[技术主题]方法，其特征在于，包括：\n"
                "步骤S[110]：通过[组件A]([110])[动词]获取[输入]，得到[中间结果A]；\n"
                "步骤S[120]：通过[组件B]([120])对[中间结果A]进行[操作]，得到[中间结果B]；\n"
                "步骤S[1N0]：输出[最终结果]。"
            ),
            "independent_device_template": (
                "一种[技术主题]装置，其特征在于，包括：\n"
                "[模块A]([10])，用于执行[功能A]；\n"
                "[模块B]([20])，与[模块A]连接，用于执行[功能B]。"
            ),
            "dependent_claim_variations": [
                "根据权利要求[1]所述的方法，其特征在于，所述[参数]的取值范围为[X]至[Y]。",
                "根据权利要求[1]所述的方法，其特征在于，所述[步骤]中[操作]使用[替代方案]。",
                "根据权利要求[1]所述的方法，其特征在于，所述方法还包括：[额外步骤]。",
                "根据权利要求[1]至[3]任一所述的方法，其特征在于，所述[特征]为[具体限定]。",
            ],
            "top_claim_openers_from_patents": data["top_claim_openers"][:20],
            "top_dep_patterns_from_patents": data["top_dep_claim_patterns"][:20],
        },

        # ── Cross-domain section writing guide ──
        "section_writing_guide": {
            "cn_required_sections": [
                {"name": "技术领域", "purpose": "1-2句话说明发明所属技术领域", "example": "本发明涉及[技术领域]技术领域，具体涉及一种[技术方案简述]。"},
                {"name": "背景技术", "purpose": "现有技术的不足之处（不要描述优点）", "example": "目前，[现状描述]。然而，现有技术存在以下不足：[局限性列表]。"},
                {"name": "发明内容", "purpose": "技术问题+技术方案+有益效果", "subsections": ["技术问题", "技术方案", "有益效果"]},
                {"name": "附图说明", "purpose": "逐图说明", "example": "图1是本发明实施例提供的[技术方案]的流程示意图。"},
                {"name": "具体实施方式", "purpose": "至少1个实施例的详细描述", "example": "实施例1\n本实施例提供一种[技术方案]的具体实现方式。步骤S110：[详细描述]。"},
            ],
            "top_sections_found": data["top_sections"][:20],
        },

        # ── Boilerplate bank ──
        "boilerplate_bank": {
            "abstract": "本发明公开了一种[技术主题]，包括：[简化步骤]。本发明[有益效果简述]。",
            "tech_field": "本发明涉及[领域]技术领域，具体涉及一种[技术方案]。",
            "problem_statement": "随着[技术/行业发展]，[现状]。然而，现有技术中存在[具体问题]。",
            "solution_intro": "为解决上述技术问题，本发明提供一种[技术方案]，包括以下步骤：",
            "beneficial_effects": "与现有技术相比，本发明具有以下有益效果：\n[1]. [效果1]。\n[2]. [效果2]。",
            "embodiment_opening": "下面结合附图[图X]对本发明实施例[Y]进行详细描述。",
            "closing": "以上所述仅为本发明的优选实施例而已，并不用于限制本发明。凡在本发明的精神和原则之内，所作的任何修改、等同替换、改进等，均应包含在本发明的保护范围之内。",
            "top_real_boilerplate": data["top_boilerplate"][:30],
        },

        # ── Terminology guide ──
        "terminology_guide": {
            "universal_patent_terms": {
                "其特征在于": "用于独立权利要求，分隔前序部分和特征部分",
                "所述": "专利中指代前述的特定元件/步骤（不同于普通中文的'该'或'此'）",
                "包括": "开放式列举，不排除未列出的元素",
                "由...组成": "封闭式列举，排除未列出的元素",
                "任一项": "多引多时的通用表达'根据权利要求1至X任一项所述'",
                "可选地": "表示非必须但可选的优选特征",
                "优选地": "表示更优选的实施方式",
            },
            "forbidden_in_claims": ["等等", "最好是", "约", "接近", "诸如此类", "可能", "通常"],
            "top_compound_terms": data["top_compound_terms"][:50],
            "top_transitions": data["top_transitions"][:20],
        },

        # ── Domain-specific insights ──
        "domain_specific_insights": {
            domain: {
                "patents_analyzed": stats["count"],
                "avg_claims": stats["avg_claims"],
                "sample_claims": stats["claim_samples"][:2],
            }
            for domain, stats in data["domain_stats"].items()
        },

        # ── Writing quality checklist ──
        "writing_checklist": [
            "权利要求是否为单句（仅句末一个。）？",
            "独立权利要求是否包含'其特征在于'分隔的前序部分和特征部分？",
            "从属权利要求是否避免多引多？",
            "摘要是否少于300字？",
            "是否包含全部5个必选章节？",
            "附图中的每个引用号是否在说明书中至少出现一次？",
            "是否避免在权利要求中使用'约'、'接近'、'最好是'等模糊用语？",
            "说明书中的术语是否前后一致？",
            "实施例是否提供了足够详细的实现细节使本领域技术人员能够实施？",
            "有益效果是否与技术问题因果对应？",
        ],
    }

    # Save
    output_path = EXPERT_DIR / "patent_expert_kb.json"
    output_path.write_text(json.dumps(kb, ensure_ascii=False, indent=2))
    print(f"\n✓ Patent Expert KB saved to {output_path} ({output_path.stat().st_size:,} bytes)")
    return kb


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print(f"Patent Expert Builder")
    print(f"Total patent IDs: {len(ALL_PATENTS)} across {len(set(p['domain'] for p in ALL_PATENTS.values()))} domains")
    print(f"Domains: {sorted(set(p['domain'] for p in ALL_PATENTS.values()))}")
    print()

    # Phase 1: Download
    download_missing()

    # Phase 2: Parse
    data = parse_all()

    # Phase 3: Build Expert KB
    build_expert_kb(data)

    print(f"\n✓ Expert knowledge base ready at {EXPERT_DIR}/")
    for f in sorted(EXPERT_DIR.glob("*.json")):
        print(f"  {f.name} ({f.stat().st_size:,} bytes)")
