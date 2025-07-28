from django.db.models import Max, Min
from django.core.mail import send_mail
from django.http import HttpResponse
import csv
from django.conf import settings

def filtrar_produtos(produtos, filtro):
    if filtro:
        if "-" in filtro:
            categoria, tipo = filtro.split("-") # categoria-tipo = [categoria, tipo]
            produtos = produtos.filter(tipo__slug=tipo, categoria__slug=categoria)
        else:
            produtos = produtos.filter(categoria__slug=filtro) # se tiver uma categoria depois do loja, vai verificar no banco de dados se existe essa categoria e retornar, se não existir retorna uma lista vazia sem dar erro
    return produtos        

def preco_minimo_maximo(produtos):
    maximo = 0
    minimo = 0
    if len(produtos) > 0:
        maximo = list(produtos.aggregate(Max("preco")).values())[0]
        maximo = round(maximo, 2) # arredondar 2 casas decimais
        minimo = list(produtos.aggregate(Min("preco")).values())[0]
        minimo = round(minimo, 2) # arredondar 2 casas decimais
    return minimo, maximo

def ordenar_produtos(produtos, ordem):
    if ordem == "menor-preco":
        produtos = produtos.order_by("preco") # por padrão ordena em ordem crescente, menor p maior
    elif ordem == "maior-preco":
        produtos = produtos.order_by("-preco",) # esse (-) antes do preco, é para mudar a ordem para decrescente, maior p menor
    elif ordem == "mais-vendidos":
        lista_produtos = []
        for produto in produtos:
            lista_produtos.append((produto.total_vendas(), produto)) 
        lista_produtos = sorted(lista_produtos, reverse=True, key=lambda tupla: tupla[0]) # o sorted ordena pelo numero das vendas na tupla, reserve=true fica do maior para o menor, mais vendidos p menos vendidos
        produtos = [item[1] for item in lista_produtos]
    return produtos

def enviar_email_compra(pedido):
    email = pedido.cliente.email
    assunto = f"Pedido aprovado: {pedido.id}"
    corpo = f"""Parábens! Seu pedido foi aprovado.
    ID do pedido: {pedido.id}
    Valor total: {pedido.preco_total}
    Quantidade de produtos: {pedido.quantidade_total}"""
    remetente = settings.EMAIL_HOST_USER
    send_mail(assunto, corpo, remetente, [email])

def exportar_csv(informacoes):
    colunas = informacoes.model._meta.fields  #você está acessando os metadados do modelo para obter todos os campos definidos nele.
    nomes_coluna = [coluna.name for coluna in colunas]

    resposta = HttpResponse(content_type="text/csv")
    resposta["Content-Disposition"] = "attachment; filename=export.csv"

    criador_csv = csv.writer(resposta, delimiter=";")

    criador_csv.writerow(nomes_coluna)

    for linha in informacoes.values_list():
        criador_csv.writerow(linha)
    return resposta