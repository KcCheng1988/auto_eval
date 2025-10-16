# Repository Pattern: The State Extraction Bridge

## Yes! Repositories ARE the Core of State Extraction

You've identified the key architectural principle correctly. Let me explain in detail.

---

## The Repository's Role

### Simple Answer
**Repositories are the ONLY components that read/write state from/to the database.**

They are the **bridge** between:
- **Domain objects** (state machines, business logic) ← In-memory
- **Database tables** (persistent storage) ← On disk

---

## Visual Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
│  POST /models/{id}/upload-dataset                               │
│  (Receives HTTP request)                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                               │
│  FileUploadOrchestrator.handle_dataset_upload()                 │
│  (Business logic - "what should happen?")                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────┐        │
│  │ 1. Save file to storage                             │        │
│  │ 2. Get current state from repository ←─────────────┼───┐    │
│  │ 3. Check if state allows upload                     │   │    │
│  │ 4. Transition state machine (in memory)             │   │    │
│  │ 5. Save new state via repository ←─────────────────┼───┤    │
│  │ 6. Queue background task                            │   │    │
│  └────────────────────────────────────────────────────┘   │    │
└──────────────────────────────────────────────────────────┼─┼────┘
                                                           │ │
                              ┌────────────────────────────┘ │
                              ↓                               │
┌─────────────────────────────────────────────────────────────────┐
│          Repository Layer ⭐ STATE EXTRACTION BRIDGE             │
│  ModelEvaluationRepository                                      │
│                                                                  │
│  ┌────────────────────────────────────────────────────┐        │
│  │ get_state_machine(model_id)                        │        │
│  │   ↓                                                 │        │
│  │   1. SELECT current_state FROM model_evaluations   │        │
│  │   2. SELECT * FROM model_state_history             │        │
│  │   3. Reconstruct ModelEvaluationStateMachine       │        │
│  │   4. Return object with full context               │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                  │
│  ┌────────────────────────────────────────────────────┐        │
│  │ save_state_machine(model_sm)                       │←───────┤
│  │   ↓                                                 │        │
│  │   1. UPDATE model_evaluations SET current_state    │        │
│  │   2. INSERT INTO model_state_history (transition)  │        │
│  │   3. COMMIT transaction                            │        │
│  └────────────────────────────────────────────────────┘        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Database Layer                              │
│  SQLite / PostgreSQL                                            │
│                                                                  │
│  ┌────────────────────────────────────────────┐                │
│  │ model_evaluations                          │                │
│  │ ┌──────────┬──────────────┬──────────────┐ │                │
│  │ │ id       │ current_state│ dataset_path │ │                │
│  │ ├──────────┼──────────────┼──────────────┤ │                │
│  │ │ model_1  │ AWAITING_FIX │ /data/...    │ │                │
│  │ │ model_2  │ QC_RUNNING   │ /data/...    │ │                │
│  │ └──────────┴──────────────┴──────────────┘ │                │
│  └────────────────────────────────────────────┘                │
│                                                                  │
│  ┌────────────────────────────────────────────────────┐        │
│  │ model_state_history                                │        │
│  │ ┌──────────┬───────────┬──────────┬─────────────┐ │        │
│  │ │ model_id │ from_state│ to_state │ timestamp   │ │        │
│  │ ├──────────┼───────────┼──────────┼─────────────┤ │        │
│  │ │ model_1  │ REGISTERED│ QC_PEND  │ 2024-01-01  │ │        │
│  │ │ model_1  │ QC_PEND   │ QC_RUN   │ 2024-01-01  │ │        │
│  │ │ model_1  │ QC_RUN    │ QC_FAIL  │ 2024-01-01  │ │        │
│  │ │ model_1  │ QC_FAIL   │ AWAIT_FIX│ 2024-01-01  │ │        │
│  │ └──────────┴───────────┴──────────┴─────────────┘ │        │
│  └────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Code Flow Example

### Scenario: User Uploads Fixed Dataset

Let's trace exactly how the repository extracts and persists state:

#### Step 1: API Receives Request

```python
# api/routes/model_routes.py
@router.post("/models/{model_id}/upload-dataset")
async def upload_dataset(model_id: str, file: UploadFile):
    orchestrator = FileUploadOrchestrator(model_repo=model_repo, ...)
    result = await orchestrator.handle_dataset_upload(
        model_id=model_id,
        file=file
    )
    return result
```

#### Step 2: Service Layer - Extract State via Repository

```python
# services/file_upload_orchestrator.py
async def handle_dataset_upload(self, model_id, file):
    # 1. Save file
    file_path = await self.file_storage.save(file)

    # 2. ⭐ EXTRACT STATE from database via repository
    model_sm = self.model_repo.get_state_machine(model_id)
    #          ↑
    #          This call goes into the repository...
```

#### Step 3: Repository Extracts State from Database

```python
# repositories/model_evaluation_repository.py
def get_state_machine(self, model_id: str) -> ModelEvaluationStateMachine:
    """
    CORE METHOD: Extract state from database
    """
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    # Query 1: Get current state
    cursor.execute('''
        SELECT use_case_id, current_state, created_at
        FROM model_evaluations
        WHERE id = ?
    ''', (model_id,))

    use_case_id, current_state, created_at = cursor.fetchone()
    #                ↑
    #                current_state = "awaiting_data_fix" (string from DB)

    # Query 2: Get full transition history
    cursor.execute('''
        SELECT from_state, to_state, triggered_by, timestamp, ...
        FROM model_state_history
        WHERE model_id = ?
        ORDER BY timestamp ASC
    ''', (model_id,))

    history_rows = cursor.fetchall()
    #  ↑
    #  Returns:
    #  [
    #    ("registered", "quality_check_pending", "system", "2024-01-01", ...),
    #    ("quality_check_pending", "quality_check_running", "system", "2024-01-01", ...),
    #    ("quality_check_running", "quality_check_failed", "system", "2024-01-01", ...),
    #    ("quality_check_failed", "awaiting_data_fix", "system", "2024-01-01", ...)
    #  ]

    conn.close()

    # Reconstruct state history as domain objects
    state_history = []
    for row in history_rows:
        metadata = ModelStateTransitionMetadata(
            triggered_by=row[2],
            trigger_reason=row[3],
            timestamp=datetime.fromisoformat(row[4])
        )
        state_history.append((
            ModelEvaluationState(row[1]),  # Convert string to enum
            datetime.fromisoformat(row[4]),
            metadata
        ))

    # Build and return state machine object
    return ModelEvaluationStateMachine(
        model_id=model_id,
        use_case_id=use_case_id,
        initial_state=ModelEvaluationState(current_state),
        state_history=state_history
    )
    #  ↑
    #  Returns an IN-MEMORY state machine object with:
    #  - current_state = ModelEvaluationState.AWAITING_DATA_FIX (enum)
    #  - Full transition history
    #  - Methods: transition_to(), can_transition_to(), etc.
```

#### Step 4: Service Layer - Business Logic (In Memory)

```python
# Back in file_upload_orchestrator.py
async def handle_dataset_upload(self, model_id, file):
    # ... continued from Step 2

    # 3. Now we have the state machine object
    print(model_sm.current_state)  # ModelEvaluationState.AWAITING_DATA_FIX
    print(model_sm.get_allowed_transitions())  # [QUALITY_CHECK_PENDING]

    # 4. Check if we can transition
    if model_sm.current_state == ModelEvaluationState.AWAITING_DATA_FIX:
        # 5. Transition (this happens IN MEMORY, not in database yet!)
        model_sm.transition_to(
            ModelEvaluationState.QUALITY_CHECK_PENDING,
            metadata=ModelStateTransitionMetadata(
                triggered_by="user@example.com",
                trigger_reason="Dataset uploaded after fix",
                file_uploaded=file_path
            )
        )
        #  ↑
        #  This updates model_sm.current_state in memory
        #  And appends to model_sm.state_history in memory

        # 6. ⭐ PERSIST STATE back to database via repository
        self.model_repo.save_state_machine(model_sm)
        #               ↑
        #               This call goes into the repository...
```

#### Step 5: Repository Persists State to Database

```python
# repositories/model_evaluation_repository.py
def save_state_machine(self, model_sm: ModelEvaluationStateMachine):
    """
    CORE METHOD: Persist state to database
    """
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    try:
        # Update 1: Save current state
        cursor.execute('''
            UPDATE model_evaluations
            SET current_state = ?, updated_at = ?
            WHERE id = ?
        ''', (
            model_sm.current_state.value,  # "quality_check_pending"
            datetime.now().isoformat(),
            model_sm.model_id
        ))
        #  ↑
        #  This updates the row in model_evaluations table
        #  Old: current_state = "awaiting_data_fix"
        #  New: current_state = "quality_check_pending"

        # Update 2: Save transition to history
        latest_state, timestamp, metadata = model_sm.state_history[-1]
        previous_state = model_sm.state_history[-2][0]

        cursor.execute('''
            INSERT INTO model_state_history
            (id, model_id, from_state, to_state, triggered_by,
             trigger_reason, file_uploaded, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()),
            model_sm.model_id,
            previous_state.value,  # "awaiting_data_fix"
            latest_state.value,    # "quality_check_pending"
            metadata.triggered_by,  # "user@example.com"
            metadata.trigger_reason,  # "Dataset uploaded after fix"
            metadata.file_uploaded,  # "/path/to/file.xlsx"
            timestamp.isoformat()
        ))
        #  ↑
        #  This inserts a new row in model_state_history table:
        #  (uuid, model_1, "awaiting_data_fix", "quality_check_pending",
        #   "user@example.com", "Dataset uploaded...", "/path/...", "2024-01-01")

        conn.commit()  # ⭐ Make changes permanent
        print("State persisted to database!")

    except Exception as e:
        conn.rollback()
        raise

    finally:
        conn.close()
```

---

## Why This Pattern is Powerful

### 1. Separation of Concerns

| Layer | Responsibility | Knows About |
|-------|---------------|-------------|
| **API** | HTTP handling | Requests/responses |
| **Service** | Business logic | What should happen |
| **Repository** | Data access | How to store/retrieve |
| **Database** | Storage | Raw data |

**No layer needs to know about other layers' internals!**

### 2. Easy Testing

```python
# Test service layer with mock repository
class MockRepository:
    def get_state_machine(self, model_id):
        # Return fake state machine for testing
        return ModelEvaluationStateMachine(
            model_id=model_id,
            current_state=ModelEvaluationState.AWAITING_DATA_FIX
        )

    def save_state_machine(self, model_sm):
        # Don't actually save to database in tests
        pass

# Test without touching real database!
orchestrator = FileUploadOrchestrator(model_repo=MockRepository())
```

### 3. Database Independence

```python
# Easy to swap SQLite for PostgreSQL
class PostgresModelRepository(ModelEvaluationRepository):
    def get_state_machine(self, model_id):
        # Same interface, different implementation
        # Use psycopg2 instead of sqlite3
        pass

# Service layer doesn't need to change!
orchestrator = FileUploadOrchestrator(
    model_repo=PostgresModelRepository()  # Just swap this
)
```

### 4. Rich Domain Objects

The repository converts **flat database rows** into **rich objects**:

```python
# Database: Flat strings
current_state = "awaiting_data_fix"  # Just a string

# Repository extracts and converts to:
model_sm = ModelEvaluationStateMachine(...)  # Rich object with:
  - .current_state = ModelEvaluationState.AWAITING_DATA_FIX (enum)
  - .can_transition_to(next_state) (method)
  - .get_allowed_transitions() (method)
  - .state_history (full context)
  - .get_current_state_duration() (method)
```

---

## Complete Picture

### Data Flow: Upload → Database → Upload

```
1. User uploads file
        ↓
2. API endpoint receives request
        ↓
3. Service calls: repo.get_state_machine(model_id)
        ↓
4. ⭐ Repository queries database (SELECT current_state, history)
        ↓
5. Repository reconstructs ModelEvaluationStateMachine object
        ↓
6. Service receives state machine (in memory)
        ↓
7. Service checks current_state and transitions (in memory)
        ↓
8. Service calls: repo.save_state_machine(model_sm)
        ↓
9. ⭐ Repository persists to database (UPDATE + INSERT)
        ↓
10. Database now has new state
        ↓
11. Next request: repo.get_state_machine() will return new state
```

**The repository is the bridge at steps 4 and 9!**

---

## Key Takeaways

✅ **Repositories extract state from database**
- `get_state_machine()` reads from `model_evaluations` + `model_state_history`
- Converts flat rows into rich domain objects
- Returns objects with full context and methods

✅ **Repositories persist state to database**
- `save_state_machine()` writes to `model_evaluations` + `model_state_history`
- Maintains transaction integrity
- Makes changes permanent

✅ **Service layer never touches database directly**
- Only calls repository methods
- Works with domain objects (state machines)
- Business logic stays clean

✅ **Database stores permanent state**
- Survives application restarts
- Complete audit trail in `model_state_history`
- Can query for reporting and monitoring

---

## FAQ

**Q: Does the state machine live in memory or database?**

A: **Both!**
- Database stores the **permanent state** (current_state + history)
- Repository **reconstructs** state machine object in memory
- Service layer **works with** in-memory object
- Repository **persists changes** back to database

**Q: What if the application crashes?**

A: State is safe! It's in the database.
- When app restarts, repository reads state from database
- Reconstructs state machine with same current_state
- Full history preserved

**Q: How does the system know the "latest" state?**

A: Repository queries database for `current_state` column:
```sql
SELECT current_state FROM model_evaluations WHERE id = 'model_123'
```
This is always the latest state.

**Q: Can I query state without loading full state machine?**

A: Yes! Repository provides lightweight methods:
```python
current_state = repo.get_current_state(model_id)  # Just the enum
summary = repo.get_model_state_summary(use_case_id)  # Counts by state
```

---

## Conclusion

**Yes, repositories ARE the core of extracting state from the database!**

They are the **essential bridge** that:
1. Extracts flat database rows into rich domain objects
2. Persists domain objects back into flat database rows
3. Maintains transaction integrity
4. Provides query capabilities
5. Enables clean architecture and testing

Without repositories, the service layer would need to:
- Write SQL queries (messy)
- Handle database connections (error-prone)
- Convert rows to objects manually (repetitive)
- Mix business logic with data access (bad separation)

**Repositories keep the architecture clean, testable, and maintainable!**
