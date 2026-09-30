# ObraCalidad

Plataforma de gestión de calidad para empresas constructoras (Perú). Prototipo de frontend —
ver [HANDOFF.md](./HANDOFF.md) para el contexto completo antes de continuar el desarrollo.

## Stack

- [Next.js 16](https://nextjs.org) (App Router) + TypeScript
- Tailwind CSS v4
- [shadcn/ui](https://ui.shadcn.com) sobre [Base UI](https://base-ui.com) (no Radix — ver nota en HANDOFF.md)

## Requisitos

- Node.js 20+

## Instalación y ejecución

```bash
npm install
npm run dev
```

Abre [http://localhost:3000](http://localhost:3000). El login de demostración acepta cualquier
contraseña junto con un correo activo de **Configuración → Usuarios** (por ejemplo
`carlos.mendoza@constructoraandina.pe`).

## Scripts

```bash
npm run dev      # servidor de desarrollo
npm run build    # build de producción + chequeo de tipos
npm run lint     # ESLint
```

## Estado del proyecto

Este es un **prototipo sin backend**: todos los datos viven en memoria (React Context) y se
reinician al recargar la página. Es intencional para esta etapa — el objetivo fue validar el
flujo de producto y la experiencia de usuario antes de invertir en backend real.

Lee **[HANDOFF.md](./HANDOFF.md)** para la arquitectura, las decisiones de diseño, qué es
prototipo vs. qué debe reconstruirse para producción, y el roadmap sugerido.
