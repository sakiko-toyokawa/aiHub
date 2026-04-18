# PR 审查清单

> 审查 AI Knowledge Hub 代码变更时的标准检查流程。

---

## 1. 假数据 / 硬编码检查

搜索以下关键词：

```
mock、fake、demo、test、TODO、硬编码、/api/test、/api/debug
```

**必须标记的模式：**

```typescript
// ❌ 硬编码数组/对象
const mockData = [...]
const fakeUsers = [...]
const stats = [{ label: '今日', value: '12' }]
const platforms = [{ name: 'GitHub', count: 5 }]

// ❌ 假接口
const handleSubmit = async () => {
  // TODO: 调用 API
}

// ❌ 测试接口调用
const resetData = async () => {
  await fetch('/api/test/reset-db')
}
```

---

## 2. 数据流检查

确保所有展示数据经过：

```
API 层 (client.ts) → TanStack Query → 组件渲染
```

**禁止直接赋值：**

```typescript
// ❌ 错误
debugData = [...]

// ✅ 正确
const { data } = useQuery({ queryKey: ['key'], queryFn: api.getData })
```

---

## 3. 列表渲染来源检查

```tsx
// ❌ 遍历硬编码数组
{mockUsers.map(user => <UserCard key={user.id} user={user} />)}

// ✅ 从 API 获取
{data?.items?.map(user => <UserCard key={user.id} user={user} />)}
```

---

## 4. API 调用规范检查

- [ ] 无直接 `axios.get(...)` 或 `fetch(...)` 调用（必须通过 `client.ts`）
- [ ] 请求参数与后端路由签名匹配
- [ ] 响应处理与 `interaction.md` 格式一致

---

## 5. DOM 与状态检查

- [ ] 无嵌套 `<a>` 标签
- [ ] 每个数据获取都有 loading / error / empty 状态处理
- [ ] 事件处理中需要阻止冒泡的地方使用了 `stopPropagation()`

---

## 6. 类型一致性检查

- [ ] 前端 `types/index.ts` 与后端 Schema / API 返回一致
- [ ] Props 类型有明确接口定义
- [ ] 无隐式 `any`
