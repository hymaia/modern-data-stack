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

PLANS       = ["free", "premium", "enterprise"]
COUNTRIES   = ["FR", "BE", "DE", "ES", "IT", "GB", "NL", "CH", "PT", "PL"]
CATEGORIES  = ["electronics", "clothing", "books", "home", "sports", "beauty", "toys", "food"]
SUBCATEGORIES = {
    "electronics": ["audio", "peripherals", "displays", "phones", "cameras"],
    "clothing":    ["tops", "bottoms", "shoes", "accessories", "outerwear"],
    "books":       ["fiction", "non-fiction", "science", "history", "tech"],
    "home":        ["furniture", "decor", "kitchen", "garden", "lighting"],
    "sports":      ["fitness", "outdoor", "team-sports", "water", "winter"],
    "beauty":      ["skincare", "haircare", "makeup", "fragrance", "nails"],
    "toys":        ["board-games", "outdoor", "educational", "electronic", "dolls"],
    "food":        ["organic", "snacks", "beverages", "supplements", "spices"],
}
STATUSES        = ["pending", "processing", "shipped", "delivered", "cancelled", "refunded"]
CURRENCIES      = ["EUR", "USD", "GBP", "CHF"]
PAYMENT_METHODS = ["card", "paypal", "apple_pay", "google_pay", "bank_transfer", "crypto"]

CHUNK_SIZE = 50_000  # items par batch (équilibre RAM / vitesse)

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


# ── Générateurs d'entités ─────────────────────────────────────────────────────

def make_user(event_date: date) -> dict:
    uid = _uid()
    pk  = f"USER#{uid}"
    return {
        "PK":           pk,
        "SK":           f"PROFILE#{uid}",
        "entity_type":  "USER",
        "user_id":      uid,
        "email":        fake.email(),
        "full_name":    fake.name(),
        "created_at":   _dt_on(event_date),
        "plan":         random.choice(PLANS),
        "country":      random.choice(COUNTRIES),
        "is_verified":  random.random() > 0.3,
        "avatar_url":   f"https://cdn.example.com/avatars/{uid}.jpg" if random.random() > 0.4 else None,
        "locale":       fake.locale(),
        "phone":        fake.phone_number() if random.random() > 0.5 else None,
    }


def make_product(event_date: date) -> dict:
    pid      = _uid()
    pk       = f"PRODUCT#{pid}"
    category = random.choice(CATEGORIES)
    sub      = random.choice(SUBCATEGORIES[category])
    price    = round(random.uniform(2.99, 999.99), 2)
    return {
        "PK":           pk,
        "SK":           "METADATA",
        "entity_type":  "PRODUCT",
        "product_id":   pid,
        "name":         fake.catch_phrase(),
        "description":  fake.text(max_nb_chars=200),
        "category":     category,
        "subcategory":  sub,
        "price":        price,
        "currency":     random.choice(CURRENCIES),
        "stock":        random.randint(0, 10_000),
        "sku":          f"SKU-{fake.lexify('????').upper()}-{random.randint(1000, 9999)}",
        "tags":         [fake.word() for _ in range(random.randint(1, 6))],
        "images":       [f"https://cdn.example.com/products/{pid}-{i}.jpg" for i in range(1, random.randint(2, 5))],
        "is_active":    random.random() > 0.08,
        "created_at":   _dt_on(event_date),
        "weight_kg":    round(random.uniform(0.05, 50.0), 2),
        "dimensions_cm": {
            "l": random.randint(5, 100),
            "w": random.randint(5, 80),
            "h": random.randint(2, 60),
        },
        "rating_avg":   round(random.uniform(1.0, 5.0), 1),
        "rating_count": random.randint(0, 5000),
    }


def make_order(event_date: date) -> dict:
    oid     = _uid()
    uid     = _uid()
    status  = random.choice(STATUSES)
    n_items = random.randint(1, 8)
    items   = [
        {
            "product_id": _uid(),
            "qty":        random.randint(1, 5),
            "unit_price": round(random.uniform(2.99, 499.99), 2),
        }
        for _ in range(n_items)
    ]
    total = round(sum(i["qty"] * i["unit_price"] for i in items), 2)
    placed = _dt_on(event_date)
    return {
        "PK":              f"USER#{uid}",
        "SK":              f"ORDER#{oid}",
        "entity_type":     "ORDER",
        "order_id":        oid,
        "user_id":         uid,
        "status":          status,
        "placed_at":       placed,
        "updated_at":      placed,
        "delivered_at":    _dt_on(event_date + timedelta(days=random.randint(1, 7)))
        if status == "delivered" else None,
        "total_amount":    total,
        "currency":        random.choice(CURRENCIES),
        "items":           items,
        "item_count":      n_items,
        "payment_method":  random.choice(PAYMENT_METHODS),
        "shipping_address": {
            "street":  fake.street_address(),
            "city":    fake.city(),
            "zip":     fake.postcode(),
            "country": random.choice(COUNTRIES),
        },
        "cancellation_reason": random.choice(["out_of_stock", "user_request", "fraud", "payment_failed"])
        if status in ("cancelled", "refunded") else None,
        "GSI1PK": f"ORDER_STATUS#{status}",
        "GSI1SK": placed,
    }


def make_review(event_date: date) -> dict:
    rid    = _uid()
    pid    = _uid()
    uid    = _uid()
    rating = random.randint(1, 5)
    ts     = _dt_on(event_date)
    return {
        "PK":               f"PRODUCT#{pid}",
        "SK":               f"REVIEW#{rid}",
        "entity_type":      "REVIEW",
        "review_id":        rid,
        "product_id":       pid,
        "user_id":          uid,
        "order_id":         _uid() if random.random() > 0.3 else None,
        "rating":           rating,
        "title":            fake.sentence(nb_words=random.randint(4, 10)).rstrip("."),
        "body":             fake.paragraph(nb_sentences=random.randint(2, 6)),
        "created_at":       ts,
        "helpful_votes":    random.randint(0, 500),
        "unhelpful_votes":  random.randint(0, 50),
        "verified_purchase": random.random() > 0.35,
        "language":         random.choice(["fr", "en", "de", "es"]),
        "images":           [f"https://cdn.example.com/reviews/{rid}-{i}.jpg"
                             for i in range(random.randint(0, 3))],
        "GSI1PK":           f"USER#{uid}",
        "GSI1SK":           f"REVIEW#{event_date.isoformat()}",
        "GSI2PK":           f"PRODUCT#{pid}#RATING#{rating}",
        "GSI2SK":           ts,
    }


# ── Table de dispatch ─────────────────────────────────────────────────────────

GENERATORS: dict[str, tuple] = {
    "USER":    (make_user,    0.20),
    "PRODUCT": (make_product, 0.15),
    "ORDER":   (make_order,   0.42),
    "REVIEW":  (make_review,  0.23),
}

_TYPES   = list(GENERATORS.keys())
_WEIGHTS = [GENERATORS[t][1] for t in _TYPES]


# ── Génération par chunk ──────────────────────────────────────────────────────

def generate_chunk(n: int, event_date: date) -> list[dict]:
    """Génère n items avec répartition pondérée par type d'entité."""
    chosen = random.choices(_TYPES, weights=_WEIGHTS, k=n)
    return [GENERATORS[entity][0](event_date) for entity in chosen]


# ── Writers ───────────────────────────────────────────────────────────────────

def write_ndjson(records: list[dict], path: Path) -> None:
    """JSON newline-delimited — idéal pour Athena / Spark / DuckDB."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        for rec in records:
            f.write(orjson.dumps(rec) + b"\n")


def write_json_array(records: list[dict], path: Path) -> None:
    """JSON array avec enveloppe DynamoDB (Items + Count)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"Items": records, "Count": len(records), "ScannedCount": len(records)}
    with path.open("wb") as f:
        f.write(orjson.dumps(payload, option=orjson.OPT_INDENT_2))


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
    writer = write_ndjson if args.format == "ndjson" else write_json_array
    ext    = "ndjson" if args.format == "ndjson" else "json"
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
