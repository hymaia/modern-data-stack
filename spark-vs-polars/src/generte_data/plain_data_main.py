"""
DynamoDB Single-Table Design — Bulk JSON Generator

Stack  : Faker (données réalistes) + orjson (sérialisation rapide)
Output : JSON newline-delimited (ndjson) ou JSON array, partitionné par jour

Usage:
    pip install faker orjson tqdm
    python generate_dynamo_dump.py --rows 1_000_000 --start 2024-01-01 --end 2024-12-31
    python generate_dynamo_dump.py --rows 5_000_000 --format ndjson --seed 42
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import orjson
from faker import Faker
from tqdm import tqdm

# ── Constantes ────────────────────────────────────────────────────────────────

CHUNK_SIZE = 50_000

# ── Faker setup ───────────────────────────────────────────────────────────────

fake = Faker(["fr_FR", "en_US", "de_DE", "es_ES"])
Faker.seed(0)  # écrasé si --seed est fourni


# ── Helpers ───────────────────────────────────────────────────────────────────

def _uid() -> str:
    return fake.uuid4()[:12].replace("-", "")


def _dt_on(d: date) -> str:
    """Datetime ISO sur la journée d (heure aléatoire)."""
    h = random.randint(0, 23)
    m = random.randint(0, 59)
    s = random.randint(0, 59)
    return datetime(d.year, d.month, d.day, h, m, s).isoformat() + "Z"


# ── Génération par chunk ──────────────────────────────────────────────────────

def make_data(event_date: date) -> dict:
    oid     = _uid()
    uid     = _uid()
    n_items = random.randint(1, 8)
    placed = _dt_on(event_date)
    return {
        "uid":             uid,
        "entity_type":     "ORDER",
        "order_id":        oid,
        "user_id":         uid,
        "placed_at":       placed,
        "updated_at":      placed,
        "delivered_at":    _dt_on(event_date + timedelta(days=random.randint(1, 7))),
        "item_count":      n_items,
        "cancellation_reason": random.choice(["out_of_stock", "user_request", "fraud", "payment_failed"])
    }

def generate_chunk(n: int, event_date: date) -> list[dict]:
    """Génère n items avec répartition pondérée par type d'entité."""
    return [make_data(event_date) for _ in range(n)]


# ── Writers ───────────────────────────────────────────────────────────────────

def write_ndjson(records: list[dict], path: Path) -> None:
    """JSON newline-delimited — idéal pour Athena / Spark / DuckDB."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        for rec in records:
            f.write(orjson.dumps(rec) + b"\n")

# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="DynamoDB single-table bulk JSON generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--rows",   type=int, default=1_000_000, help="Nombre total d'items à générer")
    p.add_argument("--start",  type=str, default="2024-01-01", help="Date de début YYYY-MM-DD")
    p.add_argument("--end",    type=str, default="2024-12-31", help="Date de fin YYYY-MM-DD")
    p.add_argument("--output", type=str, default="output",    help="Dossier de sortie")
    p.add_argument("--format", type=str, default="ndjson", choices=["ndjson", "json"],
                   help="Format de sortie : ndjson (recommandé) ou json array")
    p.add_argument("--seed",   type=int, default=None, help="Seed pour la reproductibilité")
    p.add_argument("--chunk",  type=int, default=CHUNK_SIZE, help="Taille des batchs mémoire")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # Seed
    if args.seed is not None:
        random.seed(args.seed)
        Faker.seed(args.seed)

    # Dates
    start  = date.fromisoformat(args.start)
    end    = date.fromisoformat(args.end)
    if start > end:
        sys.exit("Erreur : --start doit être <= --end")

    days   = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    n_days = len(days)
    output = Path(args.output)
    writer = write_ndjson
    ext    = "ndjson"
    chunk  = args.chunk

    rows_per_day  = max(1, math.ceil(args.rows / n_days))
    total_written = 0

    print(f"\nDynamoDB bulk generator")
    print(f"  items    : {args.rows:,}")
    print(f"  période  : {args.start} → {args.end}  ({n_days} jours)")
    print(f"  format   : {args.format}")
    print(f"  sortie   : {output}/")
    print()

    with tqdm(total=args.rows, unit="items", unit_scale=True, dynamic_ncols=True) as pbar:
        for day in days:
            remaining = args.rows - total_written
            if remaining <= 0:
                break
            n_today = min(rows_per_day, remaining)

            # Génération par sous-chunks pour limiter la pression mémoire
            records: list[dict] = []
            for start_i in range(0, n_today, chunk):
                batch_n = min(chunk, n_today - start_i)
                records.extend(generate_chunk(batch_n, day))

            path = output / f"dt={day.isoformat()}" / f"data.{ext}"
            writer(records, path)

            total_written += n_today
            pbar.update(n_today)

    # Résumé
    total_size = sum(
        f.stat().st_size
        for f in output.rglob(f"*.{ext}")
    )
    size_mb = total_size / (1024 ** 2)
    print(f"\n✓ {total_written:,} items générés")
    print(f"  {n_days} fichiers dans {output}/")
    print(f"  Taille totale : {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
