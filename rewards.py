import argparse
import glob
import json
import re
import subprocess
from pathlib import Path
from typing import Dict, Optional, List, Tuple

# ====== 解析與過濾 ======
ANSI_RE = re.compile(r"\x1B\[[0-9;]*[A-Za-z]")

ADDRESS_RE    = re.compile(r"^\s*Address\s+([A-Za-z0-9]+)", re.MULTILINE)
ORE_RE        = re.compile(r"^\s*Balance\s+([0-9.]+)\s+ORE\b", re.MULTILINE)
SOL_RE        = re.compile(r"^\s*SOL\s+([0-9.]+)\s+SOL\b", re.MULTILINE)
NOT_FOUND_RE  = re.compile(r"Not\s+found", re.IGNORECASE)

def strip_ansi(s: Optional[str]) -> str:
    if not isinstance(s, str):
        return ""
    return ANSI_RE.sub("", s)

def to_float(x: Optional[str]) -> float:
    try:
        return float(x) if x is not None else 0.0
    except ValueError:
        return 0.0

# ====== 調用 ore.exe ======
def run_account(keypair: str, timeout: int = 30) -> subprocess.CompletedProcess:
    # ore.exe 走 PATH，不指定絕對路徑；強制 utf-8、忽略無法解碼字元，避免 Windows CP950 問題
    return subprocess.run(
        ["ore.exe", "account", "--keypair", keypair],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=timeout
    )

def parse_account_output(output: Optional[str]) -> Dict[str, Optional[str]]:
    clean = strip_ansi(output)
    addr = None
    ore = None
    sol = None
    note = None

    m = ADDRESS_RE.search(clean)
    if m:
        addr = m.group(1)
    m = ORE_RE.search(clean)
    if m:
        ore = m.group(1)
    m = SOL_RE.search(clean)
    if m:
        sol = m.group(1)
    if NOT_FOUND_RE.search(clean):
        note = "account not found"

    return {"address": addr, "ore": ore, "sol": sol, "note": note}

# ====== 資料列印 ======
def print_table_header():
    print(f"{'文件':<16} {'ORE餘額':>15} {'SOL餘額':>15} {'備註':>16}")
    print("-" * 60)

def print_table_row(name: str, ore: float, sol: float, note: str = ""):
    print(f"{name:<16} {ore:>15.9f} {sol:>15.9f} {note:>16}")

# ====== 主流程 ======
def collect_keypairs(default_glob: str, single: Optional[str]) -> List[str]:
    if single:
        return [single]
    paths = glob.glob(default_glob)
    if not paths:
        raise SystemExit(f"找不到任何 keypair：{default_glob}")
    return sorted(paths)

def get_one(keypair: str, timeout: int) -> Dict:
    try:
        proc = run_account(keypair, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {
            "keypair": keypair,
            "address": None,
            "ore_balance": None,
            "sol_balance": None,
            "error": "timeout",
        }

    if proc.returncode != 0:
        return {
            "keypair": keypair,
            "address": None,
            "ore_balance": None,
            "sol_balance": None,
            "error": (proc.stderr or "").strip() or f"exit={proc.returncode}",
        }

    parsed = parse_account_output(proc.stdout)
    out = {
        "keypair": keypair,
        "address": parsed["address"],
        "ore_balance": to_float(parsed["ore"]),
        "sol_balance": to_float(parsed["sol"]),
    }
    if parsed.get("note"):
        out["note"] = parsed["note"]
    return out

def main():
    # 預設：相對於這支腳本所在目錄掃描 .\keypairs\*.json
    base_dir = Path(__file__).resolve().parent
    default_glob = str(base_dir / "keypairs" / "*.json")

    ap = argparse.ArgumentParser(description="Fetch ORE & SOL balances (ore.exe via PATH)")
    ap.add_argument("--keypair", help="單一 keypair json 檔路徑（可選）")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--json", action="store_true", help="以 JSON 輸出結果")
    args = ap.parse_args()

    keypairs = collect_keypairs(default_glob, args.keypair)
    results: List[Dict] = [get_one(kp, args.timeout) for kp in keypairs]

    if args.json:
        print(json.dumps(results if len(results) > 1 else results[0], ensure_ascii=False, indent=2))
        return

    # 表格輸出與合計
    total_ore = 0.0
    total_sol = 0.0
    print_table_header()
    for r in results:
        name = Path(r["keypair"]).name
        ore = float(r["ore_balance"]) if isinstance(r.get("ore_balance"), (int, float)) else 0.0
        sol = float(r["sol_balance"]) if isinstance(r.get("sol_balance"), (int, float)) else 0.0
        note = r.get("note") or r.get("error") or ""
        total_ore += ore
        total_sol += sol
        print_table_row(name, ore, sol, note)

    print("-" * 60)
    print_table_row("合計", total_ore, total_sol, "")

if __name__ == "__main__":
    main()
