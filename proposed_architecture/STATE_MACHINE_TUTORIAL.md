# State Machine Tutorial for Evaluation System

## 📚 Table of Contents
1. [What is a State Machine?](#what-is-a-state-machine)
2. [Why Use State Machines?](#why-use-state-machines)
3. [Basic Concepts](#basic-concepts)
4. [Simple Example](#simple-example)
5. [Evaluation System States](#evaluation-system-states)
6. [Implementation Guide](#implementation-guide)
7. [Practical Examples](#practical-examples)
8. [Common Patterns](#common-patterns)
9. [Best Practices](#best-practices)

---

## What is a State Machine?

A **state machine** is a system that can be in exactly **one state** at a time and transitions between states based on events or conditions.

### Real-World Analogies:

**Traffic Light:**
```
🔴 RED → 🟢 GREEN → 🟡 YELLOW → 🔴 RED
```
- Current state: RED
- Event: Timer expires
- Next state: GREEN

**Door:**
```
🚪 CLOSED ⇄ 🚪 OPEN
```
- Current state: CLOSED
- Event: Turn handle
- Next state: OPEN

**Order Status:**
```
📦 Placed → 📦 Shipped → 📦 Delivered
```

---

## Why Use State Machines?

### ✅ Benefits:

1. **Clarity** - Easy to understand current status
2. **Validation** - Prevent invalid transitions
3. **Tracking** - History of all state changes
4. **Debugging** - Know exactly where process failed
5. **Automation** - Trigger actions on state changes

### ❌ Without State Machine:

```python
# Messy boolean flags
is_submitted = False
is_validated = False
is_processing = False
is_completed = False
has_errors = False

# Hard to track what state we're in!
if is_submitted and not is_validated:
    # What do we do here?
    pass
```

### ✅ With State Machine:

```python
# Clear state
current_state = "VALIDATING"

# Easy to understand and control
if current_state == "VALIDATING":
    validate_data()
    transition_to("PROCESSING")
```

---

## Basic Concepts

### 1. States
**States** = Possible conditions of the system

```python
from enum import Enum

class OrderState(Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
```

### 2. Transitions
**Transitions** = Moving from one state to another

```python
# Valid transitions
PENDING → PAID
PAID → SHIPPED
SHIPPED → DELIVERED
PENDING → CANCELLED
```

### 3. Events
**Events** = Triggers that cause transitions

```python
# Events
payment_received()  # PENDING → PAID
ship_order()        # PAID → SHIPPED
confirm_delivery()  # SHIPPED → DELIVERED
```

### 4. Guards
**Guards** = Conditions that must be true for transition

```python
def can_ship(order):
    return order.is_paid and order.address_valid

if can_ship(order):
    order.state = "SHIPPED"
```

---

## Simple Example

### Example 1: Door State Machine

```python
class DoorStateMachine:
    def __init__(self):
        self.state = "CLOSED"
        self.valid_transitions = {
            "CLOSED": ["OPEN"],
            "OPEN": ["CLOSED"]
        }

    def transition(self, new_state):
        """Attempt to transition to new state"""
        if new_state in self.valid_transitions.get(self.state, []):
            print(f"✅ Transitioning: {self.state} → {new_state}")
            self.state = new_state
        else:
            print(f"❌ Invalid transition: {self.state} → {new_state}")

    def open_door(self):
        self.transition("OPEN")

    def close_door(self):
        self.transition("CLOSED")


# Usage
door = DoorStateMachine()
print(f"Initial state: {door.state}")  # CLOSED

door.open_door()    # ✅ CLOSED → OPEN
door.open_door()    # ❌ Invalid (already OPEN)
door.close_door()   # ✅ OPEN → CLOSED
```

### Example 2: Simple Order System

```python
from enum import Enum
from datetime import datetime

class OrderState(Enum):
    CART = "cart"
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"

class Order:
    def __init__(self, order_id):
        self.order_id = order_id
        self.state = OrderState.CART
        self.history = []

    def transition_to(self, new_state, notes=""):
        """Transition to new state with history tracking"""
        old_state = self.state
        self.state = new_state

        # Track history
        self.history.append({
            'from_state': old_state.value,
            'to_state': new_state.value,
            'timestamp': datetime.now().isoformat(),
            'notes': notes
        })

        print(f"Order {self.order_id}: {old_state.value} → {new_state.value}")

    def checkout(self):
        if self.state == OrderState.CART:
            self.transition_to(OrderState.PENDING, "Customer checked out")
        else:
            print(f"❌ Cannot checkout from state: {self.state.value}")

    def pay(self):
        if self.state == OrderState.PENDING:
            self.transition_to(OrderState.PAID, "Payment received")
        else:
            print(f"❌ Cannot pay from state: {self.state.value}")

    def ship(self):
        if self.state == OrderState.PAID:
            self.transition_to(OrderState.SHIPPED, "Package shipped")
        else:
            print(f"❌ Cannot ship from state: {self.state.value}")

    def deliver(self):
        if self.state == OrderState.SHIPPED:
            self.transition_to(OrderState.DELIVERED, "Package delivered")
        else:
            print(f"❌ Cannot deliver from state: {self.state.value}")

    def show_history(self):
        print(f"\n📜 Order {self.order_id} History:")
        for i, h in enumerate(self.history, 1):
            print(f"{i}. {h['from_state']} → {h['to_state']} ({h['timestamp']})")
            if h['notes']:
                print(f"   Notes: {h['notes']}")


# Usage
order = Order("ORD-001")

order.checkout()   # CART → PENDING
order.pay()        # PENDING → PAID
order.ship()       # PAID → SHIPPED
order.deliver()    # SHIPPED → DELIVERED

order.show_history()
```

**Output:**
```
Order ORD-001: cart → pending
Order ORD-001: pending → paid
Order ORD-001: paid → shipped
Order ORD-001: shipped → delivered

📜 Order ORD-001 History:
1. cart → pending (2025-01-14T...)
   Notes: Customer checked out
2. pending → paid (2025-01-14T...)
   Notes: Payment received
...
```

---

## Evaluation System States

### Our State Machine Flow:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Evaluation System States                      │
└─────────────────────────────────────────────────────────────────┘

1. TEMPLATE_GENERATION      DC creates config template
           ↓
2. TEMPLATE_SENT            Email sent to use case team
           ↓
3. AWAITING_CONFIG          Waiting for team response
           ↓
4. CONFIG_RECEIVED          Team submitted config + dataset
           ↓
5. QUALITY_CHECK_RUNNING    Running quality validation
           ↓
      ┌────┴────┐
      ↓         ↓
   ✅ PASS    ❌ FAIL
      ↓         ↓
6a. QUALITY_    6b. QUALITY_
    CHECK_          CHECK_
    PASSED          FAILED
      ↓               ↓
      ↓         7. AWAITING_
      ↓             DATA_FIX
      ↓               ↓
      ↓         (resubmit)
      ↓               ↓
      └───────────────┘
           ↓
8. EVALUATION_QUEUED        Ready for evaluation
           ↓
9. EVALUATION_RUNNING       Evaluation in progress
           ↓
10. EVALUATION_COMPLETED    Success!
           ↓
11. RESULTS_SENT            Email results to team
```

### State Definitions:

```python
from enum import Enum

class UseCaseState(Enum):
    # Initial states
    TEMPLATE_GENERATION = "template_generation"
    TEMPLATE_SENT = "template_sent"
    AWAITING_CONFIG = "awaiting_config"
    CONFIG_RECEIVED = "config_received"

    # Quality check states
    QUALITY_CHECK_RUNNING = "quality_check_running"
    QUALITY_CHECK_PASSED = "quality_check_passed"
    QUALITY_CHECK_FAILED = "quality_check_failed"
    AWAITING_DATA_FIX = "awaiting_data_fix"

    # Evaluation states
    EVALUATION_QUEUED = "evaluation_queued"
    EVALUATION_RUNNING = "evaluation_running"
    EVALUATION_COMPLETED = "evaluation_completed"
    EVALUATION_FAILED = "evaluation_failed"

    # Final states
    RESULTS_SENT = "results_sent"

    # Special states
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"
    ARCHIVED = "archived"
```

---

## Implementation Guide

### Step 1: Define Valid Transitions

```python
class UseCaseStateMachine:
    """State machine for use case lifecycle"""

    VALID_TRANSITIONS = {
        # From TEMPLATE_GENERATION
        "template_generation": ["template_sent", "cancelled"],

        # From TEMPLATE_SENT
        "template_sent": ["awaiting_config", "cancelled"],

        # From AWAITING_CONFIG
        "awaiting_config": ["config_received", "cancelled", "on_hold"],

        # From CONFIG_RECEIVED
        "config_received": ["quality_check_running", "cancelled"],

        # From QUALITY_CHECK_RUNNING
        "quality_check_running": [
            "quality_check_passed",
            "quality_check_failed"
        ],

        # From QUALITY_CHECK_PASSED
        "quality_check_passed": ["evaluation_queued"],

        # From QUALITY_CHECK_FAILED
        "quality_check_failed": ["awaiting_data_fix", "cancelled"],

        # From AWAITING_DATA_FIX
        "awaiting_data_fix": ["config_received", "cancelled"],

        # From EVALUATION_QUEUED
        "evaluation_queued": ["evaluation_running"],

        # From EVALUATION_RUNNING
        "evaluation_running": [
            "evaluation_completed",
            "evaluation_failed"
        ],

        # From EVALUATION_COMPLETED
        "evaluation_completed": ["results_sent"],

        # From EVALUATION_FAILED
        "evaluation_failed": ["evaluation_queued", "cancelled"],

        # From RESULTS_SENT
        "results_sent": ["archived"],

        # From ON_HOLD
        "on_hold": ["awaiting_config", "cancelled"],
    }

    @classmethod
    def is_valid_transition(cls, from_state, to_state):
        """Check if transition is valid"""
        valid_next_states = cls.VALID_TRANSITIONS.get(from_state, [])
        return to_state in valid_next_states

    @classmethod
    def get_next_states(cls, current_state):
        """Get all possible next states"""
        return cls.VALID_TRANSITIONS.get(current_state, [])
```

### Step 2: Create Use Case with State

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class UseCase:
    """Use case with state machine"""
    id: str
    name: str
    team_email: str
    state: str
    created_at: datetime
    updated_at: datetime
    state_history: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.state_history is None:
            self.state_history = []

    @classmethod
    def create_new(cls, name: str, team_email: str):
        """Create new use case in initial state"""
        now = datetime.now()
        use_case = cls(
            id=f"uc-{now.strftime('%Y%m%d%H%M%S')}",
            name=name,
            team_email=team_email,
            state="template_generation",
            created_at=now,
            updated_at=now,
            state_history=[]
        )

        # Record initial state
        use_case._add_to_history(
            from_state=None,
            to_state="template_generation",
            triggered_by="system",
            notes="Use case created"
        )

        return use_case

    def transition_to(self, new_state: str, triggered_by: str, notes: str = ""):
        """Transition to new state"""
        # Validate transition
        if not UseCaseStateMachine.is_valid_transition(self.state, new_state):
            raise ValueError(
                f"Invalid transition: {self.state} → {new_state}. "
                f"Valid transitions: {UseCaseStateMachine.get_next_states(self.state)}"
            )

        # Record transition
        old_state = self.state
        self.state = new_state
        self.updated_at = datetime.now()

        self._add_to_history(
            from_state=old_state,
            to_state=new_state,
            triggered_by=triggered_by,
            notes=notes
        )

        print(f"✅ {self.id}: {old_state} → {new_state}")

    def _add_to_history(self, from_state, to_state, triggered_by, notes):
        """Add transition to history"""
        self.state_history.append({
            'from_state': from_state,
            'to_state': to_state,
            'triggered_by': triggered_by,
            'notes': notes,
            'timestamp': datetime.now().isoformat()
        })

    def get_available_transitions(self):
        """Get all valid next states"""
        return UseCaseStateMachine.get_next_states(self.state)

    def show_history(self):
        """Display state transition history"""
        print(f"\n📜 State History for {self.id} ({self.name}):")
        print("=" * 70)
        for i, h in enumerate(self.state_history, 1):
            from_state = h['from_state'] or "(initial)"
            print(f"{i}. {from_state} → {h['to_state']}")
            print(f"   Triggered by: {h['triggered_by']}")
            print(f"   Time: {h['timestamp']}")
            if h['notes']:
                print(f"   Notes: {h['notes']}")
            print()
```

---

## Practical Examples

### Example 1: Happy Path (Everything Works)

```python
# Create new use case
use_case = UseCase.create_new(
    name="Customer Sentiment Analysis",
    team_email="ml-team@company.com"
)

print(f"Created: {use_case.id}")
print(f"Current state: {use_case.state}")

# DC generates template
use_case.transition_to(
    "template_sent",
    triggered_by="dc_user@company.com",
    notes="Template generated and emailed to team"
)

# Team is notified
use_case.transition_to(
    "awaiting_config",
    triggered_by="system",
    notes="Awaiting team configuration"
)

# Team submits config
use_case.transition_to(
    "config_received",
    triggered_by="ml-team@company.com",
    notes="Team submitted config and dataset via email"
)

# Run quality checks
use_case.transition_to(
    "quality_check_running",
    triggered_by="system",
    notes="Running quality validation on dataset"
)

# Quality checks pass
use_case.transition_to(
    "quality_check_passed",
    triggered_by="system",
    notes="All quality checks passed"
)

# Queue for evaluation
use_case.transition_to(
    "evaluation_queued",
    triggered_by="system",
    notes="Queued for evaluation"
)

# Run evaluation
use_case.transition_to(
    "evaluation_running",
    triggered_by="system",
    notes="Running field-based evaluation"
)

# Evaluation completes
use_case.transition_to(
    "evaluation_completed",
    triggered_by="system",
    notes="Evaluation completed successfully. Accuracy: 95.2%"
)

# Send results
use_case.transition_to(
    "results_sent",
    triggered_by="system",
    notes="Results emailed to team"
)

# Show full history
use_case.show_history()
```

### Example 2: Quality Check Fails (Needs Fix)

```python
# Create and progress to quality check
use_case = UseCase.create_new(
    name="Fraud Detection Model",
    team_email="fraud-team@company.com"
)

# ... (skip to quality check) ...

use_case.state = "quality_check_running"

# Quality check fails
use_case.transition_to(
    "quality_check_failed",
    triggered_by="system",
    notes="Quality issues found: 3 date format errors, 5 missing values"
)

# Send report to team
use_case.transition_to(
    "awaiting_data_fix",
    triggered_by="system",
    notes="Email sent with quality issues report"
)

# Team resubmits fixed data
use_case.transition_to(
    "config_received",
    triggered_by="fraud-team@company.com",
    notes="Team resubmitted fixed dataset"
)

# Run quality check again
use_case.transition_to(
    "quality_check_running",
    triggered_by="system",
    notes="Re-running quality checks"
)

# This time it passes
use_case.transition_to(
    "quality_check_passed",
    triggered_by="system",
    notes="Quality checks passed after fixes"
)

# Continue with evaluation...
```

### Example 3: Invalid Transition (Error Handling)

```python
use_case = UseCase.create_new(
    name="Test Case",
    team_email="test@company.com"
)

print(f"Current state: {use_case.state}")

# Try invalid transition
try:
    # Can't go directly from template_generation to evaluation_running
    use_case.transition_to(
        "evaluation_running",
        triggered_by="user",
        notes="Trying to skip steps"
    )
except ValueError as e:
    print(f"❌ Error: {e}")

# Check what transitions ARE valid
print(f"\n✅ Valid next states: {use_case.get_available_transitions()}")
```

---

## Common Patterns

### Pattern 1: State Guards (Conditions)

```python
class UseCase:
    # ... (previous code) ...

    def can_transition_to(self, new_state: str) -> tuple[bool, str]:
        """Check if transition is allowed with reason"""

        # Check if valid in state machine
        if not UseCaseStateMachine.is_valid_transition(self.state, new_state):
            return False, f"Invalid state transition: {self.state} → {new_state}"

        # Additional business logic checks
        if new_state == "evaluation_running":
            if not hasattr(self, 'config_file_path') or not self.config_file_path:
                return False, "Cannot start evaluation: no config file"

            if not hasattr(self, 'dataset_file_path') or not self.dataset_file_path:
                return False, "Cannot start evaluation: no dataset file"

        if new_state == "results_sent":
            if not hasattr(self, 'evaluation_results') or not self.evaluation_results:
                return False, "Cannot send results: no evaluation results available"

        return True, "Transition allowed"

    def safe_transition_to(self, new_state: str, triggered_by: str, notes: str = ""):
        """Transition with guard checks"""
        can_transition, reason = self.can_transition_to(new_state)

        if not can_transition:
            raise ValueError(f"Transition blocked: {reason}")

        self.transition_to(new_state, triggered_by, notes)
```

### Pattern 2: State Actions (Automatic Triggers)

```python
class UseCase:
    # ... (previous code) ...

    def transition_to(self, new_state: str, triggered_by: str, notes: str = ""):
        """Transition with automatic actions"""
        old_state = self.state

        # Perform transition
        self.state = new_state
        self.updated_at = datetime.now()
        self._add_to_history(old_state, new_state, triggered_by, notes)

        # Trigger actions based on new state
        self._on_state_entered(new_state)

    def _on_state_entered(self, state: str):
        """Execute actions when entering a state"""
        actions = {
            "template_sent": self._send_template_email,
            "quality_check_failed": self._send_quality_issues_email,
            "evaluation_completed": self._send_results_email,
            "awaiting_data_fix": self._notify_team_of_issues,
        }

        action = actions.get(state)
        if action:
            action()

    def _send_template_email(self):
        print(f"📧 Sending template email to {self.team_email}")

    def _send_quality_issues_email(self):
        print(f"📧 Sending quality issues report to {self.team_email}")

    def _send_results_email(self):
        print(f"📧 Sending evaluation results to {self.team_email}")

    def _notify_team_of_issues(self):
        print(f"📧 Notifying {self.team_email} about data issues")
```

### Pattern 3: Rollback/Undo

```python
class UseCase:
    # ... (previous code) ...

    def rollback_to_previous_state(self, triggered_by: str, notes: str = ""):
        """Rollback to previous state"""
        if len(self.state_history) < 2:
            raise ValueError("Cannot rollback: no previous state")

        # Get previous state (second to last in history)
        previous = self.state_history[-2]
        previous_state = previous['to_state']

        # Transition back
        self.transition_to(
            previous_state,
            triggered_by=triggered_by,
            notes=f"ROLLBACK: {notes}"
        )
```

---

## Best Practices

### ✅ DO:

1. **Keep states simple and clear**
   ```python
   # Good
   "awaiting_config"

   # Bad
   "waiting_for_configuration_from_team_after_template_sent"
   ```

2. **Validate all transitions**
   ```python
   if not is_valid_transition(current, next):
       raise ValueError(f"Invalid transition: {current} → {next}")
   ```

3. **Track history**
   ```python
   state_history.append({
       'from': old_state,
       'to': new_state,
       'timestamp': datetime.now(),
       'triggered_by': user_id
   })
   ```

4. **Use enums for states**
   ```python
   from enum import Enum

   class State(Enum):
       PENDING = "pending"
       ACTIVE = "active"
   ```

5. **Document state meanings**
   ```python
   AWAITING_CONFIG = "awaiting_config"  # Waiting for team to submit config file
   ```

### ❌ DON'T:

1. **Don't use boolean flags for states**
   ```python
   # Bad
   is_pending = True
   is_active = False
   is_completed = False

   # Good
   state = "PENDING"
   ```

2. **Don't allow arbitrary transitions**
   ```python
   # Bad
   use_case.state = "completed"  # No validation!

   # Good
   use_case.transition_to("completed")  # Validates first
   ```

3. **Don't mix state and status**
   ```python
   # Bad - mixing concepts
   state = "running_with_errors"

   # Good - separate concerns
   state = "running"
   has_errors = True
   ```

---

## Summary

### Key Concepts:

1. **State** = Current condition of the system
2. **Transition** = Moving between states
3. **Validation** = Ensuring transitions are valid
4. **History** = Tracking all state changes
5. **Guards** = Additional conditions for transitions
6. **Actions** = Automatic tasks when entering states

### Benefits:

✅ Clear understanding of system status
✅ Prevents invalid operations
✅ Easy debugging and auditing
✅ Enables automation
✅ Better user experience

### Implementation Checklist:

- [ ] Define all possible states
- [ ] Define valid transitions
- [ ] Implement validation
- [ ] Track state history
- [ ] Add guards for business logic
- [ ] Implement state actions
- [ ] Test all transitions
- [ ] Document state meanings

---

**🎉 You now understand state machines! Apply this to the evaluation system for robust workflow management.**
