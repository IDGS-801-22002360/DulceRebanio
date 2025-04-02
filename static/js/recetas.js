document.getElementById("btnSiguiente").addEventListener("click", function () {
    var modalAgregar = bootstrap.Modal.getInstance(document.getElementById("modalAgregarReceta"));
    var modalInsumos = new bootstrap.Modal(document.getElementById("modalSeleccionarInsumos"));

    if (modalAgregar) {
        modalAgregar.hide();
    }

    setTimeout(() => modalInsumos.show(), 500);
});

document.addEventListener('DOMContentLoaded', function() {
    const btnRenombrar = document.querySelector('button[value="renombrar"]');
    const inputNombre = document.getElementById('txtNombreReceta');
    
    btnRenombrar.addEventListener('click', function(e) {
        if (!inputNombre.value.trim()) {
            e.preventDefault();
            alert('Por favor ingrese un nombre para la receta');
        }
    });
});