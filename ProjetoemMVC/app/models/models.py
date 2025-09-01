from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.String(200))
    price_cents = db.Column(db.Integer)
    image_url = db.Column(db.String(200))

    @property
    def price_brl(self):
        return self.price_cents / 100


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    user = db.relationship('User', backref=db.backref('cart_items', lazy=True, cascade="all, delete-orphan"))
    product = db.relationship('Product')

def seed_products():
    from app.models import Product
    from app import db

    if Product.query.count() == 0:
        products = [
            Product(
                name="Camiseta Básica",
                description="Algodão macio.",
                price_cents=4990,
                image_url="https://i.imgur.com/nKLSkh4.jpg"
            ),
            Product(
                name="Vestido Midi",
                description="Leve e elegante.",
                price_cents=12990,
                image_url="https://i.imgur.com/jXwD9V7.png"
            ),
            Product(
                name="Jaqueta Jeans",
                description="Clássica, unissex.",
                price_cents=19990,
                image_url="https://i.imgur.com/Hjv1fF2.png"
            ),
            Product(
                name="Tênis Casual",
                description="Conforto diário.",
                price_cents=15990,
                image_url="https://i.imgur.com/G9LAeIF.png"
            ),
        ]

        db.session.bulk_save_objects(products)
        db.session.commit()
        print("✅ Produtos inseridos com sucesso!")
    else:
        print("⚠️ Produtos já existem, nada a fazer.")


