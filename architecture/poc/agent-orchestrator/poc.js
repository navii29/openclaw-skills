/**
 * Proof of Concept: Agent Orchestrator
 * 
 * Demonstrates:
 * - Token Bucket Rate Limiting
 * - Deadlock Detection via Graph Cycle Detection
 * - Circuit Breaker Pattern
 * - Agent Lifecycle Management
 * 
 * Run: node poc.js
 */

// ============================================================================
// 1. TOKEN BUCKET RATE LIMITER
// ============================================================================

class TokenBucket {
  constructor(capacity, refillRate) {
    this.capacity = capacity;
    this.tokens = capacity;
    this.refillRate = refillRate; // tokens per second
    this.lastRefill = Date.now();
  }

  refill() {
    const now = Date.now();
    const deltaMs = now - this.lastRefill;
    const tokensToAdd = (deltaMs / 1000) * this.refillRate;
    
    this.tokens = Math.min(this.capacity, this.tokens + tokensToAdd);
    this.lastRefill = now;
  }

  async consume(tokens = 1) {
    this.refill();
    
    if (this.tokens >= tokens) {
      this.tokens -= tokens;
      return true;
    }
    
    // Calculate wait time
    const tokensNeeded = tokens - this.tokens;
    const waitMs = (tokensNeeded / this.refillRate) * 1000;
    
    if (waitMs > 5000) { // Max 5s wait
      return false;
    }
    
    await sleep(waitMs);
    return this.consume(tokens);
  }

  getStatus() {
    this.refill();
    return {
      tokens: Math.floor(this.tokens),
      capacity: this.capacity,
      utilization: ((this.capacity - this.tokens) / this.capacity * 100).toFixed(1) + '%'
    };
  }
}

// ============================================================================
// 2. DEADLOCK DETECTOR (Resource Allocation Graph)
// ============================================================================

class DeadlockDetector {
  constructor() {
    this.waitGraph = new Map(); // agentId -> Set of agents it waits for
  }

  addWaitEdge(fromAgent, toAgent) {
    if (!this.waitGraph.has(fromAgent)) {
      this.waitGraph.set(fromAgent, new Set());
    }
    this.waitGraph.get(fromAgent).add(toAgent);
    
    // Check for cycle immediately
    return this.detectCycle();
  }

  removeAgent(agentId) {
    this.waitGraph.delete(agentId);
    // Remove from all wait lists
    for (const [agent, waits] of this.waitGraph) {
      waits.delete(agentId);
      if (waits.size === 0) {
        this.waitGraph.delete(agent);
      }
    }
  }

  detectCycle() {
    const visited = new Set();
    const recursionStack = new Set();

    const dfs = (node) => {
      visited.add(node);
      recursionStack.add(node);

      const neighbors = this.waitGraph.get(node) || new Set();
      for (const neighbor of neighbors) {
        if (!visited.has(neighbor)) {
          const cycle = dfs(neighbor);
          if (cycle) return cycle;
        } else if (recursionStack.has(neighbor)) {
          // Cycle detected!
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

  extractCycle(start, end) {
    // Simple cycle extraction
    const cycle = [end];
    let current = start;
    
    while (current !== end && cycle.length < 100) {
      cycle.push(current);
      const waits = this.waitGraph.get(current);
      if (!waits) break;
      current = [...waits][0]; // Take first dependency
    }
    
    cycle.push(end);
    return cycle.reverse();
  }

  getGraphDOT() {
    let dot = 'digraph WaitGraph {\n';
    for (const [agent, waits] of this.waitGraph) {
      for (const wait of waits) {
        dot += `  "${agent}" -> "${wait}";\n`;
      }
    }
    dot += '}';
    return dot;
  }
}

// ============================================================================
// 3. CIRCUIT BREAKER
// ============================================================================

class CircuitBreaker {
  constructor(options = {}) {
    this.failureThreshold = options.failureThreshold || 5;
    this.resetTimeoutMs = options.resetTimeoutMs || 30000;
    this.halfOpenMaxCalls = options.halfOpenMaxCalls || 3;
    
    this.state = 'CLOSED'; // CLOSED | OPEN | HALF_OPEN
    this.failures = 0;
    this.successes = 0;
    this.lastFailureTime = null;
    this.halfOpenCalls = 0;
  }

  async execute(operation) {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime > this.resetTimeoutMs) {
        this.transitionTo('HALF_OPEN');
      } else {
        throw new CircuitBreakerError('Circuit is OPEN');
      }
    }

    if (this.state === 'HALF_OPEN' && this.halfOpenCalls >= this.halfOpenMaxCalls) {
      throw new CircuitBreakerError('Circuit is HALF_OPEN (max calls reached)');
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

  onSuccess() {
    this.failures = 0;
    
    if (this.state === 'HALF_OPEN') {
      this.successes++;
      if (this.successes >= this.halfOpenMaxCalls) {
        this.transitionTo('CLOSED');
      }
    }
  }

  onFailure() {
    this.failures++;
    this.lastFailureTime = Date.now();
    
    if (this.state === 'HALF_OPEN') {
      this.transitionTo('OPEN');
    } else if (this.failures >= this.failureThreshold) {
      this.transitionTo('OPEN');
    }
  }

  transitionTo(newState) {
    console.log(`  🔄 Circuit: ${this.state} → ${newState}`);
    this.state = newState;
    
    if (newState === 'CLOSED') {
      this.failures = 0;
      this.successes = 0;
      this.halfOpenCalls = 0;
    } else if (newState === 'HALF_OPEN') {
      this.halfOpenCalls = 0;
      this.successes = 0;
    }
  }

  getStatus() {
    return {
      state: this.state,
      failures: this.failures,
      successes: this.successes,
      halfOpenCalls: this.halfOpenCalls
    };
  }
}

class CircuitBreakerError extends Error {
  constructor(message) {
    super(message);
    this.name = 'CircuitBreakerError';
  }
}

// ============================================================================
// 4. RESOURCE MANAGER
// ============================================================================

class ResourceManager {
  constructor(options = {}) {
    this.quotas = new Map(); // sessionKey -> Quota
    this.usage = new Map();  // sessionKey -> Usage
    this.defaultQuota = {
      maxConcurrentAgents: options.maxConcurrentAgents || 10,
      maxSpawnDepth: options.maxSpawnDepth || 5,
      maxSubAgentsPerParent: options.maxSubAgentsPerParent || 10
    };
  }

  setQuota(sessionKey, quota) {
    this.quotas.set(sessionKey, { ...this.defaultQuota, ...quota });
    if (!this.usage.has(sessionKey)) {
      this.usage.set(sessionKey, { active: 0, byParent: new Map() });
    }
  }

  canSpawn(sessionKey, parentId = null, currentDepth = 0) {
    const quota = this.quotas.get(sessionKey) || this.defaultQuota;
    const usage = this.usage.get(sessionKey) || { active: 0, byParent: new Map() };

    // Check concurrent limit
    if (usage.active >= quota.maxConcurrentAgents) {
      return { allowed: false, reason: 'CONCURRENT_LIMIT' };
    }

    // Check depth limit
    if (currentDepth >= quota.maxSpawnDepth) {
      return { allowed: false, reason: 'DEPTH_LIMIT' };
    }

    // Check per-parent limit
    if (parentId) {
      const parentCount = usage.byParent.get(parentId) || 0;
      if (parentCount >= quota.maxSubAgentsPerParent) {
        return { allowed: false, reason: 'SUBAGENT_LIMIT' };
      }
    }

    return { allowed: true };
  }

  registerSpawn(sessionKey, agentId, parentId = null) {
    const usage = this.usage.get(sessionKey);
    if (!usage) return;

    usage.active++;
    
    if (parentId) {
      const current = usage.byParent.get(parentId) || 0;
      usage.byParent.set(parentId, current + 1);
    }
    
    console.log(`  📊 Resource Usage: ${sessionKey} = ${usage.active} active agents`);
  }

  unregisterAgent(sessionKey, agentId, parentId = null) {
    const usage = this.usage.get(sessionKey);
    if (!usage) return;

    usage.active = Math.max(0, usage.active - 1);
    
    if (parentId && usage.byParent.has(parentId)) {
      const current = usage.byParent.get(parentId);
      if (current <= 1) {
        usage.byParent.delete(parentId);
      } else {
        usage.byParent.set(parentId, current - 1);
      }
    }
  }

  getStatus(sessionKey) {
    const quota = this.quotas.get(sessionKey) || this.defaultQuota;
    const usage = this.usage.get(sessionKey) || { active: 0 };
    
    return {
      active: usage.active,
      limits: quota,
      utilization: ((usage.active / quota.maxConcurrentAgents) * 100).toFixed(1) + '%'
    };
  }
}

// ============================================================================
// 5. AGENT ORCHESTRATOR (Main Controller)
// ============================================================================

class AgentOrchestrator {
  constructor() {
    this.agents = new Map();
    this.deadlockDetector = new DeadlockDetector();
    this.resourceManager = new ResourceManager();
    this.rateLimiter = new TokenBucket(10, 2); // 10 burst, 2/sec refill
    this.circuitBreaker = new CircuitBreaker({
      failureThreshold: 3,
      resetTimeoutMs: 5000
    });
    this.executionTree = new Map();
  }

  async spawnAgent(agentId, sessionKey, options = {}) {
    const { parentId = null, depth = 0, waitFor = [] } = options;
    
    console.log(`\n🚀 Spawning agent ${agentId} (depth=${depth})`);

    // Rate limiting
    const rateAllowed = await this.rateLimiter.consume(1);
    if (!rateAllowed) {
      throw new Error('RATE_LIMITED: Too many spawn requests');
    }

    // Resource quota check
    const resourceCheck = this.resourceManager.canSpawn(sessionKey, parentId, depth);
    if (!resourceCheck.allowed) {
      throw new Error(`RESOURCE_EXHAUSTED: ${resourceCheck.reason}`);
    }

    // Deadlock detection for wait dependencies
    for (const depId of waitFor) {
      const cycle = this.deadlockDetector.addWaitEdge(agentId, depId);
      if (cycle) {
        throw new Error(`DEADLOCK_DETECTED: Cycle ${cycle.join(' → ')}`);
      }
    }

    // Circuit breaker check for spawn operation
    const agent = await this.circuitBreaker.execute(async () => {
      return this.createAgent(agentId, sessionKey, {
        parentId,
        depth,
        waitFor,
        ...options
      });
    });

    // Register in resource manager
    this.resourceManager.registerSpawn(sessionKey, agentId, parentId);
    
    // Track in execution tree
    if (parentId) {
      if (!this.executionTree.has(parentId)) {
        this.executionTree.set(parentId, []);
      }
      this.executionTree.get(parentId).push(agentId);
    }

    console.log(`  ✅ Agent ${agentId} spawned successfully`);
    return agent;
  }

  createAgent(agentId, sessionKey, config) {
    const agent = {
      id: agentId,
      sessionKey,
      status: 'RUNNING',
      createdAt: new Date(),
      config,
      children: []
    };
    
    this.agents.set(agentId, agent);
    return agent;
  }

  completeAgent(agentId, result) {
    const agent = this.agents.get(agentId);
    if (!agent) return;

    agent.status = 'COMPLETED';
    agent.completedAt = new Date();
    agent.result = result;

    // Cleanup
    this.deadlockDetector.removeAgent(agentId);
    this.resourceManager.unregisterAgent(agent.sessionKey, agentId, agent.config.parentId);
    
    console.log(`  ✓ Agent ${agentId} completed`);
  }

  failAgent(agentId, error) {
    const agent = this.agents.get(agentId);
    if (!agent) return;

    agent.status = 'FAILED';
    agent.error = error;

    // Cleanup
    this.deadlockDetector.removeAgent(agentId);
    this.resourceManager.unregisterAgent(agent.sessionKey, agentId, agent.config.parentId);
    
    console.log(`  ✗ Agent ${agentId} failed: ${error}`);
  }

  getExecutionTree(rootId) {
    const buildTree = (agentId) => {
      const agent = this.agents.get(agentId);
      if (!agent) return null;

      const children = this.executionTree.get(agentId) || [];
      return {
        id: agentId,
        status: agent.status,
        children: children.map(buildTree).filter(Boolean)
      };
    };

    return buildTree(rootId);
  }

  getStats() {
    const statuses = { RUNNING: 0, COMPLETED: 0, FAILED: 0 };
    for (const agent of this.agents.values()) {
      statuses[agent.status] = (statuses[agent.status] || 0) + 1;
    }

    return {
      totalAgents: this.agents.size,
      statuses,
      circuitBreaker: this.circuitBreaker.getStatus(),
      rateLimiter: this.rateLimiter.getStatus()
    };
  }
}

// ============================================================================
// 6. DEMONSTRATION
// ============================================================================

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function runDemo() {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  AGENT ORCHESTRATOR - PROOF OF CONCEPT');
  console.log('═══════════════════════════════════════════════════════════════\n');

  const orchestrator = new AgentOrchestrator();

  // Demo 1: Normal spawning
  console.log('📦 DEMO 1: Normal Agent Spawning');
  console.log('─────────────────────────────────');
  
  const root = await orchestrator.spawnAgent('root', 'session-1', { depth: 0 });
  const child1 = await orchestrator.spawnAgent('child-1', 'session-1', { 
    parentId: 'root', 
    depth: 1 
  });
  const child2 = await orchestrator.spawnAgent('child-2', 'session-1', { 
    parentId: 'root', 
    depth: 1 
  });
  
  await sleep(100);
  orchestrator.completeAgent('child-1', { data: 'result-1' });
  orchestrator.completeAgent('child-2', { data: 'result-2' });
  orchestrator.completeAgent('root', { data: 'final-result' });

  console.log('\n📊 Stats:', JSON.stringify(orchestrator.getStats(), null, 2));

  // Demo 2: Deadlock Detection
  console.log('\n\n🔒 DEMO 2: Deadlock Detection');
  console.log('──────────────────────────────');
  
  const orch2 = new AgentOrchestrator();
  
  try {
    const a = await orch2.spawnAgent('agent-A', 'session-2', { depth: 0 });
    const b = await orch2.spawnAgent('agent-B', 'session-2', { 
      depth: 1, 
      waitFor: ['agent-C'] // B waits for C
    });
    const c = await orch2.spawnAgent('agent-C', 'session-2', { 
      depth: 1, 
      waitFor: ['agent-B'] // C waits for B → DEADLOCK!
    });
  } catch (e) {
    console.log(`  ⚠️  Caught: ${e.message}`);
  }

  // Demo 3: Rate Limiting
  console.log('\n\n⏱️  DEMO 3: Rate Limiting');
  console.log('─────────────────────────');
  
  const orch3 = new AgentOrchestrator();
  orch3.rateLimiter = new TokenBucket(3, 1); // 3 burst, 1/sec
  
  for (let i = 0; i < 5; i++) {
    const start = Date.now();
    try {
      await orch3.spawnAgent(`rate-test-${i}`, 'session-3', { depth: 0 });
      console.log(`  spawn-${i}: ${Date.now() - start}ms`);
    } catch (e) {
      console.log(`  spawn-${i}: REJECTED (${e.message})`);
    }
  }

  // Demo 4: Resource Limits
  console.log('\n\n🚧 DEMO 4: Resource Limits');
  console.log('───────────────────────────');
  
  const orch4 = new AgentOrchestrator();
  orch4.resourceManager.setQuota('session-4', { maxConcurrentAgents: 2 });
  
  try {
    await orch4.spawnAgent('res-1', 'session-4', { depth: 0 });
    await orch4.spawnAgent('res-2', 'session-4', { depth: 0 });
    console.log('  ✓ 2 agents spawned (at limit)');
    
    await orch4.spawnAgent('res-3', 'session-4', { depth: 0 });
  } catch (e) {
    console.log(`  ⚠️  Caught: ${e.message}`);
  }

  // Demo 5: Circuit Breaker
  console.log('\n\n🔌 DEMO 5: Circuit Breaker');
  console.log('───────────────────────────');
  
  const orch5 = new AgentOrchestrator();
  let failureCount = 0;
  
  // Simulate failures
  for (let i = 0; i < 5; i++) {
    try {
      await orch5.circuitBreaker.execute(async () => {
        if (failureCount < 3) {
          failureCount++;
          throw new Error('Service Unavailable');
        }
        return 'success';
      });
      console.log(`  call-${i}: SUCCESS`);
    } catch (e) {
      console.log(`  call-${i}: ${e.message}`);
    }
  }
  
  console.log(`\n  Final Circuit State: ${orch5.circuitBreaker.state}`);

  // Demo 6: Execution Tree Visualization
  console.log('\n\n🌳 DEMO 6: Execution Tree');
  console.log('──────────────────────────');
  
  const orch6 = new AgentOrchestrator();
  await orch6.spawnAgent('root', 'session-6', { depth: 0 });
  await orch6.spawnAgent('child-A', 'session-6', { parentId: 'root', depth: 1 });
  await orch6.spawnAgent('child-B', 'session-6', { parentId: 'root', depth: 1 });
  await orch6.spawnAgent('grandchild-A1', 'session-6', { parentId: 'child-A', depth: 2 });
  await orch6.spawnAgent('grandchild-A2', 'session-6', { parentId: 'child-A', depth: 2 });
  
  const tree = orch6.getExecutionTree('root');
  console.log('  Execution Tree:');
  console.log(JSON.stringify(tree, null, 2));

  // Final Summary
  console.log('\n═══════════════════════════════════════════════════════════════');
  console.log('  DEMO COMPLETE');
  console.log('═══════════════════════════════════════════════════════════════');
}

// Run the demo
runDemo().catch(console.error);
