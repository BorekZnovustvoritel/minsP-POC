import datetime
from random import randint
from typing import Annotated

from fastapi import FastAPI, Request, Cookie, HTTPException, Form
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from uvicorn import run
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Product, Base, Image, Reservation, Order, OrderedItem
from definitions import (
    TEMPLATES_DIR,
    ROOT_DIR,
    TRANSLATIONS,
    TRANSLATION_CLASSES,
)

app = FastAPI()
engine = create_engine("sqlite:///" + str((ROOT_DIR / "app.db").absolute()))
Base.metadata.create_all(engine)
Session = sessionmaker(engine)
templates = Jinja2Templates(directory=TEMPLATES_DIR.absolute())


async def _cookie(cookie: int | None, response: Response):
    if cookie is None:
        value = randint(0, (2**32) - 1)
        response.set_cookie(key="coala_user", value=value, secure=True)


@app.get("/favicon.ico", response_class=Response)
async def icon():
    with open(ROOT_DIR / "coal.png", "rb") as inp_file:
        return Response(content=inp_file.read(), media_type="image/png")


@app.get("/kart.ico", response_class=Response)
async def kart():
    with open(ROOT_DIR / "kart.png", "rb") as inp_file:
        return Response(content=inp_file.read(), media_type="image/png")


@app.get("/", response_class=RedirectResponse)
async def index():
    return RedirectResponse(url="/cs_CZ/")


@app.get("/{lang}/", response_class=HTMLResponse)
async def homepage(
    lang: str, request: Request, coala_user: Annotated[None | int, Cookie()] = None
):
    if lang not in TRANSLATIONS:
        response = RedirectResponse(url="/cs_CZ/")
    else:
        with Session() as session:
            products = session.query(Product).filter(Product.in_stock > 0).all()
            products = [
                await product.translate(lang, quantity=product.in_stock)
                for product in products
            ]

            response = templates.TemplateResponse(
                "index.html",
                {
                    "translation": TRANSLATION_CLASSES[lang],
                    "request": request,
                    "products": products,
                    "lang": lang,
                },
            )
    await _cookie(coala_user, response)
    return response


@app.get("/image/{idx}", response_class=Response)
async def image(idx: int):
    with Session() as session:
        image_ = session.query(Image).filter(Image.id == idx).one_or_none()
        if not image_:
            return Response(status_code=404, content="Whoopsie")
        return Response(content=image_.data, media_type="image/jpg")


@app.get("/{lang}/legal")
async def legal(lang: str, request: Request):
    if lang not in TRANSLATIONS:
        response = RedirectResponse(url="/cs_CZ/")
    else:
        response = templates.TemplateResponse(
            "legal.html",
            {
                "translation": TRANSLATION_CLASSES[lang],
                "request": request,
                "lang": lang,
            },
        )
    return response


@app.get("/{lang}/payment")
async def payment(lang: str, request: Request):
    if lang not in TRANSLATIONS:
        response = RedirectResponse(url="/cs_CZ/")
    else:
        response = templates.TemplateResponse(
            "payment.html",
            {
                "translation": TRANSLATION_CLASSES[lang],
                "request": request,
                "lang": lang,
            },
        )
    return response


@app.get("/{lang}/kart")
async def kart(lang: str, coala_user: Annotated[int, Cookie()], request: Request):
    if lang not in TRANSLATIONS:
        return RedirectResponse(url="/cs_CZ/")
    with Session() as session:
        products = []
        reservations = session.query(Reservation).filter_by(user_id=coala_user).all()
        for reservation in reservations:
            products.append(
                await session.query(Product)
                .filter_by(id=reservation.product_id)
                .one()
                .translate(lang)
            )

        response = templates.TemplateResponse(
            "kart.html",
            {
                "translation": TRANSLATION_CLASSES[lang],
                "request": request,
                "products": products,
                "lang": lang,
            },
        )
        return response


@app.get("/{lang}/form")
async def form(lang: str, coala_user: Annotated[int, Cookie()], request: Request):
    if lang not in TRANSLATIONS:
        return RedirectResponse(url="/cs_CZ/")
    response = templates.TemplateResponse(
        "form.html",
        {
            "translation": TRANSLATION_CLASSES[lang],
            "request": request,
            "lang": lang,
        },
    )
    return response


@app.post("/kart/add/{idx}")
async def add_to_kart(
    idx: int, coala_user: Annotated[int, Cookie()], quantity: int = 1
):
    if 1 < quantity < 100:
        raise HTTPException(status_code=400, detail="Invalid quantity.")
    with Session() as session:
        with session.begin():
            product = session.query(Product).filter_by(id=idx).one_or_none()
            if not product:
                raise HTTPException(status_code=404, detail="Unknown product.")
            if product.in_stock < quantity:
                raise HTTPException(
                    status_code=404, detail="Not enough product in stock."
                )
            reservation = (
                session.query(Reservation)
                .filter_by(user_id=coala_user, product_id=product.id)
                .one_or_none()
            )
            if not reservation:
                reservation = Reservation(
                    timestamp=datetime.datetime.now(),
                    user_id=coala_user,
                    product_id=idx,
                    quantity=quantity,
                )
            else:
                reservation.timestamp = datetime.datetime.now()
                reservation.quantity += quantity
            # product.in_stock -= quantity
            session.merge(reservation)
            session.commit()
    print("HI")
    return "ok"


@app.post("/kart/remove/{idx}")
async def remove_from_cart(idx: int, coala_user: Annotated[int, Cookie()]):
    with Session() as session:
        with session.begin():
            reservation = (
                session.query(Reservation)
                .filter_by(user_id=coala_user, product_id=idx)
                .one()
            )
            product = session.query(Product).filter_by(id=reservation.product_id).one()
            product.in_stock += reservation.quantity
            session.delete(reservation)
            session.commit()
    return "ok"


@app.post("/order/submit")
async def submit_order(
    first_name: Annotated[str, Form()],
    last_name: Annotated[str, Form()],
    email: Annotated[str, Form()],
    phone: Annotated[str, Form()],
    country: Annotated[str, Form()],
    postal_code: Annotated[str, Form()],
    city: Annotated[str, Form()],
    address_line_1: Annotated[str, Form()],
    address_line_2: Annotated[str, Form()],
    coala_user: Annotated[int, Cookie()],
):
    # TODO validate all
    with Session() as session:
        try:
            with session.begin():
                reservations = (
                    session.query(Reservation).filter_by(user_id=coala_user).all()
                )
                order = Order(
                    user_id=coala_user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    country=country,
                    postal_code=postal_code,
                    city=city,
                    address_line_1=address_line_1,
                    address_line_2=address_line_2,
                )
                session.add(order)
                session.flush()
                for res in reservations:
                    ordered_item = OrderedItem(
                        order_id=order.id, item_id=res.product_id, quantity=res.quantity
                    )
                    product = session.query(Product).filter_by(id=res.product_id).one()
                    if product.in_stock < res.quantity:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Not enough product in stock: {product.name}",
                        )
                    product.in_stock -= res.quantity
                    session.add(ordered_item)
                session.commit()
        except:
            session.rollback()
            raise

    # This is just a mock code
    with Session() as session:
        print("Objednávky k vyřízení:")
        for order in session.query(Order).filter_by(outstanding=True).all():
            print(
                f"Adresa: {order.country}, {order.city}, {order.postal_code}, {order.address_line_1} {order.address_line_2}"
            )
            print(f"Email: {order.email}, tel.: {order.phone}")
            print("Předměty:")
            price = 0
            for ordered_item in (
                session.query(OrderedItem).filter_by(order_id=order.id).all()
            ):
                product = (
                    session.query(Product).filter_by(id=ordered_item.item_id).one()
                )
                print(
                    f"{product.name}, {product.description}, CENA: {product.price_czk} CZK"
                )
                price += product.price_czk
            print(f"Celková suma: {price} CZK")


if __name__ == "__main__":

    run(app, port=8080)
