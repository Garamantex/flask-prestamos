document.addEventListener("DOMContentLoaded", function() {
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
