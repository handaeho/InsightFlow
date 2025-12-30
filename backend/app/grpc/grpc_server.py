"""
InsightFlow gRPC Ingestion Server
---------------------------------
역할:
    대용량 문서 파일을 스트리밍으로 수신하여 시스템에 통합하는 진입점(Entrypoint)

주요 기능:
    1. gRPC Streaming: 대용량 파일도 청크 단위로 끊어서 메모리 효율적으로 수신
    2. MariaDB Metadata: 파일의 메타데이터(파일명, 경로, 크기)를 DB에 기록하고 ID 발급 (SSOT)
    3. RAG Indexing Trigger: 저장 완료 즉시 ChromaDB 인덱싱을 수행하여 검색 가능한 상태로 전환

데이터 흐름:
    Client -> [gRPC Stream] -> Local Disk Save -> MariaDB Insert -> ChromaDB Embedding -> Ready to Search
"""

import asyncio
import os
import grpc

# 컴파일된 proto 모듈
from protos import file_pb2, file_pb2_grpc
from concurrent import futures
from app.db.session import AsyncSessionLocal
from app.db.models.files import File
from app.vectordb.vector_db_upsert import upsert_document  # RAG 인덱싱 함수 재사용

# 파일 로컬 저장 위치
UPLOAD_DIR = "./test_upload_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class FileService(file_pb2_grpc.FileServiceServicer):
    async def UploadFile(self, request_iterator, context):
        """
        스트림에서 청크 추출
            - 클라이언트 스트리밍 방식이므로, 요청이 한 번에 오지 않고 반복자(request_iterator) 형태로 쪼개져서 수신
            - 청크가 메타데이터인 경우(첫번째 청크): 파일 정보(파일명, 파일 경로 등) 확인
            - 청크가 파일 데이터인 경우(두번째 청크 이후): 실제 파일 데이터
        """
        filename = ""
        filepath = ""
        file_handle = None
        file_size = 0

        try:
            # 스트림에서 청크를 하나씩 추출 (논블로킹 방식, 데이터 수신 시 반복 루프 수행)
            async for chunk in request_iterator:
                # 1. 메타데이터 청크의 경우(가장 첫번째 순서의 청크이므로)
                if chunk.HasField("info"):
                    filename = chunk.info.filename
                    filepath = os.path.join(UPLOAD_DIR, filename)
                    file_handle = open(filepath, "wb")
                    print(f"파일 업로드 시작: {filename}")

                # 2. 파일 데이터 청크의 경우
                elif chunk.HasField("chunk_data"):
                    if file_handle:
                        file_handle.write(chunk.chunk_data)
                        file_size += len(chunk.chunk_data)
                    else:
                        # 메타데이터 없이 데이터 청크부터 온 경우 에러
                        context.abort(
                            grpc.StatusCode.INVALID_ARGUMENT, "메타데이터가 없습니다."
                        )
            # 파일 전송 끝
            if file_handle:
                file_handle.close()

            print(f"파일 업로드 완료: {filename} (Size: {file_size} bytes)")

            # MariaDB에 파일 메타데이터 저장
            async with AsyncSessionLocal() as session:
                new_file = File(
                    filename=filename, saved_path=filepath, file_size=file_size
                )
                # new_file 객체 저장 준비(INSERT 쿼리 전)
                session.add(new_file)
                # DB에 변경사항 적용(INSERT 쿼리 실행 및 트렌잭션 수행)
                await session.commit()
                # DB에 저장된 최신정보로 new_file 객체 업데이트(DB가 발급한 ID(Primary Key) 인식)
                await session.refresh(new_file)

                # DB에서 발급받은 ID(Primary Key)
                file_db_id = new_file.id
                print(f"DB 저장 완료: ID={file_db_id}")

            # 3. ChromaDB 인덱싱 (RAG)
            # doc_id를 DB의 ID(Primary Key)와 매핑하여 관리 일원화
            rag_doc_id = f"file_id_{file_db_id}"

            # ChromaDB에 데이터 저장(upsert)
            # NOTE: 동기 함수인 upsert_document 메서드를 별도 스레드에서 실행
            # 동기 방식의 경우, CPU 집약적이므로 대용량 파일 업로드 시, upsert 적용하는 동안 서버가 모든 작업을 멈추고 기다려야 함
            # 따라서, 동기 함수 실행을 별도 스레드에서 수행하고, 메인 스레드는 다른 작업을 수행하게 함(asyncio.to_thread)
            # 추후, 규모가 커지면 Celery나 RabbitMQ 같은 메시지 큐 도입(파일 저장 시, 즉시 응답 및 백그라운드 수행)
            await asyncio.to_thread(upsert_document, filepath, rag_doc_id)

            # 클라이언트에게 성공 응답 송신
            return file_pb2.UploadStatus(
                success=True,
                message=f"파일이 성공적으로 업로드 되었습니다. ID: {file_db_id}",
                file_id=str(file_db_id),
            )
        except Exception as e:
            if file_handle:
                file_handle.close()
            print(f"파일 업로드 시, 에러 발생: {e}")
            return file_pb2.UploadStatus(success=False, message=str(e))


async def serve():
    # 비동기 gRPC 서버 생성
    server = grpc.aio.server()

    # FileService 서비스를 서버에 등록
    file_pb2_grpc.add_FileServiceServicer_to_server(FileService(), server)

    # 50051 포트 열기
    server.add_insecure_port("[::]:50051")
    print("gRPC Server 실행 중... 포트 50051...")

    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
