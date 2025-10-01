import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional


PRODUCTS_CSV_PATH = Path(os.getenv("PRODUCTS_CSV_PATH", "backend/data/products.csv"))


@dataclass
class Product:
    id: str
    name: str
    brand: str
    category: str
    concerns: List[str]
    url: Optional[str]
    image_url: Optional[str]


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def load_products() -> List[Product]:
    if not PRODUCTS_CSV_PATH.exists():
        return []
    products: List[Product] = []
    with open(PRODUCTS_CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            concerns_raw = row.get("concerns", "")
            concerns = [c.strip() for c in concerns_raw.split("|") if c.strip()]
            products.append(
                Product(
                    id=row.get("id", ""),
                    name=row.get("name", ""),
                    brand=row.get("brand", ""),
                    category=row.get("category", ""),
                    concerns=concerns,
                    url=row.get("url"),
                    image_url=row.get("image_url"),
                )
            )
    return products


def recommend_products(user_concerns: List[str], limit: int = 5) -> List[Dict]:
    products = load_products()
    if not products:
        return []

    normalized_user = set(_normalize(c) for c in user_concerns)

    def score(product: Product) -> int:
        product_concerns = set(_normalize(c) for c in product.concerns)
        return len(product_concerns.intersection(normalized_user))

    ranked = sorted(products, key=score, reverse=True)
    top = [p for p in ranked if score(p) > 0][:limit]
    if not top:
        top = ranked[:limit]

    return [
        {
            "id": p.id,
            "name": p.name,
            "brand": p.brand,
            "category": p.category,
            "concerns": p.concerns,
            "url": p.url,
            "image_url": p.image_url,
        }
        for p in top
    ]


