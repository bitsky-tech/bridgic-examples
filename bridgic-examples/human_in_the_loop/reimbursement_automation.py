"""
This example demonstrates how to use the Bridgic framework to create a reimbursement automation script that can process reimbursements. This script is automatically triggered by the enterprise's OA system and requires approval before the reimbursement can be completed.

Before running this example, you need to execute the following commands to set up the environment variables:
Run this example with uv:

```shell
uv run human_in_the_loop/reimbursement_automation.py
"""

import os
import tempfile
from httpx import delete
from pydantic import BaseModel
from datetime import datetime
from bridgic.core.automa import GraphAutoma, worker, Snapshot
from bridgic.core.automa.args import From
from bridgic.core.automa.interaction import Event, InteractionFeedback, InteractionException

class ReimbursementRecord(BaseModel):
    request_id: int
    employee_id: int
    employee_name: str
    reimbursement_month: str
    reimbursement_amount: float
    description: str
    created_at: datetime
    updated_at: datetime

class AuditResult(BaseModel):
    request_id: int
    passed: bool
    audit_reason: str

class ReimbursementWorkflow(GraphAutoma):
    @worker(is_start=True)
    async def load_record(self, request_id: int):
        """
        The reimbursement workflow can be triggered by the OA system — for instance, when an employee submits a new reimbursement request. Each request is uniquely identified by a `request_id`, which is then used to retrieve the corresponding reimbursement record from the database. 
        """
        # Load the data from database.
        return await self.load_record_from_database(request_id)
    
    @worker(dependencies=["load_record"])
    async def audit_by_rules(self, record: ReimbursementRecord):
        """
        This method simulates the logic for automatically determining whether a reimbursement request complies with business rules.  

        Typical reasons for a reimbursement request failing the audit include:

        - Unusually large individual amounts
        - Excessive total amounts within a month
        - Expenses that do not meet reimbursement policies
        - Missing or invalid supporting documents
        - Duplicate submissions
        - Other non-compliant cases
        """
        if record.reimbursement_amount > 2500:
            return AuditResult(
                request_id=record.request_id,
                passed=False,
                audit_reason="The reimbursement amount {record.reimbursement_amount} exceeds the limit of 2500."
            )
        # TODO: Add more audit rules here.
        ...

        return AuditResult(
            request_id=record.request_id,
            passed=True,
            audit_reason="The reimbursement request passed the audit."
        )
    
    @worker(dependencies=["audit_by_rules"])
    async def execute_payment(self, result: AuditResult, record: ReimbursementRecord = From("load_record")):
        if not result.passed:
            print(f"The reimbursement request {record.request_id} failed the audit. Reason: {result.audit_reason}")
            return False
        
        # The reimbursement request {record.request_id} has passed the audit rules. Requesting approval from the manager...
        # human-in-the-loop: request approval from the manager.
        event = Event(
            event_type="request_approval",
            data={
                "reimbursement_record": record,
                "audit_result": result
            }        
        )
        feedback: InteractionFeedback = self.interact_with_human(event)
        if feedback.data == "yes":
            await self.lanuch_payment_transaction(record.request_id)
            print(f"The reimbursement request {record.request_id} has been approved. Payment transaction launched.")
            return True

        print(f"!!!The reimbursement request {record.request_id} has been rejected. Payment transaction not launched.\nRejection info:\n {feedback.data}")
        return False

    async def load_record_from_database(self, request_id: int):
        # Simulate a database query...
        return ReimbursementRecord(
            request_id=request_id,
            employee_id=888888,
            employee_name="John Doe",
            reimbursement_month="2025-10",
            reimbursement_amount=1024.00,
            description="Hotel expenses for a business trip",
            created_at=datetime(2025, 10, 11, 10, 0, 0),
            updated_at=datetime(2025, 10, 11, 10, 0, 0)
        )
    async def lanuch_payment_transaction(self, request_id: int):
        # Simulate a payment execution...
        ...

async def main():
    reimbursement_workflow = ReimbursementWorkflow()
    try:
        await reimbursement_workflow.arun(request_id=123456)
    except InteractionException as e:
        # The `ReimbursementWorkflow` instance has been paused and serialized to a snapshot.
        interaction_id = e.interactions[0].interaction_id
        record = e.interactions[0].event.data["reimbursement_record"]
        # Save the snapshot to the database.
        db_context = await save_snapshot_to_database(e.snapshot)
        print("The `ReimbursementWorkflow` instance has been paused and serialized to a snapshot.")
        print("The snapshot has been persisted to database.")

    print("Waiting for the manager's approval (It may take long time) ...")
    human_feedback = input(
        "\n"
        "---------- Message to User ------------\n"
        "A reimbursement request has been submitted and audited by the system.\n"
        "Please check the details and give your approval or rejection.\n"

        "Reimbursement Request Details:\n"
        f"\n{record.model_dump_json(indent=4)}\n"
        "If you approve the request, please input 'yes'.\n"
        "Otherwise, please input 'no' or the reason for rejection.\n"
        "Your input: "
        )

    # Load the snapshot from the database.
    snapshot = await load_snapshot_from_database(db_context)
    # Deserialize the `ReimbursementWorkflow` instance from the snapshot.
    reimbursement_workflow = ReimbursementWorkflow.load_from_snapshot(snapshot)
    print("-------------------------------------\n")
    print("The `ReimbursementWorkflow` instance has been deserialized and loaded from the snapshot. It will resume to run immediately...")
    feedback = InteractionFeedback(
        interaction_id=interaction_id,
        data=human_feedback
    )
    await reimbursement_workflow.arun(interaction_feedback=feedback)


async def save_snapshot_to_database(snapshot: Snapshot):
    # Simulate a database storage using temporary files.
    temp_dir = tempfile.TemporaryDirectory()
    bytes_file = os.path.join(temp_dir.name, "reimbursement_workflow.bytes")
    version_file = os.path.join(temp_dir.name, "reimbursement_workflow.version")
    with open(bytes_file, "wb") as f:
        f.write(snapshot.serialized_bytes)
    with open(version_file, "w") as f:
        f.write(snapshot.serialization_version)

    return {
        "bytes_file": bytes_file,
        "version_file": version_file,
        "temp_dir": temp_dir,
    }

async def load_snapshot_from_database(db_context):
    # Simulate a database query using temporary files.
    bytes_file = db_context["bytes_file"]
    version_file = db_context["version_file"]
    temp_dir = db_context["temp_dir"]

    with open(bytes_file, "rb") as f:
        serialized_bytes = f.read()
    with open(version_file, "r") as f:
        serialization_version = f.read()
    snapshot = Snapshot(
        serialized_bytes=serialized_bytes, 
        serialization_version=serialization_version
    )
    return snapshot

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

