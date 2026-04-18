# 前端开发规范

> 适用于 `frontend/src/` 目录下的所有代码。

---

## 1. 数据获取规范

**严禁使用 Mock 数据** — 所有数据必须通过真实 API 获取。

```typescript
// ✅ 正确：使用 TanStack Query
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ['summaries', activeFilter, page],
  queryFn: async () => {
    const response = await summariesApi.list({
      platform: activeFilter === 'all' ? undefined : activeFilter,
      page,
      page_size: PAGE_SIZE,
    })
    return response
  },
})

// ❌ 错误
const mockData = [...]
const stats = [{ label: '今日抓取', value: '12' }]
const platforms = [{ name: 'GitHub', count: 5 }]
```

---

## 2. API 调用规范

所有 API 调用必须通过 `src/api/client.ts` 中的封装方法：

```typescript
// ✅ 正确
import { summariesApi, sourcesApi, configApi } from '../api/client'

const data = await summariesApi.list(params)

// ❌ 错误：直接使用 axios
import axios from 'axios'
axios.get('/api/summaries')
```

---

## 3. 状态管理规范

- **服务器状态**：TanStack Query (React Query)
- **客户端状态**：React `useState` / `useReducer`
- **禁止 Mock 状态**

```typescript
// ✅ 正确
const { data, isLoading, error } = useQuery({
  queryKey: ['config'],
  queryFn: configApi.get,
})

const mutation = useMutation({
  mutationFn: configApi.update,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['config'] })
  },
})
```

---

## 4. 组件规范

### Props 定义

```typescript
interface ComponentProps {
  summary: Summary
  index?: number
}

function Component({ summary, index = 0 }: ComponentProps) {
  // ...
}
```

### 事件处理

```typescript
// ✅ 正确：阻止事件冒泡
const handleClick = (e: React.MouseEvent) => {
  e.preventDefault()
  e.stopPropagation()
  // 执行操作
}
```

---

## 5. DOM 嵌套规范

**禁止嵌套 `<a>` 标签** — 会导致 React warning。

```tsx
// ✅ 正确：使用 button + window.open
<button onClick={() => window.open(summary.url, '_blank', 'noopener,noreferrer')}>
  <ExternalLink className="w-4 h-4" />
  <span>原文</span>
</button>

// ❌ 错误
<Link to="/">
  <a href="...">原文</a>
</Link>
```

---

## 6. 加载状态规范

所有数据获取必须处理 `loading`、`error`、`success` 三种状态：

```tsx
if (isLoading) return <LoadingSpinner />
if (error) return <ErrorMessage error={error} onRetry={refetch} />
if (!data) return <EmptyState />
return <Content data={data} />
```

---

## 7. 文件命名规范

| 类型 | 规范 |
|------|------|
| 组件文件 | PascalCase（如 `SummaryCard.tsx`） |
| 工具文件 | camelCase（如 `client.ts`） |
| 类型文件 | camelCase（如 `index.ts`） |
