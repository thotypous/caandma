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
        success: function(data) {
            var arr = fdbs_rows(data).map(function(row) {
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

$(window).on('hashchange', function(e) {
    roteia_hash();
});

$(function() {
    roteia_hash();
});

