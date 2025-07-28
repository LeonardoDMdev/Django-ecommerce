from django.db import models
from django.contrib.auth.models import User
# id é criado automaticamente no django
# usuario estamos fazendo relação com a tabela que ja existe no django, 1 usuario pode ter 1 cliente e vice versa

class Cliente(models.Model):
    nome = models.CharField(max_length=200, null=True, blank=True)
    email = models.CharField(max_length=200, null=True, blank=True)
    telefone = models.CharField(max_length=200, null=True, blank=True)
    id_sessao =  models.CharField(max_length=200, null=True, blank=True)
    usuario = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE) 
    
    def __str__(self):
        return str(self.email)

class Categoria(models.Model): # categorias (masculino, feminino, Infantil)
    nome = models.CharField(max_length=200, null=True, blank=True)
    slug = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):           # la no admin a categoria printa um object
        return str(self.nome)    # essa função faz printar o nome da categoria q foi colocado

class Tipo(models.Model):  # tipo (camisa, camiseta, calças, bermuda)
    nome = models.CharField(max_length=200, null=True, blank=True)
    slug = models.CharField(max_length=200, null=True, blank=True)   

    def __str__(self):           # la no admin o tipo printa um object
        return str(self.nome)    # essa função faz printar o nome do tipo q foi colocado

class Produto(models.Model):
    imagem = models.ImageField(null=True, blank=True)
    nome = models.CharField(max_length=200, null=True, blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    ativo = models.BooleanField(default=True)
    categoria = models.ForeignKey(Categoria, null=True, blank=True, on_delete=models.SET_NULL)
    tipo = models.ForeignKey(Tipo, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return (f"Nome: {self.nome}, Categoria: {self.categoria}, Tipo: {self.tipo}, Preço: {self.preco}")

    def total_vendas(self): 
        itens = ItensPedido.objects.filter(pedido__finalizado=True, item_estoque__produto=self.id)
        total = sum([item.quantidade for item in itens])
        return total

class Cor(models.Model):
    nome = models.CharField(max_length=200, null=True, blank=True)
    codigo = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return str(self.nome)

class ItemEstoque(models.Model): # cada item em estoque tem apenas 1 produto associado a ele
    produto = models.ForeignKey(Produto, null=True, blank=True, on_delete=models.SET_NULL)
    cor = models.ForeignKey(Cor, null=True, blank=True, on_delete=models.SET_NULL)
    tamanho = models.CharField(max_length=200, null=True, blank=True)
    quantidade = models.IntegerField(default=0) # qtdd em estoque

    def __str__(self):
        return f"{self.produto.nome}, Tamanho: {self.tamanho}, Cor: {self.cor.nome}"

class Endereco(models.Model):
    rua = models.CharField(max_length=400, null=True, blank=True)
    numero = models.IntegerField(default=0)
    complemento = models.CharField(max_length=200, null=True, blank=True)
    cep = models.CharField(max_length=200, null=True, blank=True)
    cidade = models.CharField(max_length=200, null=True, blank=True)
    estado = models.CharField(max_length=200, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.cliente} - {self.rua} - {self.cidade}-{self.estado} - {self.cep}"

class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente, null=True, blank=True, on_delete=models.SET_NULL)
    finalizado = models.BooleanField(default=False)
    codigo_transacao = models.CharField(max_length=200, null=True, blank=True)
    endereco = models.ForeignKey(Endereco, null=True, blank=True, on_delete=models.SET_NULL)
    data_finalizacao = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        if self.cliente:
            return f"Cliente: {self.cliente.email} - id_pedido: {self.id} - Finalizado: {self.finalizado}"
        else:
            return f"Cliente: {self.cliente} - id_pedido: {self.id} - Finalizado: {self.finalizado}"
    
    @property #Ela permite criar métodos que podem ser acessados como atributos. 
    def quantidade_total(self):
        itens_pedido = ItensPedido.objects.filter(pedido__id=self.id)
        quantidade = sum([item.quantidade for item in itens_pedido])
        return quantidade
    
    @property
    def preco_total(self):
        itens_pedido = ItensPedido.objects.filter(pedido__id=self.id)
        preco = sum([item.preco_total for item in itens_pedido])
        return preco

    @property
    def itens(self):
        itens_pedidos = ItensPedido.objects.filter(pedido__id=self.id)
        return itens_pedidos

class ItensPedido(models.Model):
    item_estoque = models.ForeignKey(ItemEstoque, null=True, blank=True, on_delete=models.SET_NULL)
    quantidade = models.IntegerField(default=0) # qtdd dos pedidos do usuario
    pedido = models.ForeignKey(Pedido, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Id pedido: {self.pedido.id} - Produto: {self.item_estoque.produto.nome}, {self.item_estoque.tamanho}, {self.item_estoque.cor.nome}"
    
    @property #com esse decorator podemos chamar a função sem parenteses 
    def preco_total(self):
        return self.quantidade * self.item_estoque.produto.preco

class Banner(models.Model):
    imagem = models.ImageField(null=True, blank=True)
    link_destino = models.CharField(max_length=400, null=True, blank=True)
    ativo = models.BooleanField(default=False)

    def __str__(self):           # la no admin o tipo printa um object
        return f"{self.link_destino} - Ativo: {self.ativo}"
    

class Pagamento(models.Model):
    id_pagamento = models.CharField(max_length=400)
    pedido = models.ForeignKey(Pedido, null=True, blank=True, on_delete=models.SET_NULL)
    aprovado = models.BooleanField(default=False)
