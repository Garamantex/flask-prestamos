-- Tabla de auditoría (MySQL). Ejecutar si no usas Alembic.
-- Ajusta el nombre de la tabla de usuarios si en tu BD no es `user`.

CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT NOT NULL,
    created_at DATETIME NOT NULL,
    actor_user_id INT NOT NULL,
    target_user_id INT NULL,
    action VARCHAR(64) NOT NULL,
    ip_address VARCHAR(45) NULL,
    details TEXT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_audit_log_actor FOREIGN KEY (actor_user_id) REFERENCES `user` (id),
    CONSTRAINT fk_audit_log_target FOREIGN KEY (target_user_id) REFERENCES `user` (id)
);
