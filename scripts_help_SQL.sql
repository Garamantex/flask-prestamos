-- Crear Usuario Administrador
INSERT INTO rutzchile.user (username, password, role, first_name, last_name, cellphone, creation_date, modification_date)
VALUES ('admin', '123456', 'ADMINISTRADOR', 'User', 'Admin', '123456789', NOW(), NOW());


-- Desactivar restricciones de clave externa
SET FOREIGN_KEY_CHECKS = 1;


UPDATE employee_record
SET closing_total = 0
WHERE id = 1;

SELECT * FROM rutzchile.client c
WHERE c.document = 252761357;


-- SELECT Todas las Tablas
SELECT * FROM rutzchile.client c;

SELECT * FROM rutzchile.concept c;

SELECT * FROM rutzchile.employee e;

SELECT * FROM rutzchile.employee_record er;

SELECT * FROM rutzchile.loan l;

SELECT * FROM rutzchile.loan_installment li;

SELECT * FROM rutzchile.manager m;

SELECT * FROM rutzchile.payment p;

SELECT * FROM rutzchile.salesman s;

SELECT * FROM rutzchile.transaction t;

SELECT * FROM rutzchile.user u;


-- Actualizar Registros Payments
UPDATE payment p
SET p.amount = 6000
WHERE p.id = 298;


UPDATE loan_installment
SET payment_date = NULL, status = 'PENDIENTE'
WHERE id = 11



UPDATE loan_installment lp
SET lp.due_date = '2024-05-11'
WHERE lp.id = 181;


-- Actualizar Registros por fecha
UPDATE payment
SET payment_date = CONCAT('2025-01-11 ', TIME(payment_date))
WHERE DATE(payment_date) = '2025-01-20';


UPDATE transaction
SET creation_date = CONCAT('2025-01-11 ', TIME(creation_date))
WHERE DATE(creation_date) = '2025-01-20';


UPDATE loan
SET creation_date = CONCAT('2025-01-11 ', TIME(creation_date))
WHERE DATE(creation_date) = '2025-01-20';


UPDATE employee_record
SET creation_date = CONCAT('2025-01-11 ', TIME(creation_date))
WHERE DATE(creation_date) = '2025-01-20';


UPDATE loan_installment
SET payment_date = '2025-01-11'
WHERE payment_date = '2025-01-20';


UPDATE loan
SET modification_date = CONCAT('2025-01-11 ', TIME(modification_date))
WHERE DATE(modification_date) = '2025-01-20' and status = 0;


-- ------------------------------------


/*
UPDATE payment
SET payment_date = CONCAT('2024-07-11 ', TIME(payment_date))
WHERE id = 330;


UPDATE payment
SET installment_id = 29
WHERE id = 381;




UPDATE loan
SET creation_date = CONCAT('2024-07-09 ', TIME(creation_date))
WHERE id = 31;



DATE(payment_date) = '2024-06-12';


UPDATE employee
SET box_value = 0
WHERE id = 2;


UPDATE employee_record
SET closing_total = 29000
WHERE id = 1;


DELETE FROM loan_installment
WHERE loan_id IN (34,35,36);


DELETE FROM payment
WHERE id =  413


-- Actualizar Registros
UPDATE client c
SET c.debtor = True
WHERE c.id = 8;

-- Actualizar Registros
UPDATE employee e
SET e.status = True
WHERE e.id = 3;


CREATE TABLE employee_record (
    id INT PRIMARY KEY AUTO_INCREMENT,
    employee_id INT NOT NULL,
    initial_state FLOAT NOT NULL,
    loans_to_collect INT NOT NULL,
    paid_installments INT NOT NULL,
    partial_installments INT NOT NULL,
    overdue_installments INT NOT NULL,
    total_collected FLOAT NOT NULL,
    sales FLOAT NOT NULL,
    renewals FLOAT NOT NULL,
    incomings FLOAT NOT NULL,
    withdrawals FLOAT NOT NULL,
    expenses FLOAT NOT NULL,
    closing_total FLOAT NOT NULL,
    creation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES Employee(id)
);



CREATE TABLE employee (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    maximum_cash NUMERIC(10, 2) NOT NULL,
    maximum_sale NUMERIC(10, 2) NOT NULL,
    maximum_expense NUMERIC(10, 2) NOT NULL,
    maximum_installments NUMERIC(10, 2) NOT NULL,
    minimum_interest NUMERIC(10, 2) NOT NULL,
    status BOOLEAN NOT NULL DEFAULT TRUE,
    percentage_interest NUMERIC(10, 2) NOT NULL,
    fix_value NUMERIC(10, 2) NOT NULL,
    creation_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modification_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(id)
);


-- Conceptos Transacciones
INSERT INTO rutzchile.concept (name, transaction_types) 
VALUES 
('Viaticos', 'GASTO'),
('Combustible', 'GASTO'),
('Facturas', 'GASTO'),
('Nomina', 'GASTO'),
('Aceite Motor', 'GASTO'),
('Pasajes', 'GASTO'),
('Moto Varios', 'GASTO'),
('Papeleria', 'GASTO'),
('Medico', 'GASTO'),
('Renta', 'GASTO'),
('Celular', 'GASTO'),
('Aporte', 'INGRESO'),
('Trabajo', 'INGRESO'),
('Venta', 'INGRESO'),
('Prestamo', 'INGRESO'),
('Caja General', 'RETIRO'),
('Ruta', 'RETIRO');


SELECT loan_installment.id 
FROM loan_installment JOIN loan ON loan.id = loan_installment.loan_id
WHERE loan.employee_id = :employee_id_1


SELECT loan_installment.id
FROM loan_installment JOIN loan ON loan.id = loan_installment.loan_id
WHERE loan.employee_id = 2 AND loan_installment.status = 'ABONADA'


SELECT loan_installment.id
FROM loan_installment JOIN loan ON loan.id = loan_installment.loan_id
WHERE loan.employee_id = 2 AND loan_installment.status = 'MORA'



-- Truncate de una tabla en MySQL
TRUNCATE TABLE rutzchile.loan_installment;
TRUNCATE TABLE rutzchile.loan;
TRUNCATE TABLE rutzchile.client;
TRUNCATE TABLE rutzchile.payment;
TRUNCATE TABLE rutzchile.transaction;
TRUNCATE TABLE rutzchile.concept;
TRUNCATE TABLE rutzchile.employee_record;
TRUNCATE TABLE rutzchile.employee;
TRUNCATE TABLE rutzchile.manager;
TRUNCATE TABLE rutzchile.salesman;
TRUNCATE TABLE rutzchile.user;



INSERT INTO employee_record (id, employee_id, initial_state, loans_to_collect, paid_installments, partial_installments, due_to_collect_tomorrow, overdue_installments, total_collected, sales, renewals, incomings, withdrawals, expenses, closing_total, creation_date)
VALUES (1, 2, 0, 24, 299000, 0, 241500, 36000, 299000, 0, 200000, 0, 70000, 0, 29000, '2024-06-18 22:00:17');
