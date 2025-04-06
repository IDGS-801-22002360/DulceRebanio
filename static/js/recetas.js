

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

document.addEventListener('DOMContentLoaded', function () {
    var modalAgregarInsumo = document.getElementById('modalAgregarInsumo');
    modalAgregarInsumo.addEventListener('show.bs.modal', function (event) {
        var button = event.relatedTarget;
        var recetaId = button.getAttribute('data-receta-id');
        var insumoId = button.getAttribute('data-insumo-id');
        var unidadMedida = button.getAttribute('data-unidad-medida');

        var modalRecetaId = modalAgregarInsumo.querySelector('#modalRecetaId');
        var modalInsumoId = modalAgregarInsumo.querySelector('#modalInsumoId');
        var modalUnidadMedida = modalAgregarInsumo.querySelector('#unidad_medida');

        modalRecetaId.value = recetaId;
        modalInsumoId.value = insumoId;
        modalUnidadMedida.value = unidadMedida;
    });
});