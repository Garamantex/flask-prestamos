import '../scss/main.scss';
import 'bootstrap';
import $ from 'jquery';

document.addEventListener('DOMContentLoaded', function() {
    var form = document.getElementById('login-form');

    form.addEventListener('submit', function(event) {
        event.preventDefault(); // Evita el comportamiento predeterminado de envío del formulario

        var emailInput = document.getElementById('email').value;
        var passwordInput = document.getElementById('password').value;

        if (emailInput === 'admin@mail.com') {
            // Redirige al usuario admin a la página "menu-admin.html"
            window.location.href = 'menu-admin.html';
        } else if (emailInput === 'vendedor@mail.com') {
            // Redirige al usuario vendedor a la página "sale-menu.html"
            window.location.href = 'menu-sale.html';
        } else {
            // Muestra un alerta con un mensaje de error para otros usuarios
            alert('Usuario no válido');
        }
    });
});

$(document).ready(function() {
    // Realizar una solicitud AJAX para obtener la información de los morosos desde Flask
    $.ajax({
        url: '/get-debtors',  // Reemplaza esto con la URL correcta de tu endpoint en Flask
        method: 'GET',
        success: function(response) {
            console.log(response)
            // La respuesta debe contener los datos de los morosos en formato JSON
            
            // Inicializa variables para el total de morosos y el total de mora
            var totalMorosos = 0;
            var totalMora = 0;

            // Itera sobre los morosos y agrega elementos HTML dinámicamente
            response.forEach(function(moroso) {
                var $morosoItem = $('<li class="c-cajas__item"></li>');

                // Agrega el encabezado con el nombre del moroso
                $morosoItem.append('<div class="c-cajas__item__header"><h3 class="c-cajas__item__title c-headings c-headings__h2">' + moroso.employee_name + '</h3></div>');

                // Crea una lista para los clientes del moroso
                var $clientsList = $('<ul class="c-cajas"></ul>');

                // Itera sobre los clientes y agrega elementos para cada uno
                moroso.clients.forEach(function(client) {
                    var $clientItem = $('<li class="c-cajas__item"></li>');

                    // Agrega información del cliente
                    $clientItem.append('<div class="c-cajas__item__body__item c-cajas__item__body__item--100"><span class="c-cajas__item__body__item__label">Cliente:</span><span class="c-cajas__item__body__item__value">' + client.client_name + '</span></div>');
                    $clientItem.append('<div class="c-cajas__item__body__item c-cajas__item__body__item--100"><span class="c-cajas__item__body__item__label">Cuotas pagadas:</span><span class="c-cajas__item__body__item__value">' + client.paid_installments + '</span></div>');
                    $clientItem.append('<div class="c-cajas__item__body__item c-cajas__item__body__item--100"><span class="c-cajas__item__body__item__label">Cuotas vencidas:</span><span class="c-cajas__item__body__item__value">' + client.overdue_installments + '</span></div>');
                    $clientItem.append('<div class="c-cajas__item__body__item c-cajas__item__body__item--100"><span class="c-cajas__item__body__item__label">Monto deuda:</span><span class="c-cajas__item__body__item__value">$' + client.remaining_debt + '</span></div>');
                    $clientItem.append('<div class="c-cajas__item__body__item c-cajas__item__body__item--100"><span class="c-cajas__item__body__item__label">Monto mora:</span><span class="c-cajas__item__body__item__value">$' + client.total_overdue_amount + '</span></div>');
                    $clientItem.append('<div class="c-cajas__item__body__item c-cajas__item__body__item--100"><span class="c-cajas__item__body__item__label">Ultimo pago:</span><span class="c-cajas__item__body__item__value">' + client.last_paid_installment_date + '</span></div>');

                    // Agrega el elemento del cliente a la lista de clientes del moroso
                    $clientsList.append($clientItem);

                    // Actualiza el total de morosos y el total de mora
                    totalMorosos += parseInt(client.overdue_installments);
                    totalMora += parseFloat(client.total_overdue_amount);
                });

                // Agrega la lista de clientes al moroso
                $morosoItem.append($clientsList);

                // Agrega el moroso a la página
                $('#morosos-container').append($morosoItem);
            });

            // Actualiza el total de morosos y el total de mora en la página
            $('#totalMorosos').text(totalMorosos);
            $('#totalMora').text(totalMora.toFixed(2));
        },
        error: function() {
            console.error('Error al obtener los morosos.');
        }
    });
});

/* calcular interes */

document.addEventListener('DOMContentLoaded', function() {
    var plazoInput = document.getElementById('dues');
    var interesInput = document.getElementById('interest');
    var cuotaAproxInput = document.getElementById('amountPerPay');

    plazoInput.addEventListener('input', function() {
        calcularCuotaAproximada();
    });

    interesInput.addEventListener('input', function() {
        calcularCuotaAproximada();
    });

    function calcularCuotaAproximada() {
        var plazo = parseInt(plazoInput.value);
        var interes = parseFloat(interesInput.value);
        var prestamo = parseFloat(document.getElementById('amount').value);

        if (isNaN(plazo) || isNaN(interes) || isNaN(prestamo) || interes === 0) {
            cuotaAproxInput.value = '';
            return;
        }

        
        var cuota = prestamo / plazo;
        console.log(cuota);
        console.log(sessionStorage)
        var cuotaInteres = cuota + (cuota * interes / 100);
        console.log(cuotaInteres);
        cuotaAproxInput.value = cuotaInteres.toFixed(2);
    }

    // Llama a la función para calcular la cuota inicialmente
    calcularCuotaAproximada();
});

async function obtenerValoresMaximos() {
    try {
        const response = await fetch("/maximum-values-loan");
        const data = await response.json();
        // Obtener elementos del formulario
        const montoInput = document.getElementById("amount");
        const cuotasSelect = document.getElementById("dues");
        const interesSelect = document.getElementById("interest");
        
        // Configurar el máximo de monto permitido
        montoInput.setAttribute("max", data.maximum_sale);

        montoInput.addEventListener("input", function() {
            const monto = parseFloat(montoInput.value);
            
            if (monto > data.maximum_sale) {
                return('El monto máximo permitido es de $' + data.maximum_sale);
            }
        });
        
        // Configurar el máximo de cuotas permitidas
        for (let i = 1; i <= data.maximum_installments; i++) {
            const option = document.createElement("option");
            option.text = i;
            cuotasSelect.add(option);
        }
        
        // Configurar el mínimo de interés permitido
        for (let i = data.minimum_interest; i <= 50; i++) {
            const option = document.createElement("option");
            option.text = i;
            interesSelect.add(option);
        }
    } catch (error) {
        console.error("Error al obtener los valores máximos del préstamo:", error);
    }
}

obtenerValoresMaximos()

$(document).ready(function () {
    // Obtener el valor máximo del coordinador cuando la página se carga
    $.ajax({
        url: '/get_maximum_values_create_salesman',
        method: 'GET',
        success: function (data) {
            // Actualizar los campos de entrada correspondientes con los valores máximos
            $('#maximum_cash').val(data.maximum_cash_salesman);
            $('#maximum_sale').val(data.maximum_sale_coordinator);
            $('#maximum_expense').val(data.maximum_expense_coordinator);
            $('#maximum_installments').val(data.maximum_installments_coordinator);
            $('#minimum_interest').val(data.minimum_interest_coordinator);
        },
        error: function () {
            console.error('Error al obtener los valores máximos del coordinador');
        }
    });
});

