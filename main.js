var api_url = "https://caandma-api.pmatias.me";

function fdbs_rows(data) {
    return data['FDBS']['Manager']['TableList'][0]['RowList'];
}

function oculta_tudo(carregando) {
    $('#departamentos-container').addClass('d-none');
    $('#produtos-container').addClass('d-none');
    $('#carregando').addClass('d-none');
}

function mostra_departamentos() {
    $.ajax({
        url: api_url + '/departamentos',
        success: function (data) {
            var arr = fdbs_rows(data).map(function (row) {
                var r = row['Original'];
                return {
                    href: '#depto=' + parseInt(r['ID_DEPARTAMENTO']),
                    descricao: r['DESCRICAO'],
                };
            });
            $("#departamentos").loadTemplate($("#templ-departamento"), arr);
            oculta_tudo();
            $("#departamentos-container").removeClass('d-none');
        }
    });
}

function mostra_departamento(depto_id) {
    mostra_produtos(api_url + '/produtos_dept/' + parseInt(depto_id));
}

function mostra_pesquisa(termo) {
    mostra_produtos(api_url + '/produtos_consulta/' + termo);
}

function mostra_produtos(url) {
    $.ajax({
        url: url,
        success: function (data) {
            var arr = fdbs_rows(data).map(function (row) {
                var r = row['Original'];
                return {
                    img: (r['TEM_IMAGEM']
                        ? api_url + '/prodt_image/' + parseInt(r['ID_PRODUTO']) + '.png'
                        : 'noimage.svg'),
                    descricao: r['DESCRICAO'],
                    estoque: r['ESTOQUE'] ? 'fa fa-check-square' : 'fa fa-exclamation-triangle',
                    id: r['ID_PRODUTO'],
                    unidade: r['UNIDADE'],
                    valor: r['VALOR'],
                };
            });
            $("#produtos").loadTemplate($("#templ-produto"), arr);
            oculta_tudo();
            $("#produtos-container").removeClass('d-none');
        }
    });
}

function roteia_hash() {
    oculta_tudo();
    $('#carregando').removeClass('d-none');
    var hash = document.location.hash;
    var param;
    if (param = hash.match(/#depto=([0-9]+)/)) {
        mostra_departamento(param[1]);
    }
    else if (param = hash.match(/#busca=(.+)/)) {
        mostra_pesquisa(param[1]);
    }
    else {
        mostra_departamentos();
    }
}

function atualiza_status_loja() {
    $.ajax({
        url: api_url + '/status_loja',
        success: function (data) {
            if (data > 0) {
                $("#main-icon").removeClass("fa-store-slash text-warning").addClass("fa-store text-success");
                $("#main-icon").attr("title", "Loja aberta");
            }
            else {
                $("#main-icon").removeClass("fa-store text-success").addClass("fa-store-slash text-warning");
                $("#main-icon").attr("title", "Loja fechada");
            }
        }
    });
}


$(window).on('hashchange', roteia_hash);

$(function () {
    $("#form-busca").submit(function (e) {
        location.hash = '#busca=' + encodeURIComponent($('#input-busca').first().val());
        e.preventDefault();
    });

    window.setInterval(atualiza_status_loja, 60000);
    atualiza_status_loja();

    roteia_hash();
});

