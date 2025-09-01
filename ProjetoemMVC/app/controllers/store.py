import stripe
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models import Product, CartItem
from app import db

store_bp = Blueprint('store', __name__)

@store_bp.route('/')
@login_required
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@store_bp.route('/add/<int:pid>', methods=['POST'])
@login_required
def add_to_cart(pid):
    product = Product.query.get_or_404(pid)
    item = CartItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    if item:
        item.quantity += 1
    else:
        db.session.add(CartItem(user_id=current_user.id, product_id=product.id, quantity=1))
    db.session.commit()
    flash(f'{product.name} adicionado ao carrinho.', 'success')
    return redirect(url_for('store.index'))

@store_bp.route('/cart')
@login_required
def view_cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total_cents = sum(i.product.price_cents * i.quantity for i in items)
    return render_template('cart.html', items=items, total_cents=total_cents, stripe_key=current_app.config['STRIPE_PUBLIC_KEY'])

@store_bp.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    for key, val in request.form.items():
        if key.startswith('qty_'):
            item_id = key.split('_',1)[1]
            item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first()
            if not item: continue
            try:
                q = int(val)
            except ValueError:
                q = item.quantity
            if q <= 0:
                db.session.delete(item)
            else:
                item.quantity = q
    db.session.commit()
    flash('Carrinho atualizado.', 'info')
    return redirect(url_for('store.view_cart'))

@store_bp.route('/cart/clear', methods=['POST'])
@login_required
def clear_cart():
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('Carrinho limpo.', 'warning')
    return redirect(url_for('store.view_cart'))

@store_bp.route('/checkout/stripe', methods=['POST'])
@login_required
def checkout_stripe():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('Seu carrinho está vazio.', 'warning')
        return redirect(url_for('store.view_cart'))

    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    line_items = []
    for it in items:
        p = it.product
        line_items.append({
            "price_data": {
                "currency": "brl",
                "product_data": {"name": p.name, "images": [p.image_url], "description": p.description},
                "unit_amount": p.price_cents,
            },
            "quantity": it.quantity,
        })

    session_obj = stripe.checkout.Session.create(
        mode="payment",
        line_items=line_items,
        success_url=url_for('store.success', _external=True),
        cancel_url=url_for('store.view_cart', _external=True),
    )

    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    return redirect(session_obj.url, code=303)

@store_bp.route('/success')
@login_required
def success():
    return render_template('success.html')
