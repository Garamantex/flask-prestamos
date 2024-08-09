import '../scss/main.scss';
import 'bootstrap';


document.addEventListener('DOMContentLoaded', function() {

    var plazoInput = document.getElementById('dues');
    var interesInput = document.getElementById('interest');
    var cuotaAproxInput = document.getElementById('amountPerPay');

    if (plazoInput) {
        plazoInput.addEventListener('input', function() {
            calcularCuotaAproximada();
        });
    }

    if (interesInput) {
        interesInput.addEventListener('input', function() {
            calcularCuotaAproximada();
        });
    }

    function calcularCuotaAproximada() {
        var plazo = parseInt(plazoInput.value);
        var interes = parseFloat(interesInput.value);
        var prestamo = parseFloat(document.getElementById('amount').value);

        if (isNaN(plazo) || isNaN(interes) || isNaN(prestamo) || interes === 0 || plazo <= 0) {
            cuotaAproxInput.value = '';
            return;
        }

        var cuota = prestamo / plazo;
        var cuotaInteres = cuota + (cuota * interes / 100);
        cuotaAproxInput.value = cuotaInteres.toFixed(2);
    }

    // Llama a la función para calcular la cuota inicialmente
    if (plazoInput && interesInput) {
        calcularCuotaAproximada();
    }
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
        if(montoInput) montoInput.setAttribute("max", data.maximum_amount);

        if(montoInput){
            montoInput.addEventListener("input", function() {
                const monto = parseFloat(montoInput.value);
                
                if (monto > data.maximum_sale) {
                    // Mostrar un mensaje de error
                    alert('El monto máximo permitido es de $' + data.maximum_sale + ' Quedara en estado Pendiente de Aprobación');
                    // montoInput.value =  data.maximum_sale; // Establecer el valor máximo
                }
            });
        }
        
        // Configurar el máximo de cuotas permitidas
        for (let i = 1; i <= data.maximum_installments; i++) {
            const option = document.createElement("option");
            option.text = i;
            if(cuotasSelect){
                cuotasSelect.add(option);
            }
        }
        
        // Configurar el mínimo de interés permitido
        for (let i = data.minimum_interest; i <= 50; i++) {
            const option = document.createElement("option");
            option.text = i;
            if(interesSelect){
                interesSelect.add(option);
            }
        }
    } catch (error) {
        console.error("Error al obtener los valores máximos del préstamo:", error);
    }
}


obtenerValoresMaximos();


/* $(document).ready(function () {
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
}); */

function formatNumericFields() {
    const numericFields = document.querySelectorAll('.js-number');
    
    numericFields.forEach(function(field) {
        const rawValue = field.value.replace(/,/g, ''); // Eliminar comas si las hubiera
        const parsedValue = parseFloat(rawValue);
        
        if (!isNaN(parsedValue)) {
            field.value = parsedValue.toLocaleString('es-ES', { minimumFractionDigits: 2 });
        }
    });
}

formatNumericFields();

document.addEventListener('DOMContentLoaded', function() {
    // Verifica si la URL actual es la página de inicio
    if (window.location.href.endsWith('/')) {
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
    }
});

document.addEventListener('DOMContentLoaded', function () {
    // Al hacer clic en cualquier botón "Ver comprobante"
    document.querySelectorAll('.js-comprobante').forEach(function (button) {
        button.addEventListener('click', function () {
            // Obtén el atributo data-target del botón para identificar la modal asociada
            var targetModalId = this.getAttribute('data-target');
            var targetModal = document.getElementById(targetModalId);

            // Muestra la modal correspondiente
            targetModal.style.display = 'flex';
        });
    });

    // Al hacer clic fuera de la imagen, cierra la modal
    document.querySelectorAll('.c-modal').forEach(function (modal) {
        modal.addEventListener('click', function (event) {
            if (event.target.classList.contains('c-modal')) {
                // Cierra la modal
                this.style.display = 'none';
            }
        });
    });

    // Al hacer clic en el botón de cierre, cierra la modal
    document.querySelectorAll('.close-button').forEach(function (closeButton) {
        closeButton.addEventListener('click', function () {
            // Obtén la modal asociada al botón de cierre
            var modal = this.closest('.c-modal');
            modal.style.display = 'none';
        });
    });
});


// Codigo JS de la ruta /Payment-List
document.addEventListener('DOMContentLoaded', function () {
    // Obtén referencias a los elementos del DOM
    var verDetallesBtn = document.getElementById('verDetallesBtn');
    var detallesContainer = document.getElementById('detallesContainer');

    // Agrega un evento de clic al botón
    if (verDetallesBtn) {
        verDetallesBtn.addEventListener('click', function () {
            // Alternar la visibilidad del contenedor con un efecto de transición
            if (detallesContainer.style.display === 'none') {
                detallesContainer.style.display = 'block';
                detallesContainer.style.opacity = '1';
            } else {
                detallesContainer.style.opacity = '0';
                setTimeout(function () {
                    detallesContainer.style.display = 'none';
                }, 50); // Ajusta la duración de la transición según tus preferencias
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function () {
    var installmentsContainer = document.getElementById('installmentsContainer');
    
    if (installmentsContainer) {
        // Recorre las cuotas y aplica estilos según el estado
        var installments = installmentsContainer.querySelectorAll('.request-item');
        installments.forEach(function (installment) {
            var statusElement = installment.querySelector('p:nth-child(2) span');

            if (statusElement) {
                var status = statusElement.innerText.trim();

                if (status === 'PAGADA') {
                    installment.style.display = 'none'; // Oculta las cuotas pagadas
                } else if (status === 'MORA') {
                    installment.style.backgroundColor = 'red'; // Agrega el estilo de fondo rojo a las cuotas en mora
                }
            }
        });
    }
});

 // Agrega un evento de clic al botón para mostrar/ocultar detalles
 var verDetallesBtn = document.getElementById('verDetallesBtn');
 var detallesContainer = document.getElementById('detallesContainer');
 
if (verDetallesBtn && detallesContainer) {
    verDetallesBtn.addEventListener('click', function () {
        if (detallesContainer.style.display === 'none') {
            detallesContainer.style.display = 'block';
            detallesContainer.style.opacity = '1';
        } else {
            detallesContainer.style.opacity = '0';
            setTimeout(function () {
                detallesContainer.style.display = 'none';
            }, 300);
        }
    });
}

   // Función para actualizar los valores en la modal
   function updateModalValues(installmentValue, overdueAmount) {
    document.getElementById('installmentValue').textContent = installmentValue.toLocaleString();
    document.getElementById('overdueAmount').textContent = overdueAmount.toLocaleString();
}
    function toggleHiddenParagraphs() {
    var hiddenParagraphs = document.querySelectorAll('.u-hidden');
    hiddenParagraphs.forEach(function(paragraph) {
        paragraph.classList.toggle('u-hidden');
    });
}


// Espera a que el documento esté listo
document.addEventListener('DOMContentLoaded', function () {
    // Obtén todas las cuotas listadas
    var cuotas = document.querySelectorAll('.c-card__box-mannager');
    // Obtén todos los botones de Pago
    var btnsPagar = document.querySelectorAll('.btn-pagar');
    // Obtén todos los botones de Mora
    var btnsMora = document.querySelectorAll('.btn-mora');
    var cuotasLabels = document.querySelectorAll('.cuota-label');

    // Agrega un evento de clic a cada botón de pago
    btnsPagar.forEach(function (btn) {
        btn.addEventListener('click', function () {
            // Obtén el valor de la cuota del botón de pago
            var installmentValue = parseFloat(this.getAttribute('data-installment-value'));
            var overdueAmount = parseFloat(this.getAttribute('data-overdue-amount'));
            var loanId = this.getAttribute('data-id');

            // Calcula la suma de los valores
            var totalAmount = installmentValue;

            // Establece el valor del monto a pagar en el campo de entrada con formato de miles
            document.getElementById('customPayment').value = totalAmount;

            // Actualiza los valores en la modal
            updateModalValues(installmentValue, overdueAmount);

            // Almacena el ID del préstamo en un campo oculto
            document.getElementById('loanId').value = loanId;
        });
    });


    // Agrega un evento de clic al botón de "Confirmar Pago"
    if(document.getElementById('confirmPaymentBtn')) {
        document.getElementById('confirmPaymentBtn').addEventListener('click', function () {
            // console.log('Confirmar pago')
            var loanId = document.getElementById('loanId').value; // Obtener ID de préstamo desde el campo oculto
            var customPayment = document.getElementById('customPayment').value; // Obtener valor de pago personalizado
            // Enviar solicitud POST al servidor con los datos del pago
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/confirm_payment', true);
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4) {
                    // Verificar el estado de la respuesta
                    if (xhr.status === 200) {
                        // Procesar respuesta del servidor
                        // console.log(xhr.responseText);
                        // Recargar la página después de confirmar el pago
                        window.location.reload();
                    } else {
                        // Mostrar un mensaje de error al usuario
                        console.error('Error al procesar el pago:', xhr.responseText);
                    }
                }
            };
            xhr.send('loan_id=' + loanId + '&customPayment=' + customPayment);
        });
    }

    
    btnsMora.forEach(function (btn) {
        btn.addEventListener('click', function () {
            var loanId = this.getAttribute('data-id');
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/mark_overdue', true);
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        // console.log(xhr.responseText);
                        window.location.reload();
                    } else {
                        console.error('Error al marcar como MORA:', xhr.responseText);
                    }
                }
            };
            xhr.send('loan_id=' + loanId);
        });
    });

    if(document.getElementById('btn-ocultar')){
        document.getElementById('btn-ocultar').addEventListener('click', function () {
            // Convertir NodeList a un array para usar el método sort()
            var cuotasArray = Array.from(cuotas);
        
            // Ordenar los elementos por fecha de modificación del más viejo al más reciente
            cuotasArray.sort(function (a, b) {
                var fechaA = new Date(a.getAttribute('data-last-loan-modification-date')).getTime();
                var fechaB = new Date(b.getAttribute('data-last-loan-modification-date')).getTime();
                return fechaA - fechaB;
            });
        
            // Limpiar el contenedor antes de mostrar los elementos ordenados
            var contenedor = document.querySelector('.list-group');
            contenedor.innerHTML = '';
        
            // Mostrar los elementos ordenados en el DOM
            cuotasArray.forEach(function (cuota) {
                contenedor.appendChild(cuota);
            });

            cuotasArray.forEach(function (cuota) {
                if (cuota.classList.contains("u-hidden")) {
                    cuota.classList.toggle('u-hidden'); // Alternar entre ocultar y mostrar
                    cuota.classList.add('c-card__box-mannager');
                    cuota.querySelectorAll('.cuota-label').forEach(function (boton) {
                        boton.classList.remove("c-btn");
                        boton.classList.add("u-hidden");
                    });
                } else if (cuota.classList.contains("u-block")) {
                    // Si la cuota está bloqueada, no hacemos nada
                } else {
                    cuota.classList.add('u-hidden');
                    cuota.classList.remove('c-card__box-mannager');
                };
            });
        });
    }

    // Itera sobre cada cuota
    cuotas.forEach(function (cuota) {
        // console.log(cuota);
        
        // Obtén el estado de la cuota desde el atributo data
        var estadoCuotaAnterior = cuota.getAttribute('data-previous-installment-status');


        // Obtén la fecha de pago de la cuota desde el atributo data y formatea la fecha
        var fechaPago = cuota.getAttribute('data-last-payment-date');
        // console.log(fechaPago);

        // Obtén la fecha actual y formatea la fecha
        var fechaActual = cuota.getAttribute('data-current-date');

        if ((estadoCuotaAnterior === 'PAGADA' || estadoCuotaAnterior === 'ABONADA' || estadoCuotaAnterior === 'MORA') && fechaPago == fechaActual) {
            cuota.classList.add('u-hidden'); // Oculta el elemento
            cuota.classList.remove('c-card__box-mannager'); // Remueve la clase c-card__box-mannager
        } else  {
            cuota.classList.add('u-block');
        }
        // console.log(cuota);
    });
    
     // Función para cambiar el ícono del botón btn-ocultar
    if(document.querySelector('.js-btn-ocultar')){
        document.querySelector('.js-btn-ocultar').addEventListener('click', function () {


            // Obtener el ícono del botón
            var icono = document.querySelector('.js-icono-ocultar');

            // Cambiar la clase del ícono dependiendo del estado del botón
            if (icono.classList.contains('bi-eye')) {
                icono.classList.remove('bi-eye');
                icono.classList.add('bi-eye-slash');
            } else {
                icono.classList.remove('bi-eye-slash');
                icono.classList.add('bi-eye');
            }

            // Lógica para mostrar u ocultar elementos aquí...
        });
    }
   
});

document.addEventListener('DOMContentLoaded', function() {
    // Obtenemos todos los elementos con la clase c-card__box-mannager
    var cards = document.querySelectorAll('.u-hidden');

    // Iteramos sobre cada tarjeta
    cards.forEach(function(card) {
        // Obtenemos los datos necesarios de la tarjeta
        var previousInstallmentStatus = card.getAttribute('data-previous-installment-status');
        var installmentStatus = card.getAttribute('data-installment-status');
        var dueDate = new Date(card.getAttribute('data-due-date'));
        var today = new Date();

        // Removemos cualquier clase existente en la tarjeta
        card.classList.remove('c-card__box-mannager--pendiente', 'c-card__box-mannager--mora', 'c-card__box-mannager--abonada', 'c-card__box-mannager--pagada');

        // Aplicamos la clase correspondiente según la lógica
        if (installmentStatus === 'PENDIENTE' && 0 == 1) {
            card.classList.add('c-card__box-mannager');
        } else if (previousInstallmentStatus === 'MORA') {
            card.classList.add('c-card__box-mannager--mora');
        } else if (previousInstallmentStatus === 'ABONADA') {
            card.classList.add('c-card__box-mannager--abonada');
        } else if (previousInstallmentStatus === 'PAGADA') {
            card.classList.add('c-card__box-mannager--pagada');
        }
    });

    var cerrarCajaForms = document.querySelectorAll('.js-cerrar-caja');
    cerrarCajaForms.forEach(function(form) {
      

    });

    document.querySelectorAll('.js-eye-button').forEach(function(element) {
    element.addEventListener('click', function() {
        element.classList.toggle('c-btn--closed');
        document.querySelectorAll('.js-eye-icon').forEach(function(icon) {
        icon.classList.toggle('bi-eye');
        icon.classList.toggle('bi-eye-slash');
        });
    });
    });
});

// Esperamos a que el documento esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {
    // Obtenemos todos los elementos <li> que representan las tarjetas de cliente
    var cards = document.querySelectorAll('.c-card__box-mannager');

    // Iteramos sobre cada tarjeta
    cards.forEach(function(card) {
        // Obtenemos el estado de la cuota de la tarjeta
        var installmentStatus = card.getAttribute('data-installment-status');

        // Si el estado de la cuota es "PENDIENTE", ocultamos los elementos relevantes
        if (installmentStatus === 'PENDIENTE') {
            card.querySelectorAll('.hidden').forEach(function(hiddenElement) {
                hiddenElement.classList.add('u-hidden'); // Agregamos la clase 'hidden' para ocultarlos
            });
        } else {
            // Si el estado de la cuota no es "PENDIENTE", aseguramos que los elementos relevantes estén visibles
            card.querySelectorAll('.hidden').forEach(function(hiddenElement) {
                hiddenElement.classList.remove('u-hidden'); // Removemos la clase 'hidden' para mostrarlos
            });
        }
    });
});

document.addEventListener("keyup", e=>{


    if (e.target.matches("#searcher")){

  
        if (e.key ==="Escape")e.target.value = ""
        
        document.querySelectorAll(".search-card").forEach(payment =>{

            const searchValue = e.target.value.toLowerCase()

            if (searchValue.length > 2 && payment.textContent.toLowerCase().includes(searchValue)) {
                payment.classList.add("c-card__box-mannager");      
            } else {
                payment.classList.add("filter");
                payment.classList.remove("c-card__box-mannager");
            }

            if(searchValue.length === 0){
                payment.classList.remove("filter");
                payment.classList.add("c-card__box-mannager"); 
            }
        })

        document.querySelectorAll(".search-salesman-card").forEach(payment =>{
  
            if (payment.textContent.toLowerCase().includes(e.target.value.toLowerCase())) {
                payment.classList.remove("filter");   
            } else {
                payment.classList.add("filter");
            }
        })
  
    }
  })

  document.getElementById('photo').addEventListener('change', function() {
    checkImageFilled();
});

function checkImageFilled() {
    var photoInput = document.getElementById('photo');
    var submitButton = document.querySelector('button[type="submit"]');
    
    if (photoInput.files.length > 0) {
        submitButton.removeAttribute('disabled');
    } else {
        submitButton.setAttribute('disabled', 'disabled');
    }
}