from pathlib import Path

from database import Image, Product
from main import Session


def insert_file(path: Path) -> int:
    if not path.exists():
        return -1
    with Session() as session:
        with open(path, "rb") as inp_file:
            image = Image(name=path.name, data=inp_file.read())
            session.add(image)
        session.commit()


def insert_product(name: str, description: str, price_czk: float, image_id: int):
    with Session() as session:
        prod = Product(
            name=name, description=description, price_czk=price_czk, image_id=image_id
        )
        session.add(prod)
        session.commit()
