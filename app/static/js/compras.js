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
            btnGuardar.disabled = true;
        });
    });
});

function editarCompra() {
    var form = document.getElementById("formCompras");
    form.action = comprasEditarUrl;
    form.submit();
}

document.addEventListener("DOMContentLoaded", function() {
    function sanitizarNumerosYPuntos(texto) {
        // Permite solo dígitos (0-9) y puntos, elimina el resto
        return texto.replace(/[^0-9.]/g, "").trim();
    }

    // Supongamos que el campo se llama "totalCompra"
    document.getElementById("totalCompra").addEventListener("input", function() {
        this.value = sanitizarNumerosYPuntos(this.value);
    });
});


document.addEventListener("DOMContentLoaded", function() {
    function sanitizarTexto(texto) {
        return texto.replace(/[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]/g, "").trim();
    }

    document.getElementById("cantidad").addEventListener("input", function() {
        this.value = sanitizarTexto(this.value);
    });
    document.getElementById("totalCompra").addEventListener("input", function() {
        this.value = sanitizarTexto(this.value);
    });
});


