var api_url = "https://caandma-api.pmatias.me";

function fdbs_rows(data) {
    return data['FDBS']['Manager']['TableList'][0]['RowList'];
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
            console.log(arr);
            $("#departamentos").loadTemplate($("#templ-departamento"), arr);
            $("#departamentos-container").removeClass('d-none');
        }
    });
}

$(function() {
    mostra_departamentos();
});

