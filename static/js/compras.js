document.addEventListener("DOMContentLoaded", function() {
    var rows = document.querySelectorAll("#comprasTableBody tr");
    rows.forEach(function(row) {
        row.addEventListener("click", function() {
            document.getElementById("idCompra").value = row.getAttribute("data-id");
            document.getElementById("idProveedor").value = String(row.getAttribute("data-proveedor"));
            document.getElementById("idMateriaPrima").value = String(row.getAttribute("data-insumo"));
            document.getElementById("cantidad").value = row.getAttribute("data-cantidad");
            document.getElementById("fecha").value = row.getAttribute("data-fecha");
            document.getElementById("totalCompra").value = row.getAttribute("data-total");
        });
    });
});

function editarCompra() {
    var form = document.getElementById("formCompras");
    form.action = comprasEditarUrl;
    form.submit();
}
