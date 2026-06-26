# =============================================================================
# src/chunked_tokenize.py -- batch tokenizer (45s timeout workaround)
# =============================================================================
# Run: python3 src/chunked_tokenize.py --exp exp_B --batch 60
#      python3 src/chunked_tokenize.py --exp exp_B --batch 60  # resumes
# After all rows done:
#      python3 -c "from src.feature_builder import build_features; build_features('exp_B')"

import os, sys, argparse, logging
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.preprocessor import EXPERIMENT_CONFIGS, preprocess_document, get_tagger

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_chunked(exp_id, batch=60):
    if exp_id not in EXPERIMENT_CONFIGS:
        logger.error("Unknown exp_id: %s", exp_id)
        return

    fy_path = config.FIRM_YEAR_DOC_PATH
    if not os.path.exists(fy_path):
        logger.error("firm_year_documents.csv missing")
        return

    docs = pd.read_csv(fy_path, dtype=str)
    out_path = os.path.join(config.PREPROC_DIR, "tokenized_%s.csv" % exp_id)

    # load already-done rcept_nos
    done_set = set()
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        try:
            done_set = set(pd.read_csv(out_path, dtype=str)["rcept_no"].tolist())
        except Exception:
            pass

    remaining = docs[~docs["rcept_no"].isin(done_set)].reset_index(drop=True)
    total = len(docs)
    logger.info("[%s] %d done, %d remaining", exp_id, len(done_set), len(remaining))

    if len(remaining) == 0:
        logger.info("[%s] All rows done.", exp_id)
        return

    to_process = remaining.head(batch)
    logger.info("[%s] Processing %d rows this batch", exp_id, len(to_process))

    cfg = EXPERIMENT_CONFIGS[exp_id]
    try:
        tagger = get_tagger(cfg["tagger_name"])
    except Exception as e:
        logger.error("Tagger init failed: %s", e)
        return

    # load company names
    corp_names = []
    if os.path.exists(config.CORP_CODE_MAP_PATH):
        cm = pd.read_csv(config.CORP_CODE_MAP_PATH, dtype=str)
        corp_names = cm["corp_name"].dropna().tolist()
    logger.info("Company names loaded: %d", len(corp_names))

    new_rows = []
    for i, (_, row) in enumerate(to_process.iterrows()):
        doc_text = str(row.get("document", ""))
        result = preprocess_document(
            text=doc_text, config=cfg,
            tagger=tagger, company_names=corp_names,
        )
        new_rows.append({
            "stock_code":  row["stock_code"],
            "corp_code":   row["corp_code"],
            "rcept_no":    row["rcept_no"],
            "fiscal_year": row["fiscal_year"],
            "esg_year":    row["esg_year"],
            "exp_id":      exp_id,
            "token_count": result["token_count"],
            "joined_text": result["joined_text"],
        })
        if (i + 1) % 10 == 0:
            logger.info("  %d/%d done...", i+1, len(to_process))

    new_df = pd.DataFrame(new_rows)

    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        try:
            existing = pd.read_csv(out_path, dtype=str)
            combined = pd.concat([existing, new_df], ignore_index=True)
        except Exception:
            combined = new_df
    else:
        combined = new_df

    combined.to_csv(out_path, index=False, encoding="utf-8-sig")
    done_count = len(done_set) + len(new_rows)
    logger.info("[%s] Saved: %s (%d/%d)", exp_id, out_path, done_count, total)

    if done_count >= total:
        logger.info("[%s] ALL DONE. Run: build_features('%s')", exp_id, exp_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp",   required=True)
    parser.add_argument("--batch", type=int, default=60)
    args = parser.parse_args()
    run_chunked(args.exp, args.batch)
