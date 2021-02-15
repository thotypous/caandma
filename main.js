var api_url = "https://caandma-api.pmatias.me";

function fdbs_rows(data) {
    return data['FDBS']['Manager']['TableList'][0]['RowList'];
}

function oculta_tudo() {
    $("#departamentos-container").addClass('d-none');
}

function mostra_departamentos() {
    $.ajax({
        url: api_url + '/departamentos',
        success: function (data) {
            var arr = fdbs_rows(data).map(function (row) {
                return {
                    href: '#depto=' + row['Original']['ID_DEPARTAMENTO'],
                    descricao: row['Original']['DESCRICAO'],
                };
            });
            $("#departamentos").loadTemplate($("#templ-departamento"), arr);
            $("#departamentos-container").removeClass('d-none');
        }
    });
}

function mostra_departamento(depto_id) {
    console.log(depto_id);
}

function roteia_hash() {
    oculta_tudo();
    var hash = document.location.hash;
    if (param = hash.match(/#depto=([0-9]+)/)) {
        mostra_departamento(param[1]);
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
            }
            else {
                $("#main-icon").removeClass("fa-store text-success").addClass("fa-store-slash text-warning");
            }
        }
    });
}

$(window).on('hashchange', roteia_hash);

$(function () {
    window.setInterval(atualiza_status_loja, 60000);
    atualiza_status_loja();
    roteia_hash();
});

