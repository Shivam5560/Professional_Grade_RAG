import asyncio
import json
import os
import traceback
from app.utils.logger import get_logger
from app.services.messaging import get_rabbitmq_connection, publish_message

logger = get_logger(__name__)

async def process_job(message_body: dict):
    job_type = message_body.get("job_type")
    user_id = message_body.get("user_id")
    job_id = message_body.get("job_id")
    
    logger.info(f"Processing job: {job_id} of type: {job_type} for user: {user_id}")
    
    try:
        if job_type == "analyze_resume":
            from app.services.nexus_resume_service import analyze_resume
            from app.db.database import SessionLocal
            resume_id = message_body.get("resume_id")
            job_description = message_body.get("job_description")
            db = SessionLocal()
            try:
                await analyze_resume(db, user_id, resume_id, job_description)
                success_msg = {"type": "job_completed", "job_id": job_id, "job_type": job_type, "status": "success", "message": "Resume analyzed successfully", "user_id": user_id}
                await publish_message("notifications", success_msg)
            finally:
                db.close()

        elif job_type == "upload_resume":
            from app.services.nexus_resume_service import upload_resume
            from app.db.database import SessionLocal
            file_path = message_body.get("file_path")
            filename = message_body.get("filename")
            db = SessionLocal()
            try:
                # Need a mock upload file or directly call internal logic
                # For now, let's assume we read from file_path
                class DummyUploadFile:
                    def __init__(self, path, name):
                        self.filename = name
                        self.file = open(path, "rb")
                    async def read(self):
                        self.file.seek(0)
                        return self.file.read()
                    
                dummy_file = DummyUploadFile(file_path, filename)
                await upload_resume(db, user_id, dummy_file)
                success_msg = {"type": "job_completed", "job_id": job_id, "job_type": job_type, "status": "success", "message": "Resume uploaded successfully", "user_id": user_id}
                await publish_message("notifications", success_msg)
            finally:
                db.close()

        elif job_type == "upload_document":
            from app.services.document_processor import get_document_processor
            from app.db.database import SessionLocal
            from app.db.models import Document
            from app.config import settings
            file_path = message_body.get("file_path")
            filename = message_body.get("filename")
            title = message_body.get("title")
            category = message_body.get("category")
            
            with open(file_path, "rb") as f:
                content = f.read()
                
            doc_processor = get_document_processor()
            metadata = {"user_id": user_id}
            if title: metadata["title"] = title
            if category: metadata["category"] = category
            
            document_id, num_chunks = await doc_processor.ingest_file(
                file_content=content,
                filename=filename,
                metadata=metadata
            )
            
            db = SessionLocal()
            try:
                import pathlib
                file_extension = pathlib.Path(filename).suffix.lower()
                if file_extension == ".pdf":
                    pdf_dir = os.path.join(settings.data_dir, "documents")
                    os.makedirs(pdf_dir, exist_ok=True)
                    pdf_path = os.path.join(pdf_dir, f"{document_id}.pdf")
                    with open(pdf_path, "wb") as f:
                        f.write(content)
                        
                db_document = Document(
                    id=document_id,
                    user_id=user_id,
                    filename=filename,
                    file_size=len(content),
                    file_type=file_extension,
                    vector_count=num_chunks,
                    title=title,
                    category=category,
                )
                db.add(db_document)
                db.commit()
                
                success_msg = {"type": "job_completed", "job_id": job_id, "job_type": job_type, "status": "success", "message": f"Document '{filename}' successfully processed into {num_chunks} chunks", "user_id": user_id}
                await publish_message("notifications", success_msg)
            finally:
                db.close()
                
        elif job_type == "generate_tree":
            from app.services.pageindex_service import get_pageindex_service
            from app.db.database import SessionLocal
            document_id = message_body.get("document_id")
            pdf_path = message_body.get("pdf_path")
            pageindex_service = get_pageindex_service()
            db = SessionLocal()
            try:
                pageindex_service.mark_tree_status(db, document_id, "processing")
                tree = await pageindex_service.generate_tree(pdf_path)
                pageindex_service.store_tree(db, document_id, tree)
                success_msg = {"type": "job_completed", "job_id": job_id, "job_type": job_type, "status": "success", "message": "Tree generated successfully", "user_id": user_id}
                await publish_message("notifications", success_msg)
            finally:
                db.close()

        elif job_type == "data_analysis":
            # Call the synchronous workflow in a thread pool
            from app.analysis.workflows.analysis_workflow import run_analysis_workflow
            from app.db.database import SessionLocal
            from app.api.routes.analysis import _manager
            db = SessionLocal()
            try:
                await asyncio.to_thread(run_analysis_workflow, db, job_id, user_id, _manager)
                success_msg = {"type": "job_completed", "job_id": job_id, "job_type": job_type, "status": "success", "message": "Data analysis completed", "user_id": user_id}
                await publish_message("notifications", success_msg)
            finally:
                db.close()
                
        elif job_type == "auto_tailor":
            from app.analysis.workflows.auto_tailor_workflow import AutoTailorWorkflow
            from app.db.database import SessionLocal
            resume_id = message_body.get("resume_id")
            job_description = message_body.get("job_description")
            target_score = message_body.get("target_score", 85.0)
            max_iterations = message_body.get("max_iterations", 3)
            
            db = SessionLocal()
            try:
                workflow = AutoTailorWorkflow(db=db, analysis_id=job_id, disable_validation=True, timeout=300.0)
                result = await workflow.run(
                    resume_id=resume_id,
                    job_description=job_description,
                    target_score=target_score,
                    max_iterations=max_iterations
                )
                
                # result contains the suspended state with status "needs_approval_attention"
                msg = {
                    "type": "needs approval attention",
                    "job_id": job_id,
                    "job_type": job_type,
                    "status": result.get("status", "paused_for_human"),
                    "message": "Auto-tailor draft ready for approval",
                    "user_id": user_id,
                    "analysis_id": job_id,
                    "current_iteration": result.get("current_iteration"),
                    "latest_score": result.get("latest_score"),
                    "resume_data": result.get("resume_data"),
                    "payload": result
                }
                await publish_message("notifications", msg)
            finally:
                db.close()

        elif job_type == "auto_tailor_reiterate":
            from app.analysis.workflows.auto_tailor_workflow import AutoTailorWorkflow, RewriteEvent
            from app.db.database import SessionLocal
            from app.db.models import NexusResumeAnalysis
            
            user_feedback = message_body.get("user_feedback")
            
            db = SessionLocal()
            try:
                analysis_record = db.query(NexusResumeAnalysis).filter(NexusResumeAnalysis.id == job_id).first()
                if not analysis_record:
                    raise Exception("Analysis record not found")
                    
                state = analysis_record.analysis
                previous_draft = state.get("resume_data")
                critic_feedback = state.get("critic_feedback")
                current_iteration = state.get("current_iteration", 1)
                target_score = state.get("target_score", 85.0)
                max_iterations = state.get("max_iterations", 3)
                
                workflow = AutoTailorWorkflow(db=db, analysis_id=job_id, disable_validation=True, timeout=300.0)
                rewrite_ev = RewriteEvent(
                    analysis_id=job_id,
                    resume_data=previous_draft,
                    critic_feedback=critic_feedback,
                    job_description=analysis_record.job_description,
                    iteration=current_iteration + 1,
                    target_score=target_score,
                    max_iterations=max_iterations,
                    human_feedback=user_feedback
                )
                
                run_task = workflow.run()
                await asyncio.sleep(0.01)
                workflow.send_event(rewrite_ev)
                result = await run_task
                
                msg = {
                    "type": "needs approval attention",
                    "job_id": job_id,
                    "job_type": "auto_tailor",
                    "status": result.get("status", "paused_for_human"),
                    "message": "Auto-tailor reiteration ready for approval",
                    "user_id": user_id,
                    "analysis_id": job_id,
                    "current_iteration": result.get("current_iteration"),
                    "latest_score": result.get("latest_score"),
                    "resume_data": result.get("resume_data"),
                    "payload": result
                }
                await publish_message("notifications", msg)
            finally:
                db.close()

        else:
            logger.warning(f"Unknown job type: {job_type}")
            
    except Exception as e:
        logger.error(f"Job failed: {e}")
        error_msg = {
            "type": "job_failed", 
            "job_id": job_id, 
            "job_type": job_type, 
            "status": "error", 
            "message": f"Failed to process {job_type}: {str(e)}", 
            "user_id": user_id
        }
        await publish_message("notifications", error_msg)

async def main():
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()
        # Ensure queue exists
        queue = await channel.declare_queue("jobs", durable=True)
        logger.info("Worker started, waiting for messages...")
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        data = json.loads(message.body.decode())
                        # process job in background or await here. Await here to process one by one
                        await process_job(data)
                    except Exception as e:
                        logger.error(f"Error decoding or processing message: {e}")

if __name__ == "__main__":
    asyncio.run(main())
