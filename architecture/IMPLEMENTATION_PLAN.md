# Implementation Plan: Agent Orchestration System

## Overview

This document provides a step-by-step plan for implementing the scalable agent orchestration architecture into OpenClaw.

**Target:** Integration with existing `sessions_spawn` and `subagents` tools  
**Timeline:** 6-7 Wochen (2 Wochen/Phase)  
**MVP:** Phase 1 + Phase 2 (4 Wochen)

---

## Phase 1: Foundation (Week 1-2)

### 1.1 Core Data Structures

**Files to Create:**
```
packages/gateway/src/orchestrator/
├── types.ts           # TypeScript interfaces
├── state-store.ts     # Agent state persistence
├── resource-manager.ts # Quota enforcement
└── index.ts           # Public API
```

**Key Types:**
```typescript
// packages/gateway/src/orchestrator/types.ts

export interface AgentInstance {
  id: string;
  agentId: string;
  requesterSessionKey: string;
  parentId?: string;
  
  status: 'PENDING' | 'SCHEDULED' | 'RUNNING' | 
          'COMPLETED' | 'FAILED' | 'TIMEOUT' | 'CANCELLED';
  
  spawnDepth: number;
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  
  config: AgentConfig;
  result?: AgentResult;
  error?: AgentError;
  
  // Resource tracking
  tokenUsage?: number;
  apiCallCount?: number;
}

export interface ResourceQuota {
  requesterSessionKey: string;
  maxConcurrentAgents: number;     // default: 10
  maxSpawnDepth: number;           // default: 5
  maxSubAgentsPerParent: number;   // default: 10
  maxTokensPerAgent: number;       // default: unlimited
  maxApiCallsPerMinute: number;    // default: 60
}
```

### 1.2 State Store Implementation

**Technology Choice:** PostgreSQL mit JSONB für Flexibilität

```typescript
// packages/gateway/src/orchestrator/state-store.ts

export class AgentStateStore {
  constructor(private db: Knex) {}

  async createAgent(agent: AgentInstance): Promise<void> {
    await this.db('agents').insert({
      id: agent.id,
      agent_id: agent.agentId,
      requester_session_key: agent.requesterSessionKey,
      parent_id: agent.parentId,
      status: agent.status,
      spawn_depth: agent.spawnDepth,
      config: JSON.stringify(agent.config),
      created_at: agent.createdAt
    });
  }

  async updateStatus(
    agentId: string, 
    status: AgentStatus,
    metadata?: Partial<AgentInstance>
  ): Promise<void> {
    await this.db('agents')
      .where({ id: agentId })
      .update({
        status,
        ...metadata,
        updated_at: new Date()
      });
  }

  async getActiveAgents(requesterSessionKey: string): Promise<AgentInstance[]> {
    return this.db('agents')
      .where({ 
        requester_session_key: requesterSessionKey 
      })
      .whereIn('status', ['PENDING', 'SCHEDULED', 'RUNNING'])
      .select('*');
  }

  async getAgentTree(rootId: string): Promise<AgentInstance[]> {
    // Recursive CTE für Baum-Abfrage
    const result = await this.db.raw(`
      WITH RECURSIVE agent_tree AS (
        SELECT * FROM agents WHERE id = ?
        UNION ALL
        SELECT a.* FROM agents a
        JOIN agent_tree at ON a.parent_id = at.id
      )
      SELECT * FROM agent_tree
    `, [rootId]);
    
    return result.rows;
  }
}
```

**Migration:**
```sql
-- migrations/001_add_agents_table.sql
CREATE TABLE agents (
  id UUID PRIMARY KEY,
  agent_id VARCHAR(255) NOT NULL,
  requester_session_key VARCHAR(255) NOT NULL,
  parent_id UUID REFERENCES agents(id),
  
  status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
  spawn_depth INTEGER NOT NULL DEFAULT 0,
  
  config JSONB NOT NULL DEFAULT '{}',
  result JSONB,
  error JSONB,
  
  token_usage INTEGER DEFAULT 0,
  api_call_count INTEGER DEFAULT 0,
  
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agents_requester ON agents(requester_session_key);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_parent ON agents(parent_id);
CREATE INDEX idx_agents_created_at ON agents(created_at);
```

### 1.3 Resource Manager

```typescript
// packages/gateway/src/orchestrator/resource-manager.ts

export class ResourceManager {
  private quotas = new Map<string, ResourceQuota>();
  private defaultQuota: ResourceQuota = {
    requesterSessionKey: '',
    maxConcurrentAgents: 10,
    maxSpawnDepth: 5,
    maxSubAgentsPerParent: 10,
    maxTokensPerAgent: Infinity,
    maxApiCallsPerMinute: 60
  };

  constructor(
    private stateStore: AgentStateStore,
    private config: OrchestratorConfig
  ) {}

  async canSpawn(
    requesterSessionKey: string,
    options: SpawnOptions
  ): Promise<ResourceCheckResult> {
    const quota = this.getQuota(requesterSessionKey);
    
    // Check concurrent limit
    const activeAgents = await this.stateStore.getActiveAgents(requesterSessionKey);
    if (activeAgents.length >= quota.maxConcurrentAgents) {
      return {
        allowed: false,
        reason: 'CONCURRENT_LIMIT_EXCEEDED',
        current: activeAgents.length,
        limit: quota.maxConcurrentAgents
      };
    }

    // Check depth limit
    if (options.spawnDepth >= quota.maxSpawnDepth) {
      return {
        allowed: false,
        reason: 'MAX_DEPTH_EXCEEDED',
        current: options.spawnDepth,
        limit: quota.maxSpawnDepth
      };
    }

    // Check per-parent limit
    if (options.parentId) {
      const siblings = activeAgents.filter(a => a.parentId === options.parentId);
      if (siblings.length >= quota.maxSubAgentsPerParent) {
        return {
          allowed: false,
          reason: 'MAX_SUBAGENTS_EXCEEDED',
          current: siblings.length,
          limit: quota.maxSubAgentsPerParent
        };
      }
    }

    return { allowed: true };
  }

  setQuota(requesterSessionKey: string, quota: Partial<ResourceQuota>): void {
    this.quotas.set(requesterSessionKey, {
      ...this.defaultQuota,
      ...quota,
      requesterSessionKey
    });
  }

  private getQuota(requesterSessionKey: string): ResourceQuota {
    return this.quotas.get(requesterSessionKey) || {
      ...this.defaultQuota,
      requesterSessionKey
    };
  }
}
```

### 1.4 Integration with sessions_spawn

**Modify:** `packages/gateway/src/tools/sessions/spawn.ts`

```typescript
export async function sessionsSpawn(
  args: SessionsSpawnArgs,
  context: ToolContext
): Promise<ToolResult {
  const orchestrator = context.orchestrator;
  
  // Pre-flight checks
  const resourceCheck = await orchestrator.resources.canSpawn(
    context.sessionKey,
    {
      parentId: context.agentId, // if spawned from another agent
      spawnDepth: context.spawnDepth || 0
    }
  );

  if (!resourceCheck.allowed) {
    return {
      status: 'error',
      error: {
        type: 'RESOURCE_EXHAUSTED',
        message: `Cannot spawn agent: ${resourceCheck.reason}`,
        details: resourceCheck
      }
    };
  }

  // Rate limiting
  const rateLimitResult = await orchestrator.rateLimiter.consume(
    context.sessionKey
  );
  
  if (!rateLimitResult.allowed) {
    return {
      status: 'error',
      error: {
        type: 'RATE_LIMITED',
        message: 'Too many spawn requests, please retry later'
      }
    };
  }

  // Create agent record
  const agentInstance = await orchestrator.createAgent({
    agentId: args.agentId,
    requesterSessionKey: context.sessionKey,
    parentId: context.agentId,
    spawnDepth: (context.spawnDepth || 0) + 1,
    config: {
      task: args.task,
      model: args.model,
      thinking: args.thinking,
      timeoutSeconds: args.timeoutSeconds,
      label: args.label,
      cleanup: args.cleanup
    }
  });

  // Proceed with actual spawn
  const spawnResult = await executeSpawn(agentInstance, args);
  
  return spawnResult;
}
```

---

## Phase 2: Reliability (Week 3-4)

### 2.1 Deadlock Detection

```typescript
// packages/gateway/src/orchestrator/deadlock-detector.ts

export class DeadlockDetector {
  private waitGraph = new Map<string, Set<string>>();

  addWaitEdge(agentId: string, waitsForId: string): string[] | null {
    if (!this.waitGraph.has(agentId)) {
      this.waitGraph.set(agentId, new Set());
    }
    this.waitGraph.get(agentId)!.add(waitsForId);
    
    return this.detectCycle();
  }

  removeAgent(agentId: string): void {
    this.waitGraph.delete(agentId);
    for (const [, waits] of this.waitGraph) {
      waits.delete(agentId);
    }
  }

  private detectCycle(): string[] | null {
    const visited = new Set<string>();
    const recursionStack = new Set<string>();

    const dfs = (node: string): string[] | null => {
      visited.add(node);
      recursionStack.add(node);

      const neighbors = this.waitGraph.get(node) || new Set();
      for (const neighbor of neighbors) {
        if (!visited.has(neighbor)) {
          const cycle = dfs(neighbor);
          if (cycle) return cycle;
        } else if (recursionStack.has(neighbor)) {
          return this.extractCycle(node, neighbor);
        }
      }

      recursionStack.delete(node);
      return null;
    };

    for (const node of this.waitGraph.keys()) {
      if (!visited.has(node)) {
        const cycle = dfs(node);
        if (cycle) return cycle;
      }
    }

    return null;
  }

  private extractCycle(start: string, end: string): string[] {
    const cycle: string[] = [end];
    let current = start;
    
    while (current !== end && cycle.length < 100) {
      cycle.push(current);
      const waits = this.waitGraph.get(current);
      if (!waits || waits.size === 0) break;
      current = [...waits][0];
    }
    
    cycle.push(end);
    return cycle.reverse();
  }
}
```

**Integration:**
```typescript
// In sessions_send or when agent waits for result
const cycle = deadlockDetector.addWaitEdge(
  currentAgentId,
  targetAgentId
);

if (cycle) {
  await orchestrator.failAgent(currentAgentId, {
    type: 'DEADLOCK_DETECTED',
    message: `Circular dependency detected: ${cycle.join(' → ')}`,
    cycle
  });
  throw new Error('Deadlock detected');
}
```

### 2.2 Circuit Breaker

```typescript
// packages/gateway/src/orchestrator/circuit-breaker.ts

export class CircuitBreaker {
  private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';
  private failures = 0;
  private successes = 0;
  private lastFailureTime?: number;
  private halfOpenCalls = 0;

  constructor(private config: CircuitBreakerConfig) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      if (Date.now() - (this.lastFailureTime || 0) > this.config.resetTimeoutMs) {
        this.transitionTo('HALF_OPEN');
      } else {
        throw new CircuitBreakerError('Circuit breaker is OPEN');
      }
    }

    if (this.state === 'HALF_OPEN' && 
        this.halfOpenCalls >= this.config.halfOpenMaxCalls) {
      throw new CircuitBreakerError('Circuit breaker HALF_OPEN limit reached');
    }

    if (this.state === 'HALF_OPEN') {
      this.halfOpenCalls++;
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failures = 0;
    
    if (this.state === 'HALF_OPEN') {
      this.successes++;
      if (this.successes >= this.config.halfOpenMaxCalls) {
        this.transitionTo('CLOSED');
      }
    }
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailureTime = Date.now();
    
    if (this.state === 'HALF_OPEN') {
      this.transitionTo('OPEN');
    } else if (this.failures >= this.config.failureThreshold) {
      this.transitionTo('OPEN');
    }
  }

  private transitionTo(newState: 'CLOSED' | 'OPEN' | 'HALF_OPEN'): void {
    logger.info(`Circuit breaker: ${this.state} → ${newState}`);
    this.state = newState;
    
    if (newState === 'CLOSED') {
      this.failures = 0;
      this.successes = 0;
      this.halfOpenCalls = 0;
    }
  }
}
```

### 2.3 Orphan Cleanup

```typescript
// packages/gateway/src/orchestrator/orphan-cleanup.ts

export class OrphanCleanup {
  constructor(
    private stateStore: AgentStateStore,
    private intervalMs: number = 60000
  ) {}

  start(): void {
    setInterval(() => this.cleanup(), this.intervalMs);
  }

  private async cleanup(): Promise<void> {
    const orphans = await this.stateStore.db('agents')
      .leftJoin('agents as parents', 'agents.parent_id', 'parents.id')
      .where(function() {
        this.where('parents.status', 'COMPLETED')
            .orWhere('parents.status', 'FAILED')
            .orWhereNull('parents.id');
      })
      .whereIn('agents.status', ['RUNNING', 'PENDING', 'SCHEDULED'])
      .select('agents.id');

    for (const orphan of orphans) {
      await this.stateStore.updateStatus(orphan.id, 'CANCELLED', {
        error: {
          type: 'ORPHANED',
          message: 'Parent agent terminated without cleanup'
        }
      });
      
      // Recursively cancel children
      await this.cancelChildren(orphan.id);
    }

    if (orphans.length > 0) {
      logger.info(`Cleaned up ${orphans.length} orphaned agents`);
    }
  }

  private async cancelChildren(parentId: string): Promise<void> {
    const children = await this.stateStore.db('agents')
      .where({ parent_id: parentId })
      .whereIn('status', ['RUNNING', 'PENDING', 'SCHEDULED'])
      .select('id');

    for (const child of children) {
      await this.stateStore.updateStatus(child.id, 'CANCELLED', {
        error: { type: 'PARENT_CANCELLED' }
      });
      await this.cancelChildren(child.id);
    }
  }
}
```

### 2.4 Retry Policies

```typescript
// packages/gateway/src/orchestrator/retry-policy.ts

export interface RetryPolicy {
  maxAttempts: number;
  backoffType: 'fixed' | 'linear' | 'exponential';
  baseDelayMs: number;
  maxDelayMs: number;
  retryableErrors: string[];
}

export async function withRetry<T>(
  operation: () => Promise<T>,
  policy: RetryPolicy,
  context: { agentId: string; logger: Logger }
): Promise<T> {
  let lastError: Error;
  
  for (let attempt = 1; attempt <= policy.maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      
      if (!isRetryable(error, policy.retryableErrors)) {
        throw error;
      }

      if (attempt === policy.maxAttempts) {
        break;
      }

      const delay = calculateDelay(attempt, policy);
      context.logger.warn(
        `Retry ${attempt}/${policy.maxAttempts} for ${context.agentId} ` +
        `after ${delay}ms: ${lastError.message}`
      );
      
      await sleep(delay);
    }
  }
  
  throw lastError!;
}

function calculateDelay(attempt: number, policy: RetryPolicy): number {
  let delay: number;
  
  switch (policy.backoffType) {
    case 'fixed':
      delay = policy.baseDelayMs;
      break;
    case 'linear':
      delay = policy.baseDelayMs * attempt;
      break;
    case 'exponential':
      delay = policy.baseDelayMs * Math.pow(2, attempt - 1);
      break;
    default:
      delay = policy.baseDelayMs;
  }
  
  return Math.min(delay, policy.maxDelayMs);
}
```

---

## Phase 3: Advanced Features (Week 5-6)

### 3.1 Priority Scheduling

```typescript
// packages/gateway/src/orchestrator/scheduler.ts

export interface ScheduledAgent {
  agentId: string;
  priority: number;  // 1-100, higher = more important
  queuedAt: Date;
  requesterSessionKey: string;
}

export class PriorityScheduler {
  private queue: ScheduledAgent[] = [];
  private processing = new Set<string>();

  enqueue(agent: ScheduledAgent): void {
    this.queue.push(agent);
    this.queue.sort((a, b) => {
      // Higher priority first, then FIFO
      if (b.priority !== a.priority) {
        return b.priority - a.priority;
      }
      return a.queuedAt.getTime() - b.queuedAt.getTime();
    });
  }

  async processNext(
    executor: (agent: ScheduledAgent) => Promise<void>
  ): Promise<void> {
    const agent = this.queue.shift();
    if (!agent) return;

    if (this.processing.has(agent.agentId)) {
      return; // Already processing
    }

    this.processing.add(agent.agentId);
    
    try {
      await executor(agent);
    } finally {
      this.processing.delete(agent.agentId);
    }
  }

  // Preemption: bump priority for critical tasks
  bumpPriority(agentId: string, newPriority: number): void {
    const agent = this.queue.find(a => a.agentId === agentId);
    if (agent) {
      agent.priority = newPriority;
      this.queue.sort((a, b) => b.priority - a.priority);
    }
  }
}
```

### 3.2 Distributed Tracing

```typescript
// packages/gateway/src/orchestrator/tracing.ts

export interface TraceSpan {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  agentId: string;
  operation: string;
  startTime: Date;
  endTime?: Date;
  tags: Record<string, string>;
  logs: Array<{ timestamp: Date; message: string }>;
}

export class Tracing {
  private spans: TraceSpan[] = [];

  startSpan(
    traceId: string,
    parentSpanId: string | undefined,
    agentId: string,
    operation: string
  ): TraceSpan {
    const span: TraceSpan = {
      traceId,
      spanId: generateId(),
      parentSpanId,
      agentId,
      operation,
      startTime: new Date(),
      tags: {},
      logs: []
    };
    
    this.spans.push(span);
    return span;
  }

  finishSpan(spanId: string): void {
    const span = this.spans.find(s => s.spanId === spanId);
    if (span) {
      span.endTime = new Date();
    }
  }

  getTraceTree(traceId: string): TraceSpan[] {
    return this.spans
      .filter(s => s.traceId === traceId)
      .sort((a, b) => a.startTime.getTime() - b.startTime.getTime());
  }
}
```

### 3.3 Metrics & Monitoring

```typescript
// packages/gateway/src/orchestrator/metrics.ts

export class OrchestratorMetrics {
  constructor(private prometheus: PrometheusClient) {}

  recordSpawn(requester: string, depth: number): void {
    this.prometheus.counter('agent_spawns_total', {
      requester,
      depth: depth.toString()
    }).inc();
  }

  recordCompletion(
    agentId: string,
    durationMs: number,
    status: AgentStatus
  ): void {
    this.prometheus.histogram('agent_duration_seconds')
      .observe(durationMs / 1000);
    
    this.prometheus.counter('agent_completions_total', {
      status
    }).inc();
  }

  recordResourceExhaustion(reason: string): void {
    this.prometheus.counter('agent_resource_exhaustion_total', {
      reason
    }).inc();
  }

  recordDeadlock(cycleLength: number): void {
    this.prometheus.counter('agent_deadlocks_detected_total').inc();
    this.prometheus.histogram('agent_deadlock_cycle_length')
      .observe(cycleLength);
  }

  setActiveAgents(count: number): void {
    this.prometheus.gauge('agent_active_count').set(count);
  }
}
```

---

## Phase 4: Production Hardening (Week 6-7)

### 4.1 Load Testing

```typescript
// tests/load/orchestrator.load.ts

describe('Orchestrator Load Tests', () => {
  it('should handle 100 concurrent agents', async () => {
    const promises = Array(100).fill(0).map((_, i) =>
      orchestrator.spawnAgent(`load-test-${i}`, 'session-load', { depth: 0 })
    );
    
    const results = await Promise.allSettled(promises);
    const succeeded = results.filter(r => r.status === 'fulfilled').length;
    
    expect(succeeded).toBeGreaterThan(90); // 90% success rate
  });

  it('should handle spawn depth of 5', async () => {
    let current = null;
    for (let i = 0; i < 5; i++) {
      current = await orchestrator.spawnAgent(
        `depth-${i}`,
        'session-depth',
        { parentId: current?.id, depth: i }
      );
    }
    
    // 6th should fail
    await expect(
      orchestrator.spawnAgent('depth-6', 'session-depth', {
        parentId: current.id,
        depth: 5
      })
    ).rejects.toThrow('MAX_DEPTH_EXCEEDED');
  });

  it('should detect deadlocks under load', async () => {
    const createCircularDependency = async () => {
      const a = await orchestrator.spawnAgent('dl-a', 'session-dl');
      const b = await orchestrator.spawnAgent('dl-b', 'session-dl', {
        waitFor: ['dl-c']
      });
      
      await expect(
        orchestrator.spawnAgent('dl-c', 'session-dl', {
          waitFor: ['dl-b']
        })
      ).rejects.toThrow('DEADLOCK_DETECTED');
    };
    
    // Run multiple concurrent deadlock tests
    await Promise.all(Array(10).fill(0).map(createCircularDependency));
  });
});
```

### 4.2 Chaos Engineering

```typescript
// tests/chaos/orchestrator.chaos.ts

export class OrchestratorChaos {
  constructor(private orchestrator: AgentOrchestrator) {}

  async killRandomAgents(percentage: number): Promise<number> {
    const agents = await this.orchestrator.getActiveAgents();
    const toKill = agents.filter(() => Math.random() < percentage);
    
    for (const agent of toKill) {
      await this.orchestrator.failAgent(agent.id, {
        type: 'CHAOS_INJECTED',
        message: 'Random failure injected by chaos monkey'
      });
    }
    
    return toKill.length;
  }

  async delayRandomAgents(
    percentage: number,
    delayMs: number
  ): Promise<void> {
    const agents = await this.orchestrator.getActiveAgents();
    
    for (const agent of agents) {
      if (Math.random() < percentage) {
        await this.orchestrator.delayAgent(agent.id, delayMs);
      }
    }
  }

  async simulateNetworkPartition(
    requesterSessionKeys: string[]
  ): Promise<void> {
    // Simulate network isolation
    for (const sessionKey of requesterSessionKeys) {
      await this.orchestrator.isolateSession(sessionKey);
    }
    
    // Heal after 30s
    await sleep(30000);
    
    for (const sessionKey of requesterSessionKeys) {
      await this.orchestrator.restoreSession(sessionKey);
    }
  }
}
```

### 4.3 Runbooks

**File:** `docs/runbooks/agent-orchestrator.md`

```markdown
# Agent Orchestrator Runbook

## Alerts

### HighAgentFailureRate
- **Condition**: > 20% agent failures in 5min window
- **Severity**: P2
- **Runbook**:
  1. Check circuit breaker status: `GET /debug/circuit-breakers`
  2. Review recent errors in logs: `k logs -l app=gateway | grep ERROR`
  3. If circuit breakers tripped, check downstream services
  4. Consider manual circuit reset if issue resolved

### DeadlockDetected
- **Condition**: Any deadlock detected
- **Severity**: P2
- **Runbook**:
  1. Identify cycle from alert: `cycle: [agent-a, agent-b, agent-c]`
  2. Check agent details: `GET /debug/agents/{agentId}`
  3. If false positive, whitelist pattern in config
  4. Review agent code for circular dependencies

### ResourceExhaustion
- **Condition**: > 50% spawn requests rejected
- **Severity**: P3
- **Runbook**:
  1. Check active agent count: `GET /debug/metrics`
  2. Review quota configuration
  3. Consider temporary quota increase for critical sessions
  4. Identify resource hogs: `GET /debug/top-agents`

## Common Commands

```bash
# List active agents
openclaw debug agents --status=RUNNING

# Kill stuck agent
openclaw debug agent kill {agentId} --reason="manual-cleanup"

# Reset circuit breaker
openclaw debug circuit-breaker reset {serviceName}

# View execution tree
openclaw debug tree {rootAgentId}
```
```

---

## Migration Strategy

### Backwards Compatibility

```typescript
// Feature flag for gradual rollout
export const ORCHESTRATOR_FEATURES = {
  // Phase 1
  RESOURCE_LIMITS: process.env.ORCH_RESOURCE_LIMITS === 'true',
  
  // Phase 2
  DEADLOCK_DETECTION: process.env.ORCH_DEADLOCK_DETECTION === 'true',
  CIRCUIT_BREAKER: process.env.ORCH_CIRCUIT_BREAKER === 'true',
  
  // Phase 3
  PRIORITY_SCHEDULING: process.env.ORCH_PRIORITY_SCHEDULING === 'true',
  DISTRIBUTED_TRACING: process.env.ORCH_TRACING === 'true'
};
```

### Rollout Plan

1. **Week 1**: Deploy Phase 1 with `RESOURCE_LIMITS=false` (monitoring only)
2. **Week 2**: Enable limits for 10% of traffic
3. **Week 3**: Deploy Phase 2, enable for 10%
4. **Week 4**: Ramp up to 50%
5. **Week 5**: Deploy Phase 3
6. **Week 6**: 100% rollout with all features

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Spawn Success Rate | ~95% | > 99% | 24h window |
| Deadlock Incidents | Unknown | 0 detected | Weekly |
| Orphaned Agents | Manual cleanup | Auto-cleanup < 60s | Real-time |
| Avg Spawn Latency | ~500ms | < 100ms | P99 |
| Resource Exhaustion | ~5%/day | < 0.1%/day | Daily |

---

## Appendix

### Configuration Reference

```yaml
# config/orchestrator.yaml
orchestrator:
  resources:
    defaults:
      maxConcurrentAgents: 10
      maxSpawnDepth: 5
      maxSubAgentsPerParent: 10
      maxApiCallsPerMinute: 60
    
    overrides:
      - sessionKey: "agent:main:*"
        maxConcurrentAgents: 50  # Higher limit for main sessions
      
      - sessionKey: "cron:*"
        maxSpawnDepth: 3  # Stricter for cron jobs

  circuitBreaker:
    failureThreshold: 5
    resetTimeoutMs: 30000
    halfOpenMaxCalls: 3

  deadlock:
    checkIntervalMs: 5000
    maxCycleLength: 100

  cleanup:
    orphanCheckIntervalMs: 60000
    zombieTimeoutMs: 120000
```

**Dokument erstellt:** 2026-02-26  
**Version:** 1.0 - Production Implementation Plan
