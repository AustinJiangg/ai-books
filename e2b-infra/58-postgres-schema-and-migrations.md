# 58 · Postgres 模式与迁移

> Postgres 是 e2b 里唯一「进程重启不会丢」的关系型状态：租户、配额、模板、构建、暂停的沙箱都在这里。
> 本篇讲它的物理模式 —— 表、约束、索引、触发器 —— 以及这套模式怎么在不停服的前提下往前演进。
>
> **读者**：工程师、运维。
> **预备**：[第 11 篇 · 对象模型与状态机](11-object-model.md)（本篇讲物理模式，对象语义在那一篇）。
> **代码**：`packages/db/migrations/`、`packages/db/queries/`、`packages/db/pkg/`、
> `packages/db/scripts/migrator.go`、`packages/db/client/`、`packages/db/sqlc.yaml`、
> `packages/db/Makefile`、`packages/db/Dockerfile`

---

## 0. 本篇要回答的问题

1. 这套模式里有哪些表，主键与外键怎么连，哪些约束是靠索引而不是靠 `CONSTRAINT` 表达的？
2. `env_builds.status` 有七个取值，读侧却只比较四个值，这个转换发生在哪里、为什么放在数据库里？
3. 触发器在这套模式里承担了什么，为什么其中一部分后来被搬回应用层？
4. 85 个 goose 迁移是怎么在一个跑着的集群上安全应用的？migrator 容器与 api 进程之间靠什么协调？
5. sqlc 生成的查询在什么情况下开事务，什么情况下靠一条 SQL 解决？重试包装为什么不能作用在事务里？

---

## 1. 问题：一个模式要同时服务几件事

先看约束条件，再看模式为什么长成这样。

**第一，写入者不止一个进程。** api、dashboard-api、docker-reverse-proxy、template-manager 都直连同一个库，
迁移由第四个进程（migrator 容器）执行。没有「应用独占数据库」这个前提，
因此不变量必须尽量下沉到数据库自己能强制的地方 —— 外键、唯一索引、CHECK ——
而不是靠某一个服务的代码路径。

**第二，这个模式带着 Supabase 的遗产。** 用户表在 `auth.users`，不属于本仓库管辖；
`public` 下几乎每张表都 `ENABLE ROW LEVEL SECURITY`，因为同一个库还要被 dashboard 用
匿名密钥直连。这条约束在服务端代码里几乎看不见（服务端用的是超级用户连接），
但它决定了新表的写法：`packages/db/pkg/tests/db_test.go` 的 `TestRequireRowLevelSecurity`
会遍历 `pg_class`，要求 `public` 下每张表都开了 RLS、每个视图都带 `security_invoker`，
漏掉一个就红。

**第三，迁移不能停服。** 一次部署里 migrator 是 api 的前置任务，它跑完 api 才起；
老版本的 api 可能还在跑。所以模式演进只能用扩展—收缩的手法：先加可空列、
再双写、再回填、最后收紧，中间任何一步都要能被新旧两版代码同时容忍。
后面几节讲的很多「看起来绕」的写法，动机都在这里。

## 2. 表与关系

`packages/db/migrations/` 下有 85 个 goose 迁移文件，累积出的最终态可以从 sqlc 生成的
`packages/db/queries/models.go` 一次读完。这里按用途分成三组画。

### 2.1 身份、租户与配额

```mermaid
erDiagram
  AUTH_USERS {
    uuid id PK
    text email
  }
  AUTH_USERS ||--|| USERS : "trigger sync"
  AUTH_USERS ||--o{ ACCESS_TOKENS : "owns"
  AUTH_USERS ||--o{ USERS_TEAMS : "member of"
  TEAMS ||--o{ USERS_TEAMS : "has member"
  TEAMS ||--o{ TEAM_API_KEYS : "has key"
```

`auth.users` 只有 `id` 与 `email` 两列，由外部身份系统写入；本仓库只在没有它的部署里
临时建一张同名表（`packages/db/scripts/migrator.go` 的 `setupAuthSchema()`）。
`20251217000000_create_public_users_table.sql` 又加了一张 `public.users`，
主键就是 `auth.users.id` 的外键，由 `sync_insert_auth_users_to_public_users_trigger()`
与对应的 update 触发器保持同步。多这一张表的收益是 `public` 下的查询不再需要跨 schema
读一张不归自己管的表；代价是同一份身份数据存了两遍，靠触发器维持一致。

`teams` 的 `tier` 是指向 `tiers` 的文本外键，`users_teams` 是多对多成员关系，
其唯一性由索引 `usersteams_team_id_user_id` 而不是表约束表达。
`20260121175429_add_team_slug.sql` 给团队加了 `slug`，它后来成了模板别名的命名空间。

两类凭据 —— `team_api_keys`（前缀 `e2b_`）与 `access_tokens`（前缀 `sk_e2b_`）——
在 2025 年经历了一串迁移把明文列删掉：先加 `*_hash`、`*_prefix`、`*_length` 与掩码列
（`20250606204750_optimize_hashed_key_schema.sql`），再建哈希列上的唯一索引
（`20250825102440_add_hash_indexes.sql`），回填、放宽非空、最后
`20250910124212_remove_raw_keys.sql` 里两条 `DROP COLUMN` 收尾。
认证查询因此变成了一次哈希列等值查找，见
`packages/db/pkg/auth/sql_queries/teams/get_team.sql` 的 `GetTeamWithTierByAPIKey`。

团队的档位、附加包与配额视图，以及团队直接拥有的集群与卷，是另一组关系。

```mermaid
erDiagram
  TEAMS }o--|| TIERS : "tier"
  TEAMS ||--o{ ADDONS : "has addon"
  TEAMS ||--|| TEAM_LIMITS : "view row"
  TIERS ||--o{ TEAM_LIMITS : "baseline"
  ADDONS ||--o{ TEAM_LIMITS : "increment"
  TEAMS }o--o| CLUSTERS : "cluster_id"
  TEAMS ||--o{ VOLUMES : "owns"
```

配额不直接读 `tiers`。`20251011200438_create_addons_table.sql` 引入了 `addons` 表和一个
名为 `team_limits` 的**视图**：视图用 `LEFT JOIN LATERAL` 把该团队当前生效
（`valid_from <= now()` 且 `valid_to` 为空或未到）的所有 addon 求和，
加到档位基线上，输出 `concurrent_sandboxes`、`concurrent_template_builds`、
`max_vcpu`、`max_ram_mb`、`disk_mb`、`max_length_hours` 六个数。
视图带 `WITH (security_invoker=on)`，这样 RLS 按调用者而不是视图所有者判定。
sqlc 把它当成一张只读表，生成 `TeamLimit` 结构体，认证路径上的四条查询全部
`JOIN team_limits`。这个设计的收益是「给某个团队临时加并发」只需要插一行 addon，
不必新建档位；代价是每次认证都要跑一次带聚合的 LATERAL 子查询，
配额不再是可以直接缓存的静态值。

### 2.2 模板、构建与快照

```mermaid
erDiagram
  ENV_ALIASES }o--|| ENVS : "alias of"
  TEAMS ||--o{ ENVS : "owns"
  ENVS ||--o{ ENV_BUILD_ASSIGNMENTS : "assigns"
  ENV_BUILDS ||--o{ ENV_BUILD_ASSIGNMENTS : "as tag"
  ENVS ||--o| SNAPSHOTS : "snapshot env"
  TEAMS ||--o{ SNAPSHOTS : "owns"
  ENVS ||--o| SNAPSHOT_TEMPLATES : "promoted"
```

命名有历史包袱：**模板在数据库里叫 `envs`，构建叫 `env_builds`**。

`envs` 的主键是 20 字符的文本 ID，带 `team_id`、`public`、`spawn_count`、`last_spawned_at`，
以及 `source` 列（`template` / `snapshot` / `snapshot_template`，见
`20260210120001_add_env_and_build_source_columns.sql`）。`source` 是把三类语义完全不同的
对象塞进同一张表之后的区分手段：几乎所有面向用户的模板查询都要带上
`e.source IN ('template', 'snapshot_template')`，漏掉这个条件就会把暂停沙箱产生的
内部模板也列出来。

`env_build_assignments` 是 `20251218160000_allow_m_n_builds_with_tags.sql` 引入的多对多边，
带 `tag` 与 `source` 两列。在此之前 `envs.build_id` 让一个模板只能指向一个构建；
之后一个模板可以同时有 `default`、`v2` 等多个 tag 各指向不同构建，
同一个构建也能被多个模板引用 —— 后者直接决定了删除模板时要多做一次检查，
`queries/builds/get_exclusive_builds_for_template_deletion.sql` 用
`NOT EXISTS (... other_eba.env_id != @template_id)` 只挑出「仅属于本模板」的构建，
共享的构建留着不删。

这张表上的唯一索引是**部分索引**：`uq_legacy_assignments` 只在
`source IN ('trigger', 'migration')` 时生效，`source = 'app'` 的行不受限制。
这是迁移期的产物 —— 触发器与回填程序写入的行需要幂等，应用写入的行需要允许重复 tag。

`env_aliases` 的主键换过一次。`20260127120000_add_env_aliases_uuid_pkey.sql` 先并发建出
`(alias, namespace)` 上带 `NULLS NOT DISTINCT` 的唯一索引，再加 `id UUID` 列，
最后在一条 `ALTER TABLE` 里同时 `DROP CONSTRAINT env_aliases_pkey` 与
`ADD CONSTRAINT ... PRIMARY KEY (id)`。`NULLS NOT DISTINCT` 是关键：老数据的
`namespace` 为 NULL，若按默认语义 NULL 互不相等，同名老别名就能重复插入。

`snapshots` 每行对应一个 `sandbox_id`（`20251009170758_unique_snapshots.sql` 加了唯一约束），
JSONB 的 `config` 列存 `packages/db/pkg/types/types.go` 的 `PausedSandboxConfig`。
`snapshot_templates` 记录某个快照被固化成模板时源自哪个沙箱，主键就是 `envs.id`。

### 2.3 集群与卷

`clusters` 只有 endpoint、TLS 标志、token 与 `sandbox_proxy_domain` 四个有效列；
`teams.cluster_id` 与 `envs.cluster_id` 是可空外键，为空表示本地集群。
`volumes`（`20260204185039_volumes.sql`）用 `UNIQUE (team_id, name)` 表达「团队内卷名唯一」。

## 3. 构建状态：status 与 status_group

`env_builds.status` 是文本列，历史上出现过 `pending`、`waiting`、`building`、
`snapshotting`、`uploaded`、`success`、`failed` 等取值 —— 有些是同一个阶段在不同年代的叫法。
读侧真正关心的只有四种：待开始、进行中、可用、失败。
如果每条查询都写一遍 `status IN ('ready','uploaded','success')`，
下一次增删状态值就要同时改十几处 SQL。

`20260210120002_add_status_group_column.sql` 的做法是加一列 `status_group`，
由 `BEFORE INSERT OR UPDATE OF status` 触发器 `trg_compute_status_group` 计算：

```sql
NEW.status_group := CASE
  WHEN NEW.status IN ('pending', 'waiting') THEN 'pending'
  WHEN NEW.status IN ('in_progress', 'building', 'snapshotting') THEN 'in_progress'
  WHEN NEW.status IN ('ready', 'uploaded', 'success') THEN 'ready'
  ELSE 'failed'
END;
```

两个类型在 Go 侧也是分开的：`packages/db/pkg/types/types.go` 的 `BuildStatus`
注释写明「写入用」，`BuildStatusGroup` 注释写明「读侧比较一律用这个」，
`sqlc.yaml` 把两列分别覆盖成这两个类型。查询侧的效果可以在
`queries/builds/get_inprogress_builds.sql` 与
`queries/templates/get_template_with_build_by_tag.sql` 里看到：
条件是 `b.status_group IN ('pending', 'in_progress')` 与 `eb.status_group = 'ready'`，
再也不列举原始状态。写入侧则仍写原始值，`packages/api/internal/template/register_build.go`
插入新构建时用的是 `BuildStatusWaiting`，旁边留着一条注释说明等所有消费者迁移完
再换成 `pending`。

选择触发器而不是 Postgres 12 起支持的生成列，代价与收益是这样的：生成列的表达式
不可变更，改分组规则要重写整张表；触发器可以 `CREATE OR REPLACE FUNCTION` 就地换掉，
但每行写入多一次函数调用，而且绕过触发器的批量写入（例如 `COPY` 之外的某些路径）
会写出不一致的分组（推论：这里没有 CHECK 约束保证 `status_group` 与 `status` 相符，
只有非空约束）。

## 4. 触发器：留下的与拆掉的

这套模式里的触发器分成两类。

**长期存在的**是身份侧的自动化。`20240605070918_refactor_triggers_and_policies.sql`
定义了 `post_user_signup()`：在 `auth.users` 插入后建默认团队、建 `users_teams` 行、
建一把 team API key、建一个 access token；key 与 token 的默认值由
`generate_team_api_key()` 与 `generate_access_token()` 生成。这些函数都是
`SECURITY DEFINER SET search_path = public`，属主是专门建的 `trigger_user` 角色，
配套的 RLS 策略只放开这个角色的 INSERT。把注册流程放在数据库里，收益是任何入口
（dashboard、后台脚本）建用户都会得到一致的初始状态；代价是这段业务逻辑不在任何一个
Go 服务里，改它要走迁移。

**被拆掉的**是构建赋值的同步触发器。`20251218160000` 引入 `env_build_assignments` 时，
为了让还在写 `env_builds.env_id` 的老代码继续工作，加了两个触发器：
`sync_env_build_assignment()` 在 `env_builds` 插入或更新时自动补一行 `source='trigger'`
的赋值，`validate_assignment_source_takeover()` 处理 `app` 与 `trigger` 两种来源的冲突
（应用写入时删掉遗留的触发器行，触发器写入时若已有应用行则静默返回 NULL）。
两个多月后 `20260204172712_remove_build_assignment_triggers.sql` 把它们全部删除，
理由写在注释里：应用现在直接管理赋值边。同一个迁移把 `env_builds.env_id` 的外键与
非空约束一起去掉，并加了一个方向相反的过渡触发器 `trigger_backfill_env_id` ——
新代码不再写 `env_id`，由赋值行插入时反向回填，好让老代码还能读到。

这一段是扩展—收缩的完整样例：加新表 → 双写（触发器）→ 迁移读侧 → 停止双写 →
反向兼容（回填触发器）→ 将来删列。代价是中间态里同一份事实存在两处，
且冲突消解逻辑分散在两个 PL/pgSQL 函数里；收益是全程没有一次需要老新代码同时停机。

## 5. 迁移：goose、migrator 容器与在线安全

### 5.1 goose 的约定

迁移文件名是 `<时间戳>_<名字>.sql`，内容用 `-- +goose Up` / `-- +goose Down` 分段，
含 `$$` 函数体的语句要包在 `-- +goose StatementBegin` / `StatementEnd` 里，
否则 goose 会按分号切错。已应用版本记在自定义表 `_migrations`
（`packages/db/scripts/migrator.go` 的 `trackingTable` 常量，Makefile 里也用 `-table "_migrations"`）。

85 个迁移里有 18 个带 `-- +goose NO TRANSACTION`。goose 默认把一个迁移包进事务，
而 `CREATE INDEX CONCURRENTLY`、`DROP INDEX CONCURRENTLY` 以及带 `COMMIT` 的存储过程
都不能在事务里跑，因此需要显式退出事务 —— 代价是这类迁移失败后是部分应用的，
所以它们几乎都写成 `IF NOT EXISTS` / `IF EXISTS`，可以重复执行。

Down 段是形式上的：85 个文件里有 27 个的 Down 完全为空。这套迁移实际上是单向的，
回滚靠往前再写一个迁移，不靠 `goose down`。

### 5.2 migrator 容器

`packages/db/Dockerfile` 是一个两段构建：builder 只拷 `scripts/migrator.go` 与
`migrations/`，编出一个静态二进制，运行镜像是 alpine，`ENTRYPOINT` 就是它。
镜像在 `iac/provider-gcp/nomad/jobs/api.hcl` 里作为 `db-migrator` 任务出现，
`lifecycle { hook = "prestart"; sidecar = false }` —— 它跑完并退出成功，
同组的 api 任务才启动。

`migrator.go` 里有三处值得注意：

- 连接池 `MaxConns = 4`，且 `AfterConnect` 把 `statement_timeout` 设成 3 小时。
  回填一张大表的迁移会跑很久，默认超时会把它掐断。
- `goose.WithSessionLocker(lock.NewPostgresSessionLocker())`：用 Postgres 会话级
  advisory lock 串行化。api 在多个节点上滚动部署时会同时起多个 prestart 任务，
  没有这把锁就会并发跑同一批迁移。
- 启动时若 `_migrations` 的版本低于 `authMigrationVersion`（`20000101000000`），
  就调 `setupAuthSchema()` 自建 `auth` schema、`authenticated` 角色、`auth.users` 表和
  `auth.uid()` 函数，然后直接往 `_migrations` 里插一行标记该版本已应用。
  这是给没有 Supabase 的部署准备的引导路径。

### 5.3 应用侧的版本门

迁移跑没跑，api 自己也要确认。`packages/db/client/migration.go` 的
`CheckMigrationVersion()` 读 `_migrations` 的当前版本，低于期望值就返回错误，
`packages/api/main.go` 拿到错误直接 `Fatal`。期望值不是运行时配置，而是编译期注入的：
`packages/api/Makefile` 用 `./../../scripts/get-latest-migration.sh`
（`git ls-tree` 列出 `packages/db/migrations/` 取最大时间戳）算出数字，
经 `-ldflags "-X=main.expectedMigrationTimestamp=..."` 打进二进制。
比较是单向的：版本高于期望值允许通过，这样迁移先行、应用后到的顺序是合法的。

这道门有一个隐含前提：`get-latest-migration.sh` 用 `git ls-tree HEAD` 列文件，而不是扫目录。
在没有 git 元数据的源码包里构建，脚本拿不到值，`EXPECTED_MIGRATION_TIMESTAMP` 传空串，
`main.go` 里的 `strconv.ParseInt` 失败后把期望值降级为 `0`，只记一条 warn ——
`CheckMigrationVersion()` 于是恒真，**版本门静默失效**。
离线打包的构建路径正好落在这个前提之外，
构建侧的完整说明见[第 65 篇 §4](65-build-and-release.md#4-版本号version-文件管什么)。

### 5.4 在线迁移的手法

几个反复出现的模式，都可以在具体文件里读到：

| 手法 | 用途 | 例子 |
|---|---|---|
| `CREATE INDEX CONCURRENTLY` | 建索引不阻塞写 | `20250825102440_add_hash_indexes.sql` |
| 批量回填 + `COMMIT` + `pg_sleep` | 大表回填不长事务 | `20260210120002` 的 `backfill_status_group()` |
| 键集分页游标回填 | 批次之间不重扫 | `20251218160000` 的 `migrate_env_builds_to_assignments()`，按 `(created_at, id)` 推进 |
| `CHECK ... NOT VALID` 再 `VALIDATE` | 加非空约束不全表加锁 | `20260210120002` 收紧 `status_group` |
| 部分唯一索引 | 只约束一部分行 | `uq_legacy_assignments`、`addons_idempotency_key_uidx` |

`backfill_status_group()` 的循环体是标准写法：每批 5 万行，`GET DIAGNOSTICS` 拿到影响行数，
`COMMIT` 后 `pg_sleep(10)` 再进下一批，行数为零时退出。代价是整个迁移可能跑几十分钟，
这正是 `statement_timeout` 要放到 3 小时的原因。

### 5.5 本地迁移

`packages/db/Makefile` 里 `migrate` 走 `POSTGRES_CONNECTION_STRING`，
`migrate-local` 硬编码 `postgres://postgres:postgres@localhost:5432/postgres`；
`create-migration NAME=...` 生成新文件；`status` 看已应用列表；
`generate` 先 `rm -rf queries/*.go` 再跑 `sqlc generate`。

## 6. sqlc：查询的组织

`packages/db/sqlc.yaml` 声明了三个独立的生成单元：

| 单元 | 查询目录 | 生成到 | 用途 |
|---|---|---|---|
| 应用 | `queries/**` | `queries/`，包 `queries` | 模板、构建、快照、别名、卷 |
| 认证 | `pkg/auth/sql_queries/**` | `pkg/auth/queries/`，包 `authqueries` | 团队、用户、API key、access token |
| 测试 | `pkg/testutils/*.sql` | `pkg/testutils/queries/` | 只有一条查 RLS 状态的查询 |

前两个单元的 schema 都指向 `migrations` 与 `schema` 两个目录 —— sqlc 通过静态解析全部迁移
来推断表结构，不连数据库。这带来一个限制：包在 `DO $$ ... $$` 块里的 DDL 它看不见。
`schema/sqlc_overrides.sql` 就是为此存在的，文件里只有一行
`ALTER TABLE teams ADD COLUMN slug TEXT NOT NULL;`，注释写明「这些语句不会被执行，
只给 sqlc 读」。

`overrides` 段把数据库类型钉到 Go 类型：`uuid` → `uuid.UUID`（可空则指针），
`timestamptz` → `time.Time`，`numeric` → `decimal.Decimal`，
`jsonb` → `types.JSONBStringMap`，再加上前面提到的三个 `env_builds` 列覆盖和
`snapshots.config` → `*types.PausedSandboxConfig`。

查询本身分成 45 条应用查询与 14 条认证查询（按 `-- name:` 注释统计），
其中 27 条 `:one`、20 条 `:many`、12 条 `:exec`。目录按对象分：
`queries/builds/`、`queries/snapshots/`、`queries/templates/`、`queries/template_aliases/`、
`queries/volumes/`。组织有一处漂移：`get_active_clusters.sql`、
`get_snapshots_with_cursor.sql`、`get_team_templates.sql`、`get_templatealias_by_alias.sql`
四个文件直接躺在 `queries/` 根目录，和生成出来的 `.go` 混在一起。

几个 sqlc 特性被大量使用：`sqlc.embed(t)` 把 JOIN 出来的整张表映射成一个嵌套结构体，
`sqlc.narg(tag)` 表示可空参数，`@name` 命名参数代替 `$1`。
`queries/get_snapshots_with_cursor.sql` 是它们的集中展示 —— 一条查询同时做了
别名聚合（`LEFT JOIN LATERAL` + `ARRAY_AGG`）、取每个快照最新的 ready 构建
（`JOIN LATERAL ... LIMIT 1`）、JSONB 包含匹配（`s.metadata @> @metadata`）
和 `(sandbox_started_at, sandbox_id)` 行值比较的键集分页。

## 7. 连接、事务边界与重试

### 7.1 连接建立

`packages/db/pkg/pool/main.go` 的 `New()` 是唯一的入口：解析连接串，
应用 `WithMaxConnections` / `WithMinIdle` / `WithRetryConfig` 选项，
挂上 `otelpgx.NewTracer()` 与 `otelpgx.RecordStats()`，
最后 `return retry.Wrap(pool, retryConfig), pool, nil` —— 返回两个值，
第一个是包了重试的 `types.DBTX`（交给 sqlc），第二个是裸池（用于开事务）。

各服务的池大小写死在调用点：api 是 `WithMaxConnections(40), WithMinIdle(5)`
（`packages/api/internal/handlers/store.go`），dashboard-api 是 8，
docker-reverse-proxy 是 3。认证客户端 `packages/db/pkg/auth/client.go` 还多一层：
如果传了非空的 `replicaURL`，它会另建一个只读池，`Read` 与 `Write` 两组 `Queries`
分开；否则两者指向同一个池。

文件里有一段被注释掉的 `config.ConnConfig.DefaultQueryExecMode = pgx.QueryExecModeExec`，
带 TODO 编号。注意它的位置在 `pgxpool.NewWithConfig()` 之后 ——
推论：即便直接取消注释，它也不会对已经创建好的池生效。

### 7.2 事务边界

`client.Client.WithTx()` 从裸池 `BeginTx`，返回一个新的 `Client`（其 `Queries` 绑定到
`pgx.Tx`）和这个 `Tx`。整个上游只有三处调用它：

- `packages/api/internal/template/register_build.go`：登记一次模板构建 ——
  建/更新模板、把同 tag 的未开始构建标记为失败、插入新构建、写赋值边，四步必须原子。
- `packages/api/internal/handlers/template_tags.go`：改 tag 指向。
- `packages/api/internal/handlers/volume_create.go`：建卷。

三处的写法一致：`defer tx.Rollback(ctx)` 紧跟在 `WithTx` 之后，成功路径末尾显式 `Commit`。

事务这么少，是因为多步写入的默认做法不是开事务，而是**写成一条带 CTE 的语句**。
`queries/snapshots/create_new_snapshot.sql` 的 `UpsertSnapshot` 是最极端的例子：
一条语句里四个 CTE 依次建模板行、upsert 快照行、建构建行、建赋值边，最后
`SELECT build_id, template_id`。`queries/templates/delete_template.sql` 同理，
先用 CTE 把别名缓存键捞出来，再删模板，让级联删除发生在同一条语句里。
收益是一次网络往返、隐式事务、不需要应用管回滚；代价是这类 SQL 很难读，
分支逻辑只能用 `WHERE NOT EXISTS` 和 `COALESCE` 表达 —— 上面那条查询里就有一句注释解释
「快照已存在时 new_template 的 id 为空，而 env_id 非空，所以用 `''` 占位」。

### 7.3 重试

`packages/db/pkg/retry` 用 `RetryableDBTX` 包住 `DBTX`，对 `Exec`、`Query`、`QueryRow`
三个方法做循环重试。默认配置（`DefaultConfig()`）是 5 次尝试、初始退避 100 ms、
乘数 2.0、上限 2 s，每次退避再叠 ±25% 的抖动（`calculateBackoff()`）。
每次重试写一条 warn 日志，并往当前 span 上加一个 `db.retry` 事件。

什么算可重试由 `IsRetriable()` 判定：context 取消与超时永不重试；
`pgconn.PgError` 只在连接异常类、操作员干预类，或 `TooManyConnections` 时重试；
`ConnectError`、`net.Error`、`ECONNRESET` / `ECONNREFUSED` / `EPIPE` / `io.EOF`
一律重试；兜底还有一段按错误消息子串匹配的判断。注意这个集合里**没有**序列化失败
和死锁 —— 那类错误需要重放整个事务，不是重放一条语句。

这正好对上一条重要边界：**事务内的语句不走重试**。`Queries.WithTx(tx)` 把
`db` 字段换成了 `pgx.Tx` 本身，重试包装只存在于池那一层。这是对的 ——
事务一旦进入 aborted 状态，重发同一条语句只会继续报错；而且重试不能跨越
事务的原子性边界。代价是三处事务里的语句遇到瞬时连接问题会直接失败，
由上层重试整个请求。

`QueryRow` 的重试有一处需要留心：`pgx.Row` 要到 `Scan()` 才暴露错误，
所以 `retryableRow.Scan()` 会重新执行整条 SQL。而 `:one` 类查询里包含
`INSERT ... RETURNING`（`UpsertSnapshot`、`CreateVolume` 都是），
推论：如果一条 INSERT 已经在服务端提交、响应在回程中丢失并被判成连接错误，
重放会再执行一次插入 —— 这类查询靠 `ON CONFLICT` 或唯一约束兜底，
`addons` 的 `idempotency_key` 唯一索引也属于同一类防御。

## 8. 测试：容器 + 真迁移

`packages/db/pkg/testutils/db.go` 的 `SetupDatabase()` 用 testcontainers 起一个
`postgres:16-alpine`，等待日志出现两次「ready to accept connections」，
然后 `runDatabaseMigrations()` 直接 `exec` 一句 `go tool goose -dir migrations postgres up`
（工作目录由 `git rev-parse --show-toplevel` 定位）。也就是说测试跑的是**真实迁移**，
不是某份手写的建表脚本 —— 迁移文件本身也因此每次都被验证一遍。
容器与三个客户端的清理都挂在 `t.Cleanup()` 上，`testing.Short()` 时整组跳过。

`pkg/testutils/queries.go` 提供 `CreateTestTeam` / `CreateTestTemplate` /
`CreateTestTemplateAlias` 等工厂，用 `TestsRawSQL` 直接插数据 —— 绕开 sqlc，
免得建数据本身依赖被测查询。`pkg/tests/` 下按对象分组的测试就建立在这套设施上：
构建并发数、模板删除的独占构建、别名命名空间回退、快照赋值顺序等。

## 9. ARM 适配版的差异

ARM 适配版对 `packages/db/` 只改了两个文件，模式、查询、重试逻辑一行未动：
`Dockerfile` 从两段构建改成单段 —— 直接把宿主上预编译好的 `migrator`
二进制拷进 `debian:bookworm-slim`；`Makefile` 按 `uname -m` 选平台，
镜像推到私有 registry（`$(REPOSITORY)/e2b-orchestration/db-migrator`），
并新增一个本地 `build` 目标。这是离线打包的通用做法，
详见[第 80 篇 §3](80-single-node-rpm.md#3-离线构建怎么做到)。

## 10. 小结

- Postgres 存的是配置与租户的真相，不存运行中的沙箱；模式的三条约束是多进程共享写入、
  Supabase 遗留的 RLS 与 `auth` schema、以及迁移必须在线。
- 关键不变量大多由数据库自己强制：外键、部分唯一索引（`uq_legacy_assignments`、
  `addons_idempotency_key_uidx`）、`NULLS NOT DISTINCT` 的别名唯一索引、`UNIQUE (team_id, name)`。
- 配额来自 `team_limits` 视图而非 `tiers` 表，视图把档位基线加上当前生效的 addon 增量；
  代价是每次认证都跑一次 LATERAL 聚合。
- `env_builds` 分成写侧 `status`（七个历史取值）与读侧 `status_group`（四个分组），
  由 `BEFORE` 触发器换算；所有查询条件只看分组。
- 触发器被用于两件事：注册流程的自动化（长期保留）和模式演进期的双写
  （`env_build_assignments` 的同步与校验，两个月后拆除，换成反向的回填触发器）。
- 迁移工具是 goose，版本记在 `_migrations`；migrator 是 api job 的 prestart 任务，
  靠 Postgres advisory lock 串行化，`statement_timeout` 放到 3 小时以容纳批量回填。
- api 启动时用编译期注入的期望版本号做单向校验：数据库版本低于期望即拒绝启动；
  期望值来自 `git ls-tree`，在没有 git 元数据的源码包里会退化成 0，这道门随之静默失效。
- sqlc 从迁移文件静态推断 schema，看不见 `DO $$` 块，因此有一个只给它读、不执行的
  `schema/sqlc_overrides.sql`。
- 多步写入的默认手段是带 CTE 的单条语句，显式事务只有三处；重试只包在连接池那一层，
  事务内的语句不重试。
- 85 个迁移里 27 个的 Down 为空：这套迁移实际是单向的，回滚靠往前写新迁移。

## 延伸阅读 / 下一篇

- [第 11 篇 · 对象模型与状态机](11-object-model.md)：这些表在对象层面各自是什么，
  以及沙箱为什么没有表（[§2](11-object-model.md#2-postgres-里的对象)、
  [§6](11-object-model.md#6-构建状态机)）。
- [第 16 篇 §4](16-auth-and-multitenancy.md#4-凭证的存储与哈希)：API key 与 access token
  在认证路径上怎么被使用；[§6](16-auth-and-multitenancy.md#6-tier-与配额额度在哪几步被检查)：`team_limits` 的读路径。
- [第 22 篇 §4](22-template-api.md#4-一次构建请求的两段)、[第 40 篇 §2](40-volumes-and-nfsproxy.md#2-控制面一个-volume-从哪来)：
  `envs` / `env_build_assignments` / `volumes` 的写入方。
- [第 59 篇 §1](59-clickhouse.md#1-为什么要一个列式数据库)（下一篇）：另一半持久化 —— 指标与事件为什么不进 Postgres。
- [第 62 篇 §4](62-testing.md#4-集成测试)：testcontainers 在全书测试体系中的位置。
- goose 的迁移约定：<https://github.com/pressly/goose>；sqlc 的配置参考：<https://docs.sqlc.dev/>。
