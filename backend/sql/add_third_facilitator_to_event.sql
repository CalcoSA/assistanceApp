-- Ejecutar manualmente antes de iniciar el backend actualizado.
-- El tipo se infiere a partir del nombre y la empresa, igual que el segundo facilitador.
ALTER TABLE `Event`
    ADD COLUMN `thirdFacilitatorNameEvent` VARCHAR(200) NULL,
    ADD COLUMN `thirdFacilitatorCompanyEvent` VARCHAR(200) NULL,
    ADD COLUMN `thirdFacilitatorPositionEvent` VARCHAR(150) NULL;
