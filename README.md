# Caprichos.Store.Ctes

**E-commerce para emprendimiento gastronómico desarrollado con Django.**

Aplicación web desarrollada para **Capricho — Boutique Empanadas & Bakery**, orientada a la gestión de productos, promociones y pedidos online.

## Funcionalidades

- Catálogo de productos organizado por categorías.
- Productos con variantes y diferentes presentaciones.
- Productos destacados.
- Combos promocionales compuestos por múltiples productos.
- Carrito de compras.
- Gestión de cantidades y variantes.
- Checkout para retiro o envío.
- Selección de fecha para el pedido.
- Confirmación de pedidos mediante WhatsApp.
- Panel de administración personalizado.
- Gestión de productos, categorías, variantes, combos y usuarios.
- Gestión de pedidos y estados.
- Administración de disponibilidad y visibilidad de productos.
- Diseño responsive para desktop y mobile.
- Gestión y personalización de imágenes del catálogo.

## Panel de administración

El proyecto incluye un panel administrativo propio que permite gestionar el contenido y la operación de la tienda sin necesidad de modificar el código.

Desde el panel se pueden administrar:

- Productos.
- Categorías.
- Variantes.
- Combos.
- Pedidos.
- Usuarios.
- Configuración del negocio.

## Sistema de combos

Los combos permiten crear productos promocionales compuestos por diferentes productos del catálogo.

Cada combo puede definir:

- Productos incluidos.
- Cantidad de cada producto.
- Precio promocional.
- Imagen.
- Descripción.
- Estado de disponibilidad.

Los combos forman parte del catálogo y pueden agregarse al carrito como cualquier otro producto.

## Gestión de pedidos

El sistema permite registrar pedidos con:

- Datos del cliente.
- Productos y variantes seleccionados.
- Cantidades.
- Precios.
- Tipo de entrega.
- Dirección de envío.
- Fecha deseada.
- Observaciones.
- Estado del pedido.

Los pedidos conservan los datos relevantes de los productos y precios utilizados al momento de realizar la compra, evitando que modificaciones posteriores del catálogo alteren el historial.

## Arquitectura

El proyecto está dividido en aplicaciones según las responsabilidades del sistema:

```text
catalogo/   → Productos, categorías, variantes y combos
pedidos/    → Carrito y gestión de pedidos
panel/      → Administración del negocio
usuarios/   → Gestión de usuarios
config/     → Configuración general del proyecto
templates/  → Interfaces HTML
static/     → CSS, JavaScript y recursos estáticos
media/      → Imágenes y archivos multimedia
```

## Tecnologías

### Backend

- Python
- Django 6.1
- Django ORM
- Django Authentication

### Frontend

- HTML5
- CSS3
- JavaScript
- Django Templates

### Base de datos

- SQLite

### Multimedia

- Pillow

## Diseño responsive

La interfaz fue desarrollada contemplando diferentes resoluciones y cuenta con una experiencia específica para dispositivos móviles.

El diseño mobile utiliza componentes y estructuras adaptadas para mejorar la navegación, visualización del catálogo y proceso de compra desde pantallas pequeñas.

## Reglas de negocio

El sistema contempla reglas específicas para la gestión de pedidos:

- Los pedidos requieren un mínimo de 1 día de anticipación.
- Se pueden seleccionar fechas de hasta 10 días de anticipación.
- Los pedidos pueden realizarse para retiro en el local o mediante envío.
- Los productos pueden configurarse como disponibles o no disponibles.
- Los productos y categorías pueden mostrarse u ocultarse según su configuración.

## Validaciones

El sistema incorpora validaciones tanto en el backend como en los formularios para controlar:

- Datos de los clientes.
- Cantidades de productos.
- Variantes.
- Fechas de pedido.
- Tipo de entrega.
- Disponibilidad de productos.
- Reglas propias del negocio.

## Ejecución

```bash
git clone https://github.com/anttobocc/Caprichos.Store.Ctes.git
cd Caprichos.Store.Ctes

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

La configuración sensible se gestiona mediante variables de entorno.

## Objetivo del proyecto

El proyecto fue desarrollado como una solución e-commerce completa para un negocio gastronómico, integrando:

**Catálogo → productos → variantes → combos → carrito → checkout → pedidos → administración**

Además de resolver las necesidades funcionales del negocio, el proyecto permitió trabajar sobre:

- Arquitectura backend.
- Modelado de datos.
- Reglas de negocio.
- Autenticación y autorización.
- Gestión de archivos e imágenes.
- Diseño responsive.
- Experiencia de usuario.
- Integración entre frontend y backend.
- Gestión de pedidos y estados.

## Autora 

**Antonella Boccalandro**

Desarrollo y diseño del proyecto.

[GitHub](https://github.com/anttobocc)
