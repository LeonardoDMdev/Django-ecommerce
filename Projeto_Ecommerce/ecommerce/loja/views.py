from django.shortcuts import render, redirect
from django.urls import reverse
from .models import *
import uuid
from .utils import filtrar_produtos, preco_minimo_maximo, ordenar_produtos, enviar_email_compra, exportar_csv
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from datetime import datetime
from .api_mercadopago import criar_pagamento


# Create your views here.
def homepage(request):
    banners = Banner.objects.filter(ativo=True)
    context = {"banners": banners}
    return render(request, 'homepage.html', context)

def loja(request, filtro=None):
    produtos = Produto.objects.filter(ativo=True) #pegando os itens da tabela
    produtos = filtrar_produtos(produtos, filtro) # função do (utils.py)

    if request.method == "POST":
        dados = request.POST.dict() # pegar os dados da requisição 
        produtos = produtos.filter(preco__gte=dados.get("preco_minimo"), preco__lte=dados.get("preco_maximo"))
        if "tamanho" in dados:
            itens = ItemEstoque.objects.filter(produto__in=produtos, tamanho=dados.get("tamanho")) #diferentes variações do mesmo produto
            ids_produtos = itens.values_list("produto", flat=True).distinct() #com o id consio pegar as variações do mesmo produto, | flat=true para retornar uma lista comum, não uma lista de tuplas,
            produtos = produtos.filter(id__in=ids_produtos) # aqui pego os ids dos produto que estão no ids_produtos
        if "tipo" in dados:
            produtos = produtos.filter(tipo__slug=dados.get("tipo"))
        if "categoria" in dados:
            produtos = produtos.filter(categoria__slug=dados.get("categoria"))

    itens = ItemEstoque.objects.filter(quantidade__gt=0, produto__in=produtos)  
    tamanhos = itens.values_list("tamanho", flat=True).distinct()
    ids_categorias = produtos.values_list("categoria", flat=True).distinct()
    categorias = Categoria.objects.filter(id__in=ids_categorias)
    minimo, maximo = preco_minimo_maximo(produtos)

    ordem = request.GET.get("ordem", "menor-preco")
    produtos = ordenar_produtos(produtos, ordem)   

    context = {"produtos": produtos, "minimo": minimo, "maximo": maximo, "tamanhos": tamanhos, "categorias": categorias}
    return render(request, 'loja.html', context)

def ver_produto(request, id_produto, id_cor=None):
    tem_estoque = False
    cores = {}
    tamanhos = {}
    cor_selecionada = None
    if id_cor:
        cor_selecionada = Cor.objects.get(id=id_cor)
    produto = Produto.objects.get(id=id_produto)
    itens_estoque = ItemEstoque.objects.filter(produto=produto, quantidade__gt=0) #qtdd maior q 0
    if len(itens_estoque) > 0:
        tem_estoque = True
        cores = {item.cor for item in itens_estoque} #hashset para nao ter valores duplicados
        if id_cor:
            itens_estoque = ItemEstoque.objects.filter(produto=produto, quantidade__gt=0, cor__id=id_cor)
            tamanhos = {item.tamanho for item in itens_estoque}
    similares = Produto.objects.filter(categoria__id=produto.categoria.id, tipo__id=produto.tipo.id).exclude(id=produto.id)[:4]
    context = {"produto": produto, "tem_estoque": tem_estoque, "cores": cores, "tamanhos": tamanhos,
               "cor_selecionada": cor_selecionada, "similares":similares}
    return render(request, 'ver_produto.html', context)

def adicionar_carrinho(request, id_produto):
    if request.method == 'POST' and id_produto:
        dados = request.POST.dict()
        tamanho = dados.get("tamanho")
        id_cor = dados.get("cor")
        if not tamanho:
            return redirect("Loja")
        
        resposta = redirect ("carrinho")
        if request.user.is_authenticated:
            cliente = request.user.cliente
        else:
            if request.COOKIES.get("id_sessao"):
                id_sessao = request.COOKIES.get("id_sessao")
            else:
                id_sessao = str(uuid.uuid4())
                resposta.set_cookie(key="id_sessao", value=id_sessao, max_age=60*60*24*30) # em segundos, isso da 30 dias
            cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
        
        pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=False) 
        item_estoque = ItemEstoque.objects.get(produto__id=id_produto, tamanho=tamanho, cor__id=id_cor)
        item_pedido, criado = ItensPedido.objects.get_or_create(item_estoque=item_estoque, pedido=pedido)
        item_pedido.quantidade += 1 # sempre q edita um elemento no views "manualmente" precisa salvar
        item_pedido.save()          # salvando
        return resposta
    else:
        return redirect('loja')

def remover_carrinho(request, id_produto):
    if request.method == 'POST' and id_produto:
        dados = request.POST.dict()
        tamanho = dados.get("tamanho")
        id_cor = dados.get("cor")
        if not tamanho:
            return redirect("Loja")
        
        if request.user.is_authenticated:
            cliente = request.user.cliente
        else:
            if request.COOKIES.get("id_sessao"):
                id_sessao = request.COOKIES.get("id_sessao")
                cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
            else:
                return redirect('loja') 
        pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=False) 
        item_estoque = ItemEstoque.objects.get(produto__id=id_produto, tamanho=tamanho, cor__id=id_cor)
        item_pedido, criado = ItensPedido.objects.get_or_create(item_estoque=item_estoque, pedido=pedido)
        item_pedido.quantidade -= 1 # sempre q edita um elemento no views "manualmente" precisa salvar
        item_pedido.save()          # salvando
        if item_pedido.quantidade <= 0:
            item_pedido.delete()
        return redirect ("carrinho")
    else:
        return redirect('loja')

def carrinho(request):
    if request.user.is_authenticated:
        cliente = request.user.cliente
    else:
        if request.COOKIES.get("id_sessao"):
            id_sessao = request.COOKIES.get("id_sessao")
            cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
        else:
            context = {"cliente_existente": False, "itens_pedido": None, "pedido": None}
            return render(request, 'carrinho.html', context)
    pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=False) #se nao existir pedido, vai criar um pedido, a variavel criado é Booleano
    itens_pedido = ItensPedido.objects.filter(pedido=pedido)
    context = {"itens_pedido": itens_pedido, "pedido": pedido, "cliente_existente": True}
    return render(request, 'carrinho.html', context)

def checkout(request):
    if request.user.is_authenticated:
        cliente = request.user.cliente
    else:
        if request.COOKIES.get("id_sessao"):
            id_sessao = request.COOKIES.get("id_sessao")
            cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
        else:
            return redirect("loja")
    pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=False)
    enderecos =  Endereco.objects.filter(cliente=cliente)
    context = {"pedido": pedido, "enderecos": enderecos, "erro": None}
    return render(request, 'checkout.html', context)

def finalizar_pedido(request, id_pedido):
    if request.method == "POST":
        erro = None
        dados = request.POST.dict()

        total = dados.get("total")
        total = float(total.replace(",", "."))    # o total estava vindo com virgula do formulario
        pedido = Pedido.objects.get(id=id_pedido)

        if total != float(pedido.preco_total):    # no BD o preco esta em decimal, q é minimamente diferente do float,por isso editamos para float ali
            erro = "preco"

        if not "endereco" in dados:
            erro = "endereco"
        else:
            id_endereco = dados.get("endereco")
            endereco = Endereco.objects.get(id=id_endereco)
            pedido.endereco = endereco

        if not request.user.is_authenticated:
            email = dados.get("email")
            try:
                validate_email(email)
            except ValidationError:
                erro = "email"
            if not erro:
                clientes = Cliente.objects.filter(email=email)
                if clientes:
                    pedido.cliente = clientes[0]
                else:
                    pedido.cliente.email = email
                    pedido.cliente.save()

        codigo_transacao = f"{pedido.id}-{datetime.now().timestamp()}"
        pedido.codigo_transacao = codigo_transacao
        pedido.save()
        if erro:
            enderecos = Endereco.objects.filter(cliente=pedido.cliente)
            context = {"erro": erro, "pedido": pedido, "enderecos": enderecos}
            return render(request, "checkout.html", context)
        else:
            itens_pedido = ItensPedido.objects.filter(pedido=pedido)
            #link = request.build_absolute_uri(reverse('finalizar_pagamento'))
            link = "https://31db763fc700.ngrok-free.app" + reverse('finalizar_pagamento')
            link_pagamento, id_pagamento = criar_pagamento(itens_pedido, link)
            pagamento = Pagamento.objects.create(id_pagamento=id_pagamento, pedido=pedido)
            pagamento.save()
            return redirect(link_pagamento)
    else:
        return redirect("loja")

def finalizar_pagamento(request):
    dados = request.GET.dict()
    status = dados.get("status")
    id_pagamento = dados.get("preference_id")
    if status == "approved":
        pagamento = Pagamento.objects.get(id_pagamento=id_pagamento)
        pagamento.aprovado = True
        pedido = pagamento.pedido
        pedido.finalizado = True
        pedido.data_finalizacao = datetime.now()
        pedido.save()
        pagamento.save()
        enviar_email_compra(pedido)
        if request.user.is_authenticated:
            return redirect("meus_pedidos")
        else:
            return redirect("pedido_aprovado", pedido.id)
    else:
        return redirect("checkout")

def pedido_aprovado(request, id_pedido): #pedido aprovado de um usuário que não está logado
    pedido = Pedido.objects.get(id=id_pedido)
    context = {"pedido": pedido}
    return render(request, "pedido_aprovado.html", context)

def adicionar_endereco(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            cliente = request.user.cliente
        else:
            if request.COOKIES.get("id_sessao"):
                id_sessao = request.COOKIES.get("id_sessao")
                cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
            else:
                return redirect("loja")
        dados = request.POST.dict()
        endereco = Endereco.objects.create(cliente=cliente, rua=dados.get("rua"), 
                                           numero=int(dados.get("numero")), 
                                           estado=dados.get("estado"), 
                                           cidade=dados.get("cidade"), 
                                           cep=dados.get("cep"), complemento=dados.get("complemento"))
        endereco.save()
        return redirect("checkout")
    else:
        context = {}
        return render(request, "adicionar_endereco.html", context)


@login_required
def minha_conta(request):
    cliente = request.user.cliente
    erro = None
    alterado = False
    if request.method == "POST":
        dados = request.POST.dict()
        if "senha_atual" in dados: # esta modificando a senha
            senha_atual = dados.get("senha_atual")
            nova_senha = dados.get("nova_senha")
            nova_senha_confimacao = dados.get("nova_senha_confimacao")

            if nova_senha == nova_senha_confimacao:
                #veriicar senha atual
                usuario = authenticate(request, username=request.user.email, password=senha_atual)
                if usuario:
                    usuario.set_password(nova_senha)
                    usuario.save()
                    alterado = True
                else:
                    erro = "senha_incorreta"   
            else:
                erro = "senhas_diferentes"

        elif "email" in dados:
            email = dados.get("email")
            telefone = dados.get("telefone")
            nome = dados.get("nome")
            if email != request.user.email:
                usuarios = User.objects.filter(email=email)
                if len(usuarios) > 0:
                    erro = "email_existente"         
            if not erro:
                cliente = request.user.cliente
                cliente.email = email
                request.user.email = email
                request.user.username = email
                cliente.nome = nome
                cliente.telefone = telefone 
                cliente.save()
                request.user.save()
                alterado = True
        else:
            erro = "formulario_invalido"

    context = {"erro": erro, "alterado": alterado}
    return render(request, 'usuarios/minha_conta.html', context)

@login_required
def meus_pedidos(request):
    cliente = request.user.cliente
    pedidos = Pedido.objects.filter(finalizado=True, cliente=cliente).order_by("-data_finalizacao") # sinal de menos significa decrescente
    context = {"pedidos": pedidos}
    return render(request, "usuarios/meus_pedidos.html", context)

def fazer_login(request):
    erro = False
    if request.user.is_authenticated:
        return redirect("loja")
    if request.method == "POST":
        dados = request.POST.dict()
        if "email" in dados and "senha" in dados:
            email = dados.get("email")
            senha = dados.get("senha")
            usuario = authenticate(request, username=email, password=senha)
            if usuario:
                login(request, usuario)
                return redirect("loja")
            else:
                erro = True
        else:
            erro = True
    context = {"erro": erro}
    return render(request, 'usuarios/login.html', context)

def criar_conta(request):
    erro = None
    if request.user.is_authenticated:
        return redirect("loja")
    if request.method == "POST":
        dados = request.POST.dict()
        if "email" in dados and "senha" in dados and "confirmacao_senha" in dados:
            # criar conta
            email = dados.get("email")
            senha = dados.get("senha")
            confirmacao_senha = dados.get("confirmacao_senha")
            try:
                validate_email(email)
            except ValidationError:
                erro = "email_invalido"
            if senha == confirmacao_senha:
                #criar conta
                usuario, criado = User.objects.get_or_create(username=email, email=email)
                if not criado:
                    erro = "usuario_existente"
                else:
                    usuario.set_password(senha)
                    usuario.save()

                    #fazer login
                    usuario = authenticate(request, username=email, password=senha)
                    login(request, usuario)

                    # criar cliente#
                    # verificar se  existe o id_sessao nos cookies
                    if request.COOKIES.get("id_sessao"):
                        id_sessao = request.COOKIES.get("id_sessao")
                        cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
                    else:
                        cliente, criado = Cliente.objects.get_or_create(email=email)
                    cliente.usuario = usuario
                    cliente.email = email
                    cliente.save()
                    return redirect("loja")
            else:
                erro = "senhas_diferentes"
        else:
            erro = "preenchimento"
    context = {"erro": erro}
    return render(request, 'usuarios/criar_conta.html', context)

@login_required
def fazer_logout(request):
    logout(request)
    return redirect("fazer_login")

@login_required
def gerenciar_loja(request):
    if request.user.groups.filter(name="equipe").exists():
        pedidos_finalizados = Pedido.objects.filter(finalizado=True)
        qtde_pedidos = len(pedidos_finalizados)
        faturamento = sum(pedido.preco_total for pedido in pedidos_finalizados)
        qtde_produtos = sum(pedido.quantidade_total for pedido in pedidos_finalizados)
        context = {"qtde_pedidos":qtde_pedidos, "faturamento":faturamento, "qtde_produtos":qtde_produtos}
        return render(request, "interno/gerenciar_loja.html", context=context)
    else:
        return redirect('loja')

@login_required    
def exportar_relatorio(request, relatorio):
    print(relatorio)
    if request.user.groups.filter(name="equipe").exists():
        if relatorio == "pedido":
            informacoes = Pedido.objects.filter(finalizado=True)
        elif relatorio == "cliente":
            informacoes = Cliente.objects.all()
        elif relatorio == "endereco":
            informacoes = Endereco.objects.all()
        return exportar_csv(informacoes)
    else:
        return redirect('gerenciar_loja')