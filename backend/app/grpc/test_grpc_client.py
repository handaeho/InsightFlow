import grpc
import os
from protos import file_pb2, file_pb2_grpc

# 1. 보낼 파일 설정 (테스트용)
FILE_PATH = "test_large_file.bin"
CHUNK_SIZE = 1024 * 1024  # 1MB씩 쪼개기


def generate_requests(filepath):
    filename = os.path.basename(filepath)

    # 1. 첫 번째 메시지: 파일 정보 (Info)
    info = file_pb2.FileInfo(filename=filename, file_type="application/octet-stream")
    yield file_pb2.FileChunk(info=info)

    # 2. 두 번째부터: 파일 데이터 (Chunk Data)
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            yield file_pb2.FileChunk(chunk_data=chunk)


def run():
    # gRPC 채널 생성 (서버 주소: localhost:50051)
    # with grpc.insecure_channel('localhost:50051') as channel: # 동기 채널
    # 비동기 서버라도 클라이언트는 동기/비동기 선택 가능 (여기선 편의상 동기 사용)

    with grpc.insecure_channel("localhost:50051") as channel:
        stub = file_pb2_grpc.FileServiceStub(channel)

        print(f"Uploading file: {FILE_PATH}...")

        # 서버의 UploadFile 함수 호출 (여기에 제너레이터를 넣으면 스트리밍 시작)
        response = stub.UploadFile(generate_requests(FILE_PATH))

        print(f"Server Response: {response.message}")
        print(f"Success: {response.success}")


if __name__ == "__main__":
    # 바이너리 랜덤 파일 대신 텍스트 파일 생성
    FILE_PATH = "test_doc_kr.txt"

    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            f.write(
                "이것은 RAG 테스트를 위한 한글 문서입니다. gRPC를 통해 스트리밍으로 전송됩니다.\n"
                * 100
            )
        print(f"Created dummy text file: {FILE_PATH}")

    run()  # FILE_PATH 전역 변수 사용 또는 인자로 전달 필요
