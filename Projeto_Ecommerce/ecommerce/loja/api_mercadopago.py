import mercadopago
import os

public_key = os.environ.get('PUBLIC_KEY')
token = os.environ.get('TOKEN')

def criar_pagamento(itens_pedido, link):
    sdk = mercadopago.SDK(token)

    itens = []
    for item in itens_pedido:
        quantidade = int(item.quantidade)
        nome = item.item_estoque.produto.nome
        preco_unitario = float(item.item_estoque.produto.preco)
        itens.append({
            "title": nome,
            "quantity": quantidade,
            "unit_price": preco_unitario,
            "currency_id": "BRL",  # Boa prática
        })

    preference_data = {
        "items": itens,
        "auto_return": "approved", 
        "back_urls": {
            "success": link,
            "pending": link,
            "failure": link,
        }
    }

    resposta = sdk.preference().create(preference_data)
    print("RESPOSTA:", resposta)  # Ajuda a entender o que tá vindo

    if "init_point" not in resposta["response"]:
        raise Exception("Erro ao gerar link de pagamento: {}".format(resposta["response"]))

    link_pagamento = resposta["response"]["init_point"]
    id_pagamento = resposta["response"]["id"]
    return link_pagamento, id_pagamento
