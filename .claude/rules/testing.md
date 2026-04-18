# 测试规范

> 适用于测试代码的组织方式及测试接口的生命周期管理。

---

## 1. 测试隔离原则

- **测试类、测试接口、调试端点严禁接入前端代码。**
- 测试代码应仅在后端 `tests/` 目录或独立脚本中运行。
- 不得将清空数据库、生成假数据等危险操作暴露为 API 路由。

```typescript
// ❌ 严禁
const testData = await fetch('/api/test/generate-data')
const debugInfo = await fetch('/api/debug/clear-db')

// ❌ 严禁：条件编译暴露测试接口
if (process.env.NODE_ENV === 'development') {
  await fetch('/api/test/reset')
}
```

---

## 2. 前端审查中的测试相关检查点

- 搜索关键词：`/api/test`、`/api/debug`、`TestHelper`、`mockUser`
- 确保前端代码中无测试模块导入
- 确保前端只调用正式业务 API

---

## 3. 后端测试建议

- 单元测试放在 `backend/tests/` 目录
- 爬虫、调度器等 I/O 密集型模块建议写集成测试
- 测试配置使用独立的数据库或 SQLite `:memory:`
