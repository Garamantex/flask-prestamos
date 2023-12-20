

document.addEventListener("DOMContentLoaded", function () {
  // Función para calcular el monto por cuota automáticamente
  function calcularMontoPorCuota() {
    // Obtener los valores seleccionados por el usuario
    var monto = parseFloat(document.getElementById("amount").value);
    var cuotas = parseInt(document.getElementById("dues").value);
    var interes = parseInt(document.getElementById("interest").value);

    console.log(monto, cuotas, interes);

    // Calcular el monto por cuota
    var montoPorCuota = (monto + (monto * (interes / 100))) / cuotas;

    // Mostrar el resultado en el campo correspondiente
    document.getElementById("amountPerPay").value = montoPorCuota;
    console.log(montoPorCuota);
  }

  // Asignar eventos a los campos para calcular el monto cuando cambien
  document.getElementById("amount").addEventListener("change", calcularMontoPorCuota);
  document.getElementById("dues").addEventListener("change", calcularMontoPorCuota);
  document.getElementById("interest").addEventListener("change", calcularMontoPorCuota);
});


document.addEventListener("DOMContentLoaded", function () {
  const transactionTypeSelect = document.getElementById('transactionType');
  const conceptSelect = document.getElementById('concept');

  transactionTypeSelect.addEventListener('change', loadConceptOptions);

  function loadConceptOptions() {
    const selectedTransactionType = transactionTypeSelect.value;
    const conceptOptions = conceptSelect.options;

    // Itera sobre las opciones de concepto y muestra u oculta según el tipo de transacción seleccionado
    for (let i = 0; i < conceptOptions.length; i++) {
      const conceptOption = conceptOptions[i];
      const conceptTransactionType = conceptOption.getAttribute('data-transaction-type');

      if (conceptTransactionType) {
        const transactionType = conceptTransactionType.replace('TransactionType.', '');

        if (transactionType === selectedTransactionType || selectedTransactionType === '') {
          conceptOption.style.display = 'block';
        } else {
          conceptOption.style.display = 'none';
        }
      }
    }
  }
});

