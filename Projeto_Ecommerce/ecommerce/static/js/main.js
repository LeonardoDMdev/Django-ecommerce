let url = new URL(document.URL); // pegar a url da pagina
let itens = document.getElementsByClassName("item-ordenar"); // pegar o itens q tem classe = "item-ordenar"

for (i=0; i < itens.length; i++){
    url.searchParams.set("ordem", itens[i].value);
    itens[i].value = url.href;
}

