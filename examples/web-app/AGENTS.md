# E-Commerce Web Application - Agent Knowledge Base

## 🎯 Project Overview
**Domain**: Web Development (Next.js 14 + React 18)  
**Type**: Full-stack e-commerce platform  
**Scale**: ~50K LOC, 200+ components, 15 API routes  
**Team Size**: 8 developers

## 📁 Architecture Map

```
src/
├── app/                    # Next.js 14 App Router
│   ├── (auth)/            # Auth route group
│   ├── (shop)/            # Shopping routes
│   ├── api/               # API routes
│   └── layout.tsx         # Root layout
├── components/
│   ├── ui/                # Reusable UI components
│   ├── features/          # Feature-specific components
│   └── layouts/           # Layout components
├── lib/
│   ├── db/                # Database utilities (Prisma)
│   ├── auth/              # NextAuth.js config
│   └── utils/             # Helper functions
└── hooks/                 # Custom React hooks
```

## 🔑 Core Systems

### 1. Authentication Flow
- **Entry**: `src/app/api/auth/[...nextauth]/route.ts`
- **Provider**: NextAuth.js with JWT strategy
- **Protected Routes**: Middleware in `src/middleware.ts`
- **Session Management**: `src/lib/auth/session.ts`

### 2. Product Catalog
- **API**: `src/app/api/products/route.ts`
- **Components**: `src/components/features/ProductCard.tsx`
- **State**: React Query for server state
- **Search**: Algolia integration in `src/lib/search/`

### 3. Shopping Cart
- **State Management**: Zustand store in `src/store/cart.ts`
- **Persistence**: LocalStorage + DB sync
- **Components**: `src/components/features/Cart/`
- **Checkout Flow**: `src/app/(shop)/checkout/page.tsx`

### 4. Payment Processing
- **Integration**: Stripe API
- **Webhook**: `src/app/api/webhooks/stripe/route.ts`
- **Components**: `src/components/features/Payment/`
- **Security**: Server-side validation only

## 🛠️ Slash Commands

### /debug-hydration
**Purpose**: Fix React hydration mismatches  
**Usage**: When seeing "Hydration failed" errors  
**Checks**:
1. Server/client rendering differences
2. Date/time formatting issues
3. Random ID generation
4. Browser-only APIs in SSR

**Example**:
```bash
/debug-hydration src/components/features/ProductCard.tsx
# Analyzes: useEffect dependencies, conditional rendering, localStorage usage
```

### /trace-api-call
**Purpose**: Debug API route performance  
**Usage**: When API responses are slow  
**Traces**:
1. Database query execution time
2. External API calls (Stripe, Algolia)
3. Middleware execution
4. Response serialization

**Example**:
```bash
/trace-api-call /api/products
# Output: DB: 45ms, Algolia: 120ms, Total: 180ms
```

### /optimize-bundle
**Purpose**: Reduce JavaScript bundle size  
**Usage**: When Lighthouse scores drop  
**Analyzes**:
1. Dynamic imports usage
2. Tree-shaking opportunities
3. Duplicate dependencies
4. Image optimization

**Example**:
```bash
/optimize-bundle src/app/(shop)/products/page.tsx
# Suggests: Code splitting, lazy loading, image formats
```

### /check-accessibility
**Purpose**: Validate WCAG 2.1 compliance  
**Usage**: Before production deployment  
**Validates**:
1. Semantic HTML structure
2. ARIA labels and roles
3. Keyboard navigation
4. Color contrast ratios

## 🧩 Component Patterns

### Server Components (Default)
```typescript
// src/app/(shop)/products/page.tsx
export default async function ProductsPage() {
  const products = await db.product.findMany()
  return <ProductGrid products={products} />
}
```

### Client Components (Interactive)
```typescript
// src/components/features/AddToCart.tsx
'use client'
export function AddToCart({ productId }: Props) {
  const addItem = useCartStore(state => state.addItem)
  return <button onClick={() => addItem(productId)}>Add</button>
}
```

### Hybrid Pattern (Composition)
```typescript
// Server component wraps client component
<ProductCard product={product}>
  <AddToCart productId={product.id} />
</ProductCard>
```

## 📊 Data Flow

### Product Listing Flow
1. **Request**: User navigates to `/products`
2. **SSR**: Server fetches from Prisma DB
3. **Render**: Server component generates HTML
4. **Hydration**: Client-side React takes over
5. **Interaction**: Client components handle cart actions

### Checkout Flow
1. **Cart Review**: Client-side Zustand state
2. **Validation**: Server action validates inventory
3. **Payment**: Stripe Elements (client) → API route (server)
4. **Webhook**: Stripe confirms → Update DB
5. **Confirmation**: Redirect to success page

## 🔍 Common Issues & Solutions

### Issue: "Cannot read property of undefined"
**Location**: `src/components/features/ProductCard.tsx`  
**Cause**: Optional chaining missing on product data  
**Fix**: Add `product?.price` instead of `product.price`

### Issue: Slow initial page load
**Location**: `src/app/(shop)/layout.tsx`  
**Cause**: Loading all products in layout  
**Fix**: Move data fetching to page level, use streaming

### Issue: Cart not persisting
**Location**: `src/store/cart.ts`  
**Cause**: LocalStorage not syncing with Zustand  
**Fix**: Use `persist` middleware correctly

## 🚀 Performance Metrics

- **Lighthouse Score**: 95+ (Performance)
- **First Contentful Paint**: < 1.2s
- **Time to Interactive**: < 2.5s
- **Bundle Size**: 180KB (gzipped)
- **API Response Time**: < 200ms (p95)

## 🔐 Security Checklist

- ✅ CSRF protection via NextAuth
- ✅ SQL injection prevention (Prisma ORM)
- ✅ XSS protection (React auto-escaping)
- ✅ Rate limiting on API routes
- ✅ Secure headers (middleware)
- ✅ Environment variables for secrets

## 📚 Key Dependencies

```json
{
  "next": "14.0.0",
  "react": "18.2.0",
  "prisma": "5.0.0",
  "@tanstack/react-query": "5.0.0",
  "zustand": "4.4.0",
  "next-auth": "4.24.0",
  "stripe": "13.0.0"
}
```

## 🎓 Onboarding Guide

### Day 1: Setup
1. Clone repo and run `npm install`
2. Copy `.env.example` to `.env.local`
3. Run `npx prisma migrate dev`
4. Start dev server: `npm run dev`

### Week 1: Core Concepts
- Understand App Router vs Pages Router
- Learn Server vs Client Components
- Study the cart state management
- Review API route patterns

### Month 1: Feature Development
- Build new product features
- Optimize existing components
- Write integration tests
- Deploy to staging

---

**Last Updated**: 2026-05-01  
**Maintained By**: Frontend Team  
**Questions?**: #web-dev-help on Slack