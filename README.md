# Dulce Rebaño - Proyecto Final IDGS

---

## Documento Final
[Ver documento](/Entrega%20Proyecto%20Final.pdf)

---

## Copia de seguridad BD
[Ver documento](/DulceRebanioSecurityCopy.sql)

---
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

# Flujo de trabajo para clientes

1. Lo primero que siempre saldra a cualquier usuario al entrar a la pagina, es la pagina de incio, donde se podran visualizar todos los productos de la tienda, así como la opcion de poder iniciar sesion o registrarse

![Página de inicio de sesión](static/img/sc1.png)
![Página de inicio de sesión](static/img/sc2.png)

2. El cliente podra ver todos los productos mas no podra hacer pedidos, para ello tendra que iniciar sesion, una vez inicie sesion podra acceder al modulo de pedidos

![Página de inicio de sesión](static/img/sc4.png)

en el cual podra hacer pedidos de los productps que quiera, siempre y cuando esten dentro del liminte, sino se le pedira que elija una fecha mas alejada para poder producir su pedido

![Página de inicio de sesión](static/img/sc5.png)

3. por ultimo el cliente podra ver el estado de sus ordenes así como el historial de sus pedidos

![Página de inicio de sesión](static/img/sc6.png)

4. al final, todos estos pedidos apareceran en el apartado de pedidos del lado administrativo, los cuales solo podran ser atendidos por el vendedor de la tienda

![Página de inicio de sesión](static/img/sc9.png)


---

# Flujo de trabajo para Empleados

1. Una vez se haya iniciado sesion, el sistema redirigira al empleado a su respectivo modulo dependiendo de a cuales tiene acceso

![Página de inicio de sesión](static/img/sc24.png)
![Página de inicio de sesión](static/img/sc25.png)
![Página de inicio de sesión](static/img/sc26.png)

2. Se mostrara el flujo con el acceso a todos los modulos para mas facilidad, para empezar, podemos empezar en el modulo de ```Ventas```, en el modulo de ventas se realizan las ventas a los clientes de todos los productos disponibles en el inventario, desde productos a granel (galletas sueltas vendidas por pieza) hasta productos en paquete (que serian presentaciones de 700gr y 1Kg)

![Página de inicio de sesión](static/img/sc7.png)

3. una vez agregados al ticket de venta se podra confirmar la venta de mostrador, mostrando una ventana en la cual el empleado ingresara la cantidad de dinero recibida y se le mostrara el cambio a dar, así como tambien tendra las opciones de ofrecer descuento y la opcion de imprimir el ticket de venta

![Página de inicio de sesión](static/img/sc8.png)

4. una vez pasado a venta, se puede pasar a ```Produccion```, el cual es el modulo donde se muestran todos los productos terminados, resaltando entre estos los que estan proximos a caducar o agotarse, tambien es donde se transforman los insumos en producto terminado, en este modulo se podran crear lotes de producto en base a las recetas que haya creadas en el ``` Modulo de Recetas ```

![Página de inicio de sesión](static/img/sc10.png)

ademas de poder crear diferentes presentaciones de los productos en base a los lotes que haya disponibles en el inventario

![Página de inicio de sesión](static/img/sc12.png)

así mismo permitiendo mermar producto ya sea caduco o que se perdio por que se cayo o cualquier causa que sea motivo de merma

![Página de inicio de sesión](static/img/sc11.png)

5. Ahora pasando al modulo de ```Recetas``` se podran visualizar todas las recetas creadas por la tienda, en la que se podran ver su precio, insumos y cantidades en la receta, y la imagen de la receta para su presentacion

![Página de inicio de sesión](static/img/sc13.png)

en este modulo se podran crear nuevas recetas a como solicite la tienda, Crearemos por ejemplo tartitas de Piña

![Página de inicio de sesión](static/img/sc14.png)

despues le agregamos los insumos que va a consumir esta receta así como su imagen de presentacion

![Página de inicio de sesión](static/img/sc16.png)

6. Pero nos falto algo importante! como hacemos tartitas de piña sin mermelada de piña? para ellos iremos a nuestro apartado de ```insumos``` en el cual podremos registrar un insumo nuevo con algun proveedor que tengamos (o en su defecto registrar un proveedor nuevo en el modulo de ```proveedores``` para despues venir y registrar ese insumo a ese provedor)

![Página de inicio de sesión](static/img/sc17.png)

7. pero aun no tenemos como tal el insumo, aun no nos deja hacer el lote de galletas en produccion, para ello tendremos que solicitar producto a nuestro proveedor, o sea hacer una compra de insumos a el proveedor, en este caso le vamos a comprar 5kg de mermelada de Piña a el proveedor

![Página de inicio de sesión](static/img/sc18.png)

8. Una vez hecha la compra del insumo, podemos terminar la receta, ahora si con la mermelada de Piña

![Página de inicio de sesión](static/img/sc27.png)
![Página de inicio de sesión](static/img/sc28.png)

9. y una vez terminada la Receta podemos regresar al modulo de ```Produccion``` para producir de este lote de galletas

![Página de inicio de sesión](static/img/sc29.png)
![Página de inicio de sesión](static/img/sc30.png)

10. una vez proucido el lote de galletas con la nueva receta, podremos comprobar el gasto de insumos que tenia agregada la receta

![Página de inicio de sesión](static/img/sc31.png)
![Página de inicio de sesión](static/img/sc32.png)

11. y de la misma forma podremos verlo reflejado en el modulo de ventas, en el cual ya podremos vender el nuevo lote de ```Tartitas de Piña```

![Página de inicio de sesión](static/img/sc33.png)
   
13. y vemos como este se ve tambien afectado en todos los modulos, estando ya presente en el DashBoard con las ventas de la nueva receta

![Página de inicio de sesión](static/img/sc34.png)

14. así mismo como tambien los clientes podran ver al momento la nueva receta de ```Tartitas de Piña``` y hacer pedidos de esta nueva receta

![Página de inicio de sesión](static/img/sc35.png)
![Página de inicio de sesión](static/img/sc36.png)

















