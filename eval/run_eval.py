import json
import time
from pathlib import Path
from typing import List, Dict, Any

from src.graph import run_self_healing_rag
from src.eval.baseline import BaselineRAG
from src.eval.metrics import (
    calculate_recall_at_k,
    calculate_precision_at_k,
    calculate_mrr,
    calculate_percentiles,
    estimate_cost
)

def run_evaluation(num_samples: int = 100):
    eval_dir = Path(__file__).resolve().parent
    dataset_path = eval_dir / "eval_dataset.json"
    
    if not dataset_path.exists():
        # Fallback to golden_qa.json if dataset not found
        dataset_path = eval_dir / "golden_qa.json"

    with open(dataset_path, "r", encoding="utf-8") as f:
        qa_pairs = json.load(f)[:num_samples]

    print("==================================================================================")
    print("        SCIENTIFIC EVALUATION BENCHMARK: BASELINE VS SELF-HEALING RAG             ")
    print("==================================================================================")
    print(f"Total Test Cases Evaluated: {len(qa_pairs)}\n")

    baseline_rag = BaselineRAG()

    sh_latencies = []
    base_latencies = []
    
    sh_recalls = []
    base_recalls = []
    sh_mrrs = []
    base_mrrs = []

    sh_grounded_count = 0
    sh_fallback_count = 0
    sh_retries_count = 0
    sh_recovered_count = 0
    sh_pass_count = 0

    base_pass_count = 0

    unanswerable_triggers = ["don't have enough information", "do not have enough information", "not mentioned"]

    print(f"{'ID':<3} | {'Category':<22} | {'Base Lat':<8} | {'SH Lat':<8} | {'Retries':<7} | {'SH Verdict':<10} | {'Status':<6}")
    print("-" * 85)

    for item in qa_pairs:
        qid = item["id"]
        category = item.get("category", "General")[:22]
        question = item["question"]
        expected_sources = item.get("expected_sources", [])
        expected_behavior = item.get("expected_behavior", "answer")

        # --- 1. Baseline Linear RAG Run ---
        base_res = baseline_rag.run(question)
        base_lat = base_res["latency_ms"]
        base_latencies.append(base_lat)

        base_sources = [c["source"] for c in base_res["citations"]]
        base_rec = calculate_recall_at_k(base_sources, expected_sources)
        base_mrr = calculate_mrr(base_sources, expected_sources)
        base_recalls.append(base_rec)
        base_mrrs.append(base_mrr)

        base_ans = base_res["final_response"]
        base_fallback = any(t in base_ans.lower() for t in unanswerable_triggers)
        if expected_behavior == "answer":
            base_pass = not base_fallback
        else:
            base_pass = base_fallback
        if base_pass:
            base_pass_count += 1

        # --- 2. Self-Healing Cyclic RAG Run ---
        sh_res = run_self_healing_rag(question=question, max_retries=2, use_cache=False)
        sh_lat = sh_res.get("trace_info", {}).get("latency_ms", {}).get("total_ms", 0.0)
        sh_latencies.append(sh_lat)

        sh_sources = [c["source"] for c in sh_res.get("citations", [])]
        sh_rec = calculate_recall_at_k(sh_sources, expected_sources)
        sh_mrr = calculate_mrr(sh_sources, expected_sources)
        sh_recalls.append(sh_rec)
        sh_mrrs.append(sh_mrr)

        sh_ans = sh_res.get("final_response", "")
        sh_grounded = bool(sh_res.get("critique_grounded", False))
        sh_retries = int(sh_res.get("retry_count", 0))
        sh_retries_count += sh_retries
        sh_is_fallback = any(t in sh_ans.lower() for t in unanswerable_triggers) or (not sh_grounded)

        if sh_grounded:
            sh_grounded_count += 1
        if sh_is_fallback:
            sh_fallback_count += 1
        if sh_retries > 0 and sh_grounded and not sh_is_fallback:
            sh_recovered_count += 1

        if expected_behavior == "answer":
            sh_pass = sh_grounded and not sh_is_fallback
        else:
            sh_pass = sh_is_fallback

        if sh_pass:
            sh_pass_count += 1
            status_str = "PASS ✅"
        else:
            status_str = "FAIL ❌"

        verdict_str = "Grounded" if sh_grounded and not sh_is_fallback else "Fallback"
        print(f"{qid:<3} | {category:<22} | {base_lat:<8.0f} | {sh_lat:<8.0f} | {sh_retries:<7} | {verdict_str:<10} | {status_str:<6}")

    # Calculate Aggregates
    sh_lat_stats = calculate_percentiles(sh_latencies)
    base_lat_stats = calculate_percentiles(base_latencies)

    print("-" * 85)
    print("\n==================================================================================")
    print("                      COMPARATIVE EVALUATION SUMMARY                              ")
    print("==================================================================================")
    print(f"{'METRIC':<30} | {'BASELINE RAG':<20} | {'SELF-HEALING RAG':<20}")
    print("-" * 75)
    print(f"{'Overall Pass Rate':<30} | {base_pass_count/len(qa_pairs)*100:<19.1f}% | {sh_pass_count/len(qa_pairs)*100:<19.1f}%")
    print(f"{'Recall@4':<30} | {np.mean(base_recalls):<20.3f} | {np.mean(sh_recalls):<20.3f}")
    print(f"{'MRR (Mean Reciprocal Rank)':<30} | {np.mean(base_mrrs):<20.3f} | {np.mean(sh_mrrs):<20.3f}")
    print(f"{'Grounding / Accuracy Rate':<30} | {base_pass_count/len(qa_pairs)*100:<19.1f}% | {sh_grounded_count/len(qa_pairs)*100:<19.1f}%")
    print(f"{'Fallback Rate':<30} | {(len(qa_pairs)-base_pass_count)/len(qa_pairs)*100:<19.1f}% | {sh_fallback_count/len(qa_pairs)*100:<19.1f}%")
    print(f"{'Average Retries per Query':<30} | {'0.00':<20} | {sh_retries_count/len(qa_pairs):<20.2f}")
    print(f"{'Self-Healing Recovery Count':<30} | {'N/A':<20} | {sh_recovered_count:<20}")
    print(f"{'p50 Latency (ms)':<30} | {base_lat_stats['p50']:<20.1f} | {sh_lat_stats['p50']:<20.1f}")
    print(f"{'p95 Latency (ms)':<30} | {base_lat_stats['p95']:<20.1f} | {sh_lat_stats['p95']:<20.1f}")
    print(f"{'Average Latency (ms)':<30} | {base_lat_stats['avg']:<20.1f} | {sh_lat_stats['avg']:<20.1f}")
    print("==================================================================================\n")

if __name__ == "__main__":
    run_evaluation(num_samples=20)  # Default runs 20 samples for quick validation; pass 100 for full set
