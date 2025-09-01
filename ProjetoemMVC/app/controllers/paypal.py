import requests
from flask import Blueprint, redirect, url_for, flash, current_app, session
from flask_login import login_required, current_user
from app.models import CartItem
from app import db
from app.config import Config

paypal_bp = Blueprint('paypal', __name__)

def paypal_api_base():
    return 'https://api-m.sandbox.paypal.com' if Config.PAYPAL_MODE == 'sandbox' else 'https://api-m.paypal.com'

def get_paypal_token():
    client_id = Config.PAYPAL_CLIENT_ID
    secret = Config.PAYPAL_CLIENT_SECRET
    if not client_id or not secret:
        raise RuntimeError('PAYPAL_CLIENT_ID/SECRET não configurados no .env')
    r = requests.post(f"{paypal_api_base()}/v1/oauth2/token",
                      auth=(client_id, secret),
                      data={"grant_type": "client_credentials"})
    r.raise_for_status()
    return r.json()["access_token"]

def cart_total_brl_cents(user_id):
    items = CartItem.query.filter_by(user_id=user_id).all()
    total_cents = sum(i.product.price_cents * i.quantity for i in items)
    return items, total_cents

@paypal_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    items, total_cents = cart_total_brl_cents(current_user.id)
    if not items:
        flash('Seu carrinho está vazio.', 'warning')
        return redirect(url_for('store.view_cart'))

    amount_value = f"{total_cents/100:.2f}"

    access_token = get_paypal_token()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {"currency_code": "BRL", "value": amount_value}
        }],
        "application_context": {
            "return_url": url_for('paypal.execute', _external=True),
            "cancel_url": url_for('store.view_cart', _external=True)
        }
    }

    r = requests.post(f"{paypal_api_base()}/v2/checkout/orders", json=payload, headers=headers)
    if r.status_code not in (200, 201):
        flash(f"Erro PayPal: {r.text}", 'danger')
        return redirect(url_for('store.view_cart'))
    data = r.json()
    session['paypal_order_id'] = data['id']
    approve = next((l['href'] for l in data.get('links', []) if l.get('rel') == 'approve'), None)
    if not approve:
        flash('Não foi possível iniciar o checkout do PayPal.', 'danger')
        return redirect(url_for('store.view_cart'))
    return redirect(approve)

@paypal_bp.route('/card', methods=['POST'])
@login_required
def card():
    return redirect(url_for('paypal.checkout'))

@paypal_bp.route('/execute')
@login_required
def execute():
    order_id = session.get('paypal_order_id')
    if not order_id:
        flash('Pedido PayPal não encontrado.', 'danger')
        return redirect(url_for('store.view_cart'))

    access_token = get_paypal_token()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    r = requests.post(f"{paypal_api_base()}/v2/checkout/orders/{order_id}/capture", headers=headers)
    if r.status_code not in (200, 201):
        flash(f"Falha ao capturar pagamento PayPal: {r.text}", 'danger')
        return redirect(url_for('store.view_cart'))

    # sucesso: limpar carrinho
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('Pagamento PayPal concluído ✅', 'success')
    return redirect(url_for('store.success'))
