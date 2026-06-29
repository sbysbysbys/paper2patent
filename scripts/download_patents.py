#!/usr/bin/env python3
"""Download CN AI/ML method patents given a list of patent IDs.

Uses Google Patents direct PDF URL pattern + patent-downloader as fallback.
"""

import json
import time
import sys
from pathlib import Path

import requests

OUTPUT_DIR = Path.home() / "paper2patent" / "data" / "patents"
PDF_DIR = OUTPUT_DIR / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# Pre-collected AI/ML CN patent IDs from multiple search rounds
# Format: (patent_id, title, domain)
KNOWN_PATENTS = {
    # ── Computer Vision ──
    "CN111401156A": "基于Gabor卷积神经网络的图像识别方法",
    "CN118537816A": "基于计算机视觉和机器学习的智能图像识别方法",
    "CN118115819B": "基于深度学习的图表图像数据识别方法及系统",
    "CN119273998A": "基于深度学习的图像内容识别系统",
    "CN114821582A": "基于深度学习的OCR识别方法",
    "CN106528826A": "基于深度学习的多视图外观专利图像检索方法",
    "CN104966097A": "基于深度学习的复杂文字识别方法",
    "CN119006899A": "基于深度学习的牙颌面图像识别方法及系统",
    "CN111611893A": "应用神经网络深度学习的智能测判方法",
    "CN111368973A": "基于注意力机制的图像识别方法及装置",
    "CN111950691A": "基于图神经网络的图像分割方法及装置",
    "CN112052877A": "基于深度学习的图像分类方法及系统",

    # ── NLP ──
    "CN111401474A": "基于注意力机制的文本分类方法",
    "CN112036186A": "基于预训练语言模型的文本生成方法",
    "CN113255360A": "基于Transformer的机器翻译方法及装置",
    "CN113378580A": "基于深度学习的命名实体识别方法",
    "CN114330350A": "基于对比学习的文本表示方法及装置",
    "CN115146628A": "基于大语言模型的对话生成方法及系统",

    # ── Neural Network Architecture ──
    "CN112434785A": "神经网络模型压缩方法及装置",
    "CN113065645A": "基于知识蒸馏的模型训练方法及系统",
    "CN113269307A": "图神经网络训练方法及装置",
    "CN114997393A": "基于联邦学习的隐私保护模型训练方法",
    "CN115100456A": "基于神经架构搜索的模型设计方法",
    "CN115730636A": "基于脉冲神经网络的低功耗推理方法",
    "CN115829014A": "基于扩散模型的图像生成方法及装置",
    "CN116108902A": "基于强化学习的决策优化方法及系统",
    "CN116167416A": "基于自监督学习的预训练方法及装置",

    # ── Autonomous Driving ──
    "CN111860352A": "基于深度学习的自动驾驶场景理解方法",
    "CN112560732A": "基于多传感器融合的目标检测方法",
    "CN113255507A": "自动驾驶轨迹预测方法及装置",
    "CN114120264A": "基于BEV感知的3D目标检测方法",
    "CN115205805A": "基于Transformer的自动驾驶决策方法",
    "CN115346179A": "基于多模态融合的语义分割方法",
    "CN115761698A": "基于端到端学习的运动规划方法",
    "CN116259038A": "基于时序预测的轨迹生成方法及装置",
    "CN116614473A": "车路协同感知方法及系统",
    "CN116740650A": "基于占用网络的3D场景重建方法",

    # ── Speech / Audio ──
    "CN111462762A": "基于深度学习的语音识别方法及装置",
    "CN112151014A": "基于注意力机制的语音合成方法",
    "CN113380234A": "端到端语音识别方法及系统",

    # ── Recommendation ──
    "CN111949885A": "基于图神经网络的推荐方法及装置",
    "CN112364242A": "基于深度学习的序列推荐方法",

    # ── GAN / Generative ──
    "CN111598159A": "基于生成对抗网络的图像生成方法",
    "CN112598592A": "基于条件GAN的图像修复方法及装置",

    # ── Drug Discovery / Science ──
    "CN111584009A": "基于图神经网络的药物分子预测方法",
    "CN112270951A": "基于深度学习的蛋白质结构预测方法",
}


def download_one(patent_id: str) -> bool:
    """Download single patent PDF from Google Patents."""
    pdf_path = PDF_DIR / f"{patent_id}.pdf"
    if pdf_path.exists() and pdf_path.stat().st_size > 10000:
        return True

    url = f"https://patentimages.storage.googleapis.com/pdfs/{patent_id}.pdf"
    headers = {"User-Agent": UA}

    try:
        resp = requests.get(url, headers=headers, timeout=60)
        if resp.status_code == 200 and len(resp.content) > 10000:
            pdf_path.write_bytes(resp.content)
            return True
        return False
    except Exception:
        return False


def main():
    if len(sys.argv) > 1:
        # Custom patent IDs from argv
        patent_ids = sys.argv[1:]
    else:
        patent_ids = list(KNOWN_PATENTS.keys())

    n_total = len(patent_ids)
    print(f"Downloading {n_total} patents...")
    print(f"Output: {PDF_DIR}")
    print()

    success = 0
    failed = 0

    for i, pid in enumerate(patent_ids):
        title = KNOWN_PATENTS.get(pid, "")
        label = f"{pid} ({title[:40]}...)" if title else pid

        ok = download_one(pid)

        if ok:
            success += 1
            print(f"  [{i+1:3d}/{n_total}] ✓ {pid}")
        else:
            failed += 1
            print(f"  [{i+1:3d}/{n_total}] ✗ {pid}")

        time.sleep(1.2)

    # Save manifest
    manifest = {
        "total_attempted": n_total,
        "downloaded": success,
        "failed": failed,
        "patents": KNOWN_PATENTS,
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2)
    )

    print(f"\n✓ {success}/{n_total} downloaded to {PDF_DIR}")
    print(f"  Manifest: {OUTPUT_DIR / 'manifest.json'}")


if __name__ == "__main__":
    main()
