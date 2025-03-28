# Dulce Rebaño - Proyecto Final IDGS

## Descripción del Proyecto

**Dulce Rebaño** es un sistema de gestión para una empresa dedicada a la producción y venta de galletas. Este software permite controlar las ventas de productos, compras de materias primas y producción de galletas, asegurando un flujo eficiente en la operativa del negocio.

El sistema está desarrollado con **Python - Flask** y utiliza **MySQL** como base de datos. Se permite el uso de frameworks como **Bootstrap**, pero no se permite el uso de frameworks frontend como Vue.js. o Angular

---

## Características Principales

- **Gestión de productos:** Venta de 10 variedades de galletas en diferentes presentaciones (por pieza, Kilo y Med. Kilo).
- **Control de inventarios:** Registro y manejo de materias primas con control de mermas y fechas de caducidad.
- **Gestión de producción:** Transformación de materia prima en galletas listas para la venta con reducción automática de insumos.
- **Panel de ventas:** Registra ventas, genera tickets y permite cortes diarios.
- **Portal del cliente:** Permite a los clientes registrarse, realizar pedidos y consultar su historial de compras.
- **Seguridad robusta:** Implementación de autenticación, autorización y protección contra vulnerabilidades comunes (OWASP Top 10).

---

## Módulos del Sistema

1. **Dashboard:**
   - Ventas diarias
   - Productos y presentaciones más vendidas
2. **Manejo de usuarios:**
   - Registro, modificación y eliminación de usuarios, clientes y proveedores.
3. **Inventario de Insumos:**
   - Control de materias primas y productos terminados.
4. **Inventario de Producción:**
   - Transformación de insumos en productos finales.
   - creacion de paquetes de Kilo y Med. kilo.
5. **Ventas:**
   - Registro de ventas y generación de tickets.
   - Portal del cliente para realizar pedidos.
6. **Seguridad:**
   - Control de acceso basado en roles.
   - Validación de entradas y manejo de errores seguro.
   - Cifrado de contraseñas y autenticación con JWT.

---

## Tecnologías Utilizadas

- **Backend:** Python - Flask
- **Base de Datos:** MySQL
- **Frontend:** HTML, CSS, Bootstrap
- **Seguridad:** OWASP Top Ten Compliance
- **Control de Versiones:** GitHub

---

## Seguridad y Buenas Prácticas

Este proyecto busca seguir los siguientes estándares de seguridad:

- Uso de roles como Cliente, Ventas, Produccion y Administrador y permisos para restringir accesos.
- Cifrado de contraseñas con **hash**.
- Evita inyecciones SQL mediante **consultas parametrizadas**.
- Sanitización de entradas para prevenir **XSS e Inyección de Código**.

---

⢸⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⡷  
⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠢⣀  
⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇ Are you programming son?  
⢸⠀⠀⠀⠀ ⠖⠒⠒⠒⢤⠀⠀⠀⠀⠀⡇  
⢸⠀⠀⣀⢤⣼⣀⡠⠤⠤⠼⠤⡄⠀⠀⡇  
⢸⠀⠀⠑⡤⠤⡒⠒⠒⡊⠙⡏⠀⢀⠀⡇  
⢸⠀⠀⠀⠇⠀⣀⣀⣀⣀⢀⠧⠟⠁⠀⡇  
⢸⠀⠀⠀⠸⣀⠀⠀⠈⢉⠟⠓  
⢸⠀⠀⠀⠀⠈⢱⡖⠋⠁⠀⠀⠀⠀⠀⠀⡇  
⢸⠀⠀⠀⠀⣠⢺⠧⢄⣀⠀⠀⣀⣀⠀⠀⡇  
⢸⠀⠀⠀⣠⠃⢸⠀⠀⠈⠉⡽⠿⠯⡆  
⢸⠀⠀⣰⠁⠀⢸⠀⠀⠀⠀⠉⠉⠉⠀⠀⡇  
⢸⠀⠀⠣⠀⠀⢸⢄⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇  
⢸⠀⠀⠀⠀⠀⢸⠀⢇⠀⠀⠀⠀⠀⠀⠀⠀⡇
