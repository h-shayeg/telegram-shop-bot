"""Load the sample categories and products from data/sample_products.json.

Safe to run more than once: rows that already exist are skipped.
Usage: python -m scripts.seed_sample_data
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from bot.config import load_settings
from bot.db.models import Category, Product
from bot.db.session import make_session_factory

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "sample_products.json"


async def seed() -> None:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    session_factory = make_session_factory(load_settings().database_url)
    added_categories = 0
    added_products = 0
    async with session_factory() as session:
        for category_data in data["categories"]:
            category = await session.scalar(
                select(Category).where(Category.name == category_data["name"])
            )
            if category is None:
                category = Category(name=category_data["name"])
                session.add(category)
                await session.flush()
                added_categories += 1
            for item in category_data["products"]:
                exists = await session.scalar(
                    select(Product.id).where(
                        Product.category_id == category.id, Product.name == item["name"]
                    )
                )
                if exists is None:
                    session.add(
                        Product(
                            category_id=category.id,
                            name=item["name"],
                            description=item.get("description"),
                            price=item["price"],
                            stock=item.get("stock", 0),
                        )
                    )
                    added_products += 1
        await session.commit()
    await session_factory.kw["bind"].dispose()
    print(f"Seed done: {added_categories} categories and {added_products} products added")


if __name__ == "__main__":
    asyncio.run(seed())
